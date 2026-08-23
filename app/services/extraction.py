import json
import re
from collections.abc import Generator

from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import settings
from app.models.job import Job
from app.models.phrase import Phrase
from app.models.segment import Segment
from app.prompts.extraction import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.services.llm import call_llm


def clean_json_response(content: str) -> str:
    content = content.strip()
    content = content.removeprefix("```json")
    content = content.removeprefix("```")
    content = content.removesuffix("```")
    return content.strip()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_segments_for_prompt(segments: list[Segment]) -> str:
    lines = []
    for seg in segments:
        lines.append(seg.text)
    return "\n".join(lines)


def merge_segments_for_context(segments: list[Segment], min_words: int = 40) -> list[Segment]:
    """
    Merges short segments into longer ones for better context.
    This helps LLM understand the full thought and extract better phrases.
    """
    if not segments:
        return []

    merged = []
    current_text = ""
    current_start = None
    current_end = None
    job_id = segments[0].job_id

    for seg in segments:
        if current_start is None:
            current_start = seg.start
            current_text = seg.text
            current_end = seg.end
        else:
            current_text += " " + seg.text
            current_end = seg.end

        total_words = len(current_text.split())

        if total_words >= min_words:
            merged.append(Segment(
                id=None,
                job_id=job_id,
                start=current_start,
                end=current_end,
                text=current_text
            ))
            current_text = ""
            current_start = None
            current_end = None

    if current_text:
        merged.append(Segment(
            id=None,
            job_id=job_id,
            start=current_start,
            end=current_end,
            text=current_text
        ))

    return merged


def chunk_segments(segments: list[Segment], chunk_size: int = 30) -> Generator[list[Segment], None, None]:
    merged = merge_segments_for_context(segments, min_words=40)

    for i in range(0, len(merged), chunk_size):
        yield merged[i:i + chunk_size]


def build_timeline(segments: list[Segment]) -> tuple[str, list[float | None], list[float | None]]:
    full_text = ""
    start_times: list[float | None] = []
    end_times: list[float | None] = []

    for seg in segments:
        seg_text = seg.text + " "
        seg_len = len(seg_text)
        full_text += seg_text

        if seg.start is not None and seg.end is not None and seg_len > 0:
            duration = seg.end - seg.start
            for i in range(seg_len):
                char_start = seg.start + (i / seg_len) * duration
                char_end = seg.start + ((i + 1) / seg_len) * duration
                start_times.append(round(char_start, 3))
                end_times.append(round(char_end, 3))
        else:
            for _ in range(seg_len):
                start_times.append(None)
                end_times.append(None)

    return full_text, start_times, end_times


def find_phrase_timestamps(
    phrase_text: str,
    full_text: str,
    start_times: list[float | None],
    end_times: list[float | None]
) -> tuple[float | None, float | None]:
    if not phrase_text or len(phrase_text.strip()) < 2:
        return None, None

    phrase_lower = phrase_text.lower().strip()
    full_lower = full_text.lower()
    idx = full_lower.find(phrase_lower)

    if idx == -1:
        norm_phrase = normalize_text(phrase_text)
        norm_full = normalize_text(full_text)

        phrase_words = norm_phrase.split()
        if len(phrase_words) < 1:
            return None, None

        first_word = phrase_words[0]
        pattern = r"\b" + re.escape(first_word) + r"\b"
        match = re.search(pattern, full_lower)
        if match:
            idx = match.start()
        else:
            return None, None

    if idx == -1:
        return None, None

    end_idx = idx + len(phrase_text.strip()) - 1

    if idx >= len(start_times) or end_idx >= len(end_times):
        return None, None

    phrase_start = start_times[idx]
    phrase_end = end_times[min(end_idx, len(end_times) - 1)]

    if phrase_start is None or phrase_end is None:
        return None, None

    padding_before = settings.clip_padding_before
    padding_after = settings.clip_padding_after
    offset = settings.subtitle_offset

    final_start = max(0.0, phrase_start - padding_before + offset)
    final_end = phrase_end + padding_after + offset

    # Ensure minimum clip duration of 3 seconds
    if final_end - final_start < 3.0:
        center = (final_start + final_end) / 2
        final_start = max(0.0, center - 1.5)
        final_end = center + 1.5

    if final_end <= final_start:
        final_end = final_start + 3.0

    return round(final_start, 3), round(final_end, 3)


def verify_example_original(example: str, full_text: str) -> bool:
    if not example or not example.strip():
        return True

    norm_example = normalize_text(example)
    norm_full = normalize_text(full_text)

    example_words = norm_example.split()
    if not example_words:
        return True

    found_count = 0
    for word in example_words:
        if word in norm_full:
            found_count += 1

    return (found_count / len(example_words)) >= 0.7


def extract_and_save_phrases(session: Session, job: Job) -> list[Phrase]:
    job.status = "extracting"
    session.add(job)
    session.commit()

    statement = select(Segment).where(Segment.job_id == job.id).order_by(Segment.id)
    segments = session.exec(statement).all()

    if not segments:
        job.status = "failed"
        session.add(job)
        session.commit()
        raise HTTPException(status_code=400, detail="No transcript segments found for this job.")

    print("\n🔧 Building transcript timeline...")
    full_text, start_times, end_times = build_timeline(segments)
    print(f"✅ Timeline built: {len(full_text)} characters mapped.\n")

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
            print(f"❌ LLM call failed on chunk {processed_chunks}: {e!s}")
            continue

        try:
            cleaned_response = clean_json_response(raw_response)
            data = json.loads(cleaned_response)
            extracted_phrases = data.get("phrases", [])
            print(f"✅ LLM suggested {len(extracted_phrases)} phrases.")
        except json.JSONDecodeError:
            print(f"⚠️ Invalid JSON for chunk {processed_chunks}. Skipping.")
            continue

        verified_in_chunk = 0
        for item in extracted_phrases:
            phrase_text = item.get("phrase", "").strip()
            if not phrase_text:
                continue

            start_time, end_time = find_phrase_timestamps(
                phrase_text, full_text, start_times, end_times
            )

            if start_time is None or end_time is None:
                print(f"   ❌ Discarded (not found in transcript): '{phrase_text}'")
                discarded_count += 1
                continue

            example_original = item.get("example_original", "")
            if example_original and not verify_example_original(example_original, full_text):
                print(f"   ⚠️ Discarded (fake example): '{phrase_text}'")
                discarded_count += 1
                continue

            phrase = Phrase(
                job_id=job.id,
                phrase=phrase_text,
                start=start_time,
                end=end_time,
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

        print(f"   ✓ Saved: {verified_in_chunk} phrases")
        session.commit()

    job.status = "completed"
    session.add(job)
    session.commit()

    for p in all_saved_phrases:
        session.refresh(p)

    print(f"\n{'='*60}")
    print("🎉 EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Verified phrases: {len(all_saved_phrases)}")
    print(f"❌ Discarded: {discarded_count}")
    print(f"{'='*60}\n")

    return all_saved_phrases