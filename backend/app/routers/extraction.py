
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.models.job import Job
from app.schemas.phrase import PhraseRead
from app.services.extraction import extract_and_save_phrases

router = APIRouter()

@router.post(
    "/jobs/{job_id}/extract",
    response_model=list[PhraseRead],
    status_code=200
)
def extract_phrases_endpoint(
    job_id: str,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status not in ["pending", "transcript_ready", "failed"]:
         raise HTTPException(
             status_code=400, 
             detail=f"Job is in '{job.status}' state. Cannot extract."
         )

    phrases = extract_and_save_phrases(session, job)
    
    return phrases