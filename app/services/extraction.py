import json
from typing import List, Generator, Optional, Tuple

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.job import Job
from app.models.segment import Segment
from app.models.phrase import Phrase
from app.services.llm import call_llm
from app.prompts.extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE


def clean_json_response(content: str) -> str:
    """Strips markdown code blocks if the LLM includes them."""
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()


def format_segments_for_prompt(segments: List[Segment]) -> str:
    """Converts segments into a readable text format for the LLM."""
    lines = []
    for seg in segments:
        # We NO longer send timestamps to LLM to prevent hallucination
        lines.append(seg.text)
    return "\n".join(lines)


def chunk_segments(segments: List[Segment], chunk_size: int = 30) -> Generator[List[Segment], None, None]:
    """Yields chunks of segments to avoid LLM token limits."""
    for i in range(0, len(segments), chunk_size):
        yield segments[i:i + chunk_size]


def build_timeline(segments: List[Segment]) -> Tuple[str, List[Optional[float]]]:
    """
    Concatenates all segments into one text and builds a character-to-time mapping.
    Returns (full_text, char_map) where char_map[i] = timestamp_at_char_i.
    """
    full_text = ""
    char_map: List[Optional[float]] = []
    
    for seg in segments:
        start_char = len(full_text)
        seg_text = seg.text + " "
        full_text += seg_text
        end_char = len(full_text)
        
        seg_length = end_char - start_char
        
        # If segment has timestamps, interpolate for each character
        if seg.start is not None and seg.end is not None and seg_length > 0:
            seg_duration = seg.end - seg.start
            for i in range(seg_length):
                t = seg.start + (i / seg_length) * seg_duration
                char_map.append(round(t, 3))
        else:
            # No timestamps for this segment
            for _ in range(seg_length):
                char_map.append(None)
    
    return full_text, char_map


def find_phrase_timestamps(
    phrase_text: str,
    full_text: str,
    char_map: List[Optional[float]]
) -> Tuple[Optional[float], Optional[float]]:
    """
    Finds start and end timestamps of a phrase by searching the full concatenated transcript.
    Returns (start_time, end_time) or (None, None) if not found.
    """
    phrase_lower = phrase_text.lower().strip()
    full_lower = full_text.lower()
    
    if not phrase_lower or len(phrase_lower) < 3:
        return None, None
    
    # Find the phrase in the full text
    idx = full_lower.find(phrase_lower)
    if idx == -1:
        return None, None
    
    end_idx = idx + len(phrase_lower) - 1
    
    # Get timestamps from character map
    start_time = char_map[idx] if idx < len(char_map) else None
    end_time = char_map[min(end_idx, len(char_map) - 1)] if end_idx < len(char_map) else None
    
    # Add small padding for natural audio (100ms before and after)
    if start_time is not None:
        start_time = max(0.0, round(start_time - 0.1, 3))
    if end_time is not None:
        end_time = round(end_time + 0.1, 3)
    
    return start_time, end_time


def verify_example_original(example: str, full_text: str) -> bool:
    """Verifies that example_original exists verbatim in the transcript."""
    if not example or not example.strip():
        return True  # Empty is OK
    
    example_lower = example.lower().strip()
    full_lower = full_text.lower()
    
    # Allow slight variations (punctuation differences)
    import re
    example_clean = re.sub(r"[^\w\s]", "", example_lower)
    full_clean = re.sub(r"[^\w\s]", "", full_lower)
    
    return example_clean in full_clean


def extract_and_save_phrases(session: Session, job: Job) -> List[Phrase]:
    # 1. Update job status
    job.status = "extracting"
    session.add(job)
    session.commit()

    # 2. Fetch segments
    statement = select(Segment).where(Segment.job_id == job.id).order_by(Segment.id)
    segments = session.exec(statement).all()

    if not segments:
        job.status = "failed"
        session.add(job)
        session.commit()
        raise HTTPException(status_code=400, detail="No transcript segments found for this job.")

    # 3. Build timeline for timestamp matching (this is the key fix!)
    print("\n🔧 Building transcript timeline...")
    full_text, char_map = build_timeline(segments)
    print(f"✅ Timeline built: {len(full_text)} characters mapped to timestamps.\n")

    # 4. Process in chunks
    chunk_size = 30
    all_saved_phrases = []
    discarded_count = 0
    
    total_chunks = (len(segments) + chunk_size - 1) // chunk_size
    processed_chunks = 0

    print(f"--- Starting Extraction for Job {job.id} ---")
    print(f"Total segments: {len(segments)} | Total chunks: {total_chunks}\n")

    for chunk in chunk_segments(segments, chunk_size):
        processed_chunks += 1
        print(f"Processing chunk {processed_chunks}/{total_chunks}...")
        
        transcript_text = format_segments_for_prompt(chunk)
        user_prompt = USER_PROMPT_TEMPLATE.format(transcript_text=transcript_text)

        try:
            raw_response = call_llm(SYSTEM_PROMPT, user_prompt)
        except Exception as e:
            print(f"❌ LLM call failed on chunk {processed_chunks}: {str(e)}")
            continue

        try:
            cleaned_response = clean_json_response(raw_response)
            data = json.loads(cleaned_response)
            extracted_phrases = data.get("phrases", [])
            print(f"✅ LLM suggested {len(extracted_phrases)} phrases in chunk {processed_chunks}.")
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON returned for chunk {processed_chunks}. Skipping.")
            continue

        # 5. VERIFY each phrase against the real transcript
        verified_in_chunk = 0
        for item in extracted_phrases:
            phrase_text = item.get("phrase", "").strip()
            if not phrase_text:
                continue
            
            # VERIFICATION 1: Does this phrase actually exist in the transcript?
            start_time, end_time = find_phrase_timestamps(phrase_text, full_text, char_map)
            
            if start_time is None or end_time is None:
                print(f"   ❌ Discarded hallucinated phrase: '{phrase_text}' (not found in transcript)")
                discarded_count += 1
                continue
            
            # VERIFICATION 2: Does example_original exist verbatim?
            example_original = item.get("example_original", "")
            if example_original and not verify_example_original(example_original, full_text):
                print(f"   ⚠️ Discarded phrase with fabricated example: '{phrase_text}'")
                discarded_count += 1
                continue
            
            # Passed all checks! Save it.
            phrase = Phrase(
                job_id=job.id,
                phrase=phrase_text,
                start=start_time,          # REAL timestamp from segment
                end=end_time,              # REAL timestamp from segment
                definition=item.get("definition"),
                usage=item.get("usage"),
                example_original=example_original,
                example_new=item.get("example_new"),
                register=item.get("register"),
                alternatives=item.get("alternatives", []),
                why_eloquent=item.get("why_eloquent"),
                status="candidate"
            )
            session.add(phrase)
            all_saved_phrases.append(phrase)
            verified_in_chunk += 1
        
        print(f"   ✓ Verified and saved: {verified_in_chunk} phrases")
        session.commit()

    # 6. Finalize job
    job.status = "completed"
    session.add(job)
    session.commit()

    for p in all_saved_phrases:
        session.refresh(p)

    print(f"\n{'='*60}")
    print(f"🎉 EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Verified real phrases saved: {len(all_saved_phrases)}")
    print(f"❌ Hallucinations discarded: {discarded_count}")
    print(f"{'='*60}\n")
    
    return all_saved_phrases