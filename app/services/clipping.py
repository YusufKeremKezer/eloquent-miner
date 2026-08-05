import subprocess
from pathlib import Path
from typing import List, Optional
from sqlmodel import Session, select

from app.core.config import settings
from app.models.job import Job
from app.models.phrase import Phrase

def find_source_audio(job_id: str) -> Optional[Path]:
    """Looks for the uploaded source audio file in the job's media folder."""
    job_media_dir = Path(settings.media_dir) / job_id
    if not job_media_dir.exists():
        return None
    
    # Check common audio extensions
    for ext in [".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".webm"]:
        file_path = job_media_dir / f"source{ext}"
        if file_path.exists():
            return file_path
    return None

def clip_phrase_audio(source_path: Path, output_path: Path, start: float, end: float):
    """Runs ffmpeg to cut a specific segment of the audio."""
    duration = end - start
    cmd = [
        settings.ffmpeg_path,
        "-y",                 # Overwrite output files without asking
        "-i", str(source_path),
        "-ss", str(start),    # Start time
        "-t", str(duration),  # Duration
        "-acodec", "libmp3lame",
        "-q:a", "2",          # High quality MP3
        str(output_path)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr}")

def generate_clips_for_job(session: Session, job: Job) -> List[Phrase]:
    source_audio = find_source_audio(job.id)
    if not source_audio:
        raise ValueError(f"No source audio found for job {job.id}. Please upload audio first.")
        
    job_media_dir = Path(settings.media_dir) / job.id
    
    # Fetch all phrases for this job
    statement = select(Phrase).where(Phrase.job_id == job.id)
    phrases = session.exec(statement).all()
    
    clipped_phrases = []
    
    for phrase in phrases:
        # Only clip if we have exact timestamps
        if phrase.start is not None and phrase.end is not None:
            safe_filename = f"phrase_{phrase.id}.mp3"
            output_path = job_media_dir / safe_filename
            
            try:
                clip_phrase_audio(
                    source_path=source_audio,
                    output_path=output_path,
                    start=phrase.start,
                    end=phrase.end
                )
                
                # Store the relative path so FastAPI can serve it
                phrase.audio_filename = f"{job.id}/{safe_filename}"
                session.add(phrase)
                clipped_phrases.append(phrase)
            except Exception as e:
                print(f"Failed to clip phrase {phrase.id}: {e}")
                
    session.commit()
    for p in clipped_phrases:
        session.refresh(p)
        
    return clipped_phrases