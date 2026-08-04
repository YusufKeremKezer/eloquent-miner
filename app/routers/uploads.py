import shutil
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.models.job import Job

router = APIRouter()

@router.post("/jobs/{job_id}/audio")
async def upload_job_audio(
    job_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Create a specific folder for this job's media
    job_media_dir = Path(settings.media_dir) / job_id
    job_media_dir.mkdir(parents=True, exist_ok=True)

    # Determine file extension
    ext = Path(file.filename).suffix if file.filename else ".mp3"
    if not ext:
        ext = ".mp3"
        
    file_path = job_media_dir / f"source{ext}"
    
    # Save the file to disk
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "message": "Audio uploaded successfully",
        "file_path": str(file_path),
        "job_id": job_id
    }