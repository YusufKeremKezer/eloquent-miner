
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.job import Job
from app.models.phrase import Phrase
from app.schemas.phrase import PhraseCreate, PhraseRead

router = APIRouter()


class PhraseUpdate(BaseModel):
    phrase: str | None = None
    definition: str | None = None
    usage: str | None = None
    example_original: str | None = None
    example_new: str | None = None
    register: str | None = None
    alternatives: list[str] | None = None
    why_eloquent: str | None = None
    start: float | None = None
    end: float | None = None
    status: str | None = None


@router.post("/jobs/{job_id}/phrases", response_model=PhraseRead, status_code=201)
def create_phrase(
    job_id: str,
    payload: PhraseCreate,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    phrase = Phrase.model_validate(payload)
    phrase.job_id = job_id

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase


@router.get("/jobs/{job_id}/phrases", response_model=list[PhraseRead])
def list_phrases_for_job(
    job_id: str,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    statement = (
        select(Phrase)
        .where(Phrase.job_id == job_id)
        .order_by(Phrase.created_at.desc())
    )

    phrases = session.exec(statement).all()
    return phrases


@router.get("/phrases/{phrase_id}", response_model=PhraseRead)
def get_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    return phrase


@router.patch("/phrases/{phrase_id}", response_model=PhraseRead)
def update_phrase(
    phrase_id: int,
    payload: PhraseUpdate,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(phrase, key, value)

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase


@router.post("/phrases/{phrase_id}/approve", response_model=PhraseRead)
def approve_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    phrase.status = "approved"

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase


@router.post("/phrases/{phrase_id}/reject", response_model=PhraseRead)
def reject_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    phrase.status = "rejected"

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase


@router.delete("/phrases/{phrase_id}", status_code=204)
def delete_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    session.delete(phrase)
    session.commit()


class ReclipRequest(BaseModel):
    start: float
    end: float


@router.post("/phrases/{phrase_id}/reclip", response_model=PhraseRead)
def reclip_phrase(
    phrase_id: int,
    payload: ReclipRequest,
    session: Session = Depends(get_session)
):
    """Re-cut the audio clip with new start/end times."""
    import subprocess
    from pathlib import Path

    from app.core.config import settings
    from app.services.clipping import find_source_audio

    phrase = session.get(Phrase, phrase_id)
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    # Validate times
    if payload.end <= payload.start:
        raise HTTPException(status_code=400, detail="End must be after start")

    if payload.end - payload.start > 60:
        raise HTTPException(status_code=400, detail="Clip cannot be longer than 60 seconds")

    # Find source audio
    source_audio = find_source_audio(phrase.job_id)
    if not source_audio:
        raise HTTPException(status_code=400, detail="Source audio not found")

    # Update phrase timestamps
    phrase.start = payload.start
    phrase.end = payload.end

    # Re-cut the clip
    job_media_dir = Path(settings.media_dir) / phrase.job_id
    job_media_dir.mkdir(parents=True, exist_ok=True)

    safe_filename = f"phrase_{phrase.id}.mp3"
    output_path = job_media_dir / safe_filename

    duration = payload.end - payload.start
    fade_dur = settings.clip_fade_duration

    cmd = [
        settings.ffmpeg_path,
        "-y",
        "-ss", str(payload.start),
        "-i", str(source_audio),
        "-t", str(duration),
        "-acodec", "libmp3lame",
        "-q:a", "2",
        "-af", f"afade=t=in:st=0:d={fade_dur},afade=t=out:st={max(0, duration - fade_dur)}:d={fade_dur}",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"ffmpeg failed: {result.stderr}")

    phrase.audio_filename = f"{phrase.job_id}/{safe_filename}"

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase   