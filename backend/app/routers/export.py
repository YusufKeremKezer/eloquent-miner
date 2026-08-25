from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlmodel import Session

from app.core.database import get_session
from app.models.job import Job
from app.services.anki import build_anki_deck

router = APIRouter()


@router.get("/jobs/{job_id}/export/anki")
def export_anki_deck(
    job_id: str,
    status: str | None = Query(
        default=None,
        description="Filter phrases by status: candidate, approved, rejected. Leave empty for all."
    ),
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        apkg_path = build_anki_deck(
            session=session,
            job=job,
            status_filter=status
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Anki export failed: {e!s}")

    # Return the file as a download
    filename = Path(apkg_path).name
    return FileResponse(
        path=apkg_path,
        media_type="application/apkg",
        filename=filename
    )


@router.get("/jobs/{job_id}/export/json")
def export_phrases_json(
    job_id: str,
    status: str | None = Query(default=None),
    session: Session = Depends(get_session)
):
    """Export phrases as raw JSON (useful for backup or other tools)."""
    from sqlmodel import select

    from app.models.phrase import Phrase

    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    statement = select(Phrase).where(Phrase.job_id == job.id)
    if status:
        statement = statement.where(Phrase.status == status)

    phrases = session.exec(statement).all()

    return {
        "job_id": job.id,
        "job_title": job.title,
        "source_url": job.source_url,
        "language": job.language,
        "phrase_count": len(phrases),
        "phrases": [
            {
                "id": p.id,
                "phrase": p.phrase,
                "start": p.start,
                "end": p.end,
                "definition": p.definition,
                "usage": p.usage,
                "example_original": p.example_original,
                "example_new": p.example_new,
                "register": p.register,
                "alternatives": p.alternatives,
                "why_eloquent": p.why_eloquent,
                "status": p.status,
                "audio_filename": p.audio_filename,
            }
            for p in phrases
        ]
    }