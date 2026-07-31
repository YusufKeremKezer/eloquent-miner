from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.job import Job
from app.models.segment import Segment
from app.schemas.segment import SegmentRead, TranscriptInput
from app.services.ingestion import ingest_transcript


router = APIRouter()


@router.post(
    "/jobs/{job_id}/transcript",
    response_model=List[SegmentRead],
    status_code=201
)
def add_transcript(
    job_id: str,
    payload: TranscriptInput,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    segments = ingest_transcript(
        session=session,
        job=job,
        payload=payload
    )

    return segments


@router.get(
    "/jobs/{job_id}/segments",
    response_model=List[SegmentRead]
)
def list_segments_for_job(
    job_id: str,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    statement = (
        select(Segment)
        .where(Segment.job_id == job_id)
        .order_by(Segment.id)
    )

    segments = session.exec(statement).all()

    return segments