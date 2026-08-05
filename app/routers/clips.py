from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.models.job import Job
from app.models.phrase import Phrase
from app.schemas.phrase import PhraseRead
from app.services.clipping import generate_clips_for_job

router = APIRouter()

@router.post("/jobs/{job_id}/clips", response_model=List[PhraseRead])
def create_audio_clips(
    job_id: str,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    try:
        clipped_phrases = generate_clips_for_job(session, job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clipping failed: {str(e)}")
        
    return clipped_phrases