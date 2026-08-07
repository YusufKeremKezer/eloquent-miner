from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.job import Job
from app.models.segment import Segment
from app.schemas.segment import SegmentRead
from app.services.subtitles import parse_subtitle_content

router = APIRouter()


@router.post(
    "/jobs/{job_id}/subtitles",
    response_model=List[SegmentRead],
    status_code=201
)
async def upload_subtitles(
    job_id: str,
    file: UploadFile = File(...),
    replace: bool = Form(default=True),
    language: str = Form(default=None),
    session: Session = Depends(get_session)
):
    """
    Upload a subtitle file (.srt or .vtt) and parse it into transcript segments.
    
    - `replace`: If true, deletes existing segments for this job before adding new ones.
    - `language`: Optional language code to update the job's language.
    """
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Validate file extension
    filename = file.filename or ""
    if not (filename.lower().endswith(".srt") or filename.lower().endswith(".vtt")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload .srt or .vtt files."
        )
    
    # Read file content
    try:
        content_bytes = await file.read()
        content = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content_bytes.seek(0)
            content = content_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Could not decode subtitle file. Please ensure it is UTF-8 encoded."
            )
    
    # Parse the subtitle content
    try:
        parsed_segments = parse_subtitle_content(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    if not parsed_segments:
        raise HTTPException(
            status_code=400,
            detail="No valid segments found in the subtitle file."
        )
    
    # Replace existing segments if requested
    if replace:
        existing_statement = select(Segment).where(Segment.job_id == job.id)
        existing_segments = session.exec(existing_statement).all()
        for seg in existing_segments:
            session.delete(seg)
    
    # Update job language if provided
    if language:
        job.language = language
    
    # Create new segment records
    new_segments = []
    for seg_data in parsed_segments:
        segment = Segment(
            job_id=job.id,
            start=seg_data["start"],
            end=seg_data["end"],
            text=seg_data["text"]
        )
        session.add(segment)
        new_segments.append(segment)
    
    # Update job status
    job.status = "transcript_ready"
    session.add(job)
    
    session.commit()
    
    for segment in new_segments:
        session.refresh(segment)
    
    return new_segments