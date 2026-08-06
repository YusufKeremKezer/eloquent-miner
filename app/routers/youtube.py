from typing import Optional
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlmodel import Session, select
from pydantic import BaseModel

from app.core.database import get_session
from app.core.config import settings
from app.models.job import Job
from app.models.segment import Segment
from app.schemas.segment import SegmentRead
from app.services.youtube import (
    validate_youtube_url,
    extract_video_id,
    get_video_info,
    process_youtube_url,
)
from app.services.subtitles import parse_subtitle_content

router = APIRouter()


class YouTubeURLRequest(BaseModel):
    url: str
    title: Optional[str] = None
    language: str = "en"


@router.post("/youtube/process", status_code=201)
async def process_youtube(
    payload: YouTubeURLRequest,
    session: Session = Depends(get_session)
):
    """
    Submit a YouTube URL to automatically download audio and subtitles,
    parse subtitles into segments, and prepare for phrase extraction.
    """
    # Validate feature flag
    if not settings.enable_youtube_url:
        raise HTTPException(
            status_code=403,
            detail="YouTube URL processing is disabled in configuration."
        )
    
    # Validate URL
    if not validate_youtube_url(payload.url):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Please provide a valid YouTube video link."
        )
    
    # Extract video ID
    video_id = extract_video_id(payload.url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract video ID from URL."
        )
    
    # Create the job
    job = Job(
        source_type="youtube",
        source_url=payload.url,
        title=payload.title or f"YouTube Video {video_id}",
        language=payload.language
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    
    try:
        # Process YouTube URL (download audio + subtitles)
        audio_path, subtitle_path, video_info = process_youtube_url(
            url=payload.url,
            job_id=job.id
        )
        
        # Update job title with actual video title if not provided
        if not payload.title and "title" in video_info:
            job.title = video_info["title"]
            session.add(job)
        
        job.status = "audio_ready"
        session.commit()
        
        # Parse subtitles if available
        segments_created = 0
        if subtitle_path:
            try:
                with open(subtitle_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                parsed_segments = parse_subtitle_content(
                    content=content,
                    filename=Path(subtitle_path).name
                )
                
                for seg_data in parsed_segments:
                    segment = Segment(
                        job_id=job.id,
                        start=seg_data["start"],
                        end=seg_data["end"],
                        text=seg_data["text"]
                    )
                    session.add(segment)
                    segments_created += 1
                
                job.status = "transcript_ready"
                session.commit()
                
            except Exception as e:
                print(f"Failed to parse subtitles: {e}")
                job.status = "audio_ready"
                session.commit()
        
        return {
            "message": "YouTube video processed successfully",
            "job_id": job.id,
            "video_id": video_id,
            "title": job.title,
            "audio_downloaded": True,
            "subtitles_found": subtitle_path is not None,
            "segments_created": segments_created,
            "status": job.status,
            "next_steps": {
                "extract_phrases": f"POST /jobs/{job.id}/extract",
                "generate_clips": f"POST /jobs/{job.id}/clips",
                "export_anki": f"GET /jobs/{job.id}/export/anki"
            }
        }
        
    except Exception as e:
        job.status = "failed"
        session.add(job)
        session.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"YouTube processing failed: {str(e)}"
        )


@router.get("/youtube/info")
async def get_youtube_info(url: str):
    """Fetch metadata about a YouTube video without downloading."""
    if not validate_youtube_url(url):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL."
        )
    
    try:
        info = get_video_info(url)
        return {
            "video_id": info.get("id"),
            "title": info.get("title"),
            "channel": info.get("channel"),
            "uploader": info.get("uploader"),
            "duration": info.get("duration"),
            "duration_string": info.get("duration_string"),
            "view_count": info.get("view_count"),
            "has_subtitles": bool(info.get("subtitles")),
            "has_auto_subtitles": bool(info.get("automatic_captions")),
            "url": url
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch video info: {str(e)}"
        )