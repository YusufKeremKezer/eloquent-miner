from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.core.database import get_session
from app.models.job import Job
from app.models.segment import Segment
from app.services.subtitles import parse_subtitle_content
from app.services.youtube import (
    extract_video_id,
    process_youtube_url,
    validate_youtube_url,
)

router = APIRouter()


class YouTubeURLRequest(BaseModel):
    url: str
    title: str | None = None
    language: str = "en"


@router.post("/youtube/process", status_code=201)
async def process_youtube(
    payload: YouTubeURLRequest,
    session: Session = Depends(get_session)
):
    print(f"\n{'='*60}")
    print("🎬 YouTube Processing Started")
    print(f"{'='*60}")
    print(f"URL: {payload.url}")

    if not settings.enable_youtube_url:
        raise HTTPException(
            status_code=403,
            detail="YouTube URL processing is disabled in configuration."
        )

    if not validate_youtube_url(payload.url):
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube URL. Please provide a valid YouTube video link."
        )

    video_id = extract_video_id(payload.url)
    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Could not extract video ID from URL."
        )

    print(f"Video ID: {video_id}")

    # Create job
    job = Job(
        source_type="youtube",
        source_url=payload.url,
        title=payload.title or f"YouTube Video {video_id}",
        language=payload.language
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    print(f"Job created: {job.id}")

    try:
        # Step 1: Download audio and subtitles
        print("\n📥 Downloading audio and subtitles...")
        audio_path, subtitle_path, video_info = process_youtube_url(
            url=payload.url,
            job_id=job.id
        )

        # Update job title with actual video title
        if not payload.title and "title" in video_info:
            job.title = video_info["title"]
            session.add(job)
            print(f"Video title: {video_info['title']}")

        job.status = "audio_ready"
        session.commit()
        print(f"✅ Audio downloaded: {audio_path}")
        print(f"Subtitle found: {subtitle_path}")

        # Step 2: Parse subtitles if available
        segments_created = 0
        if subtitle_path:
            try:
                print("\n📝 Parsing subtitles...")
                with open(subtitle_path, "r", encoding="utf-8") as f:
                    content = f.read()

                parsed_segments = parse_subtitle_content(
                    content=content,
                    filename=Path(subtitle_path).name
                )

                print(f"Parsed {len(parsed_segments)} segments")

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
                print(f"✅ Segments saved: {segments_created}")

            except Exception as e:
                print(f"❌ Failed to parse subtitles: {e!s}")
                import traceback
                traceback.print_exc()
                job.status = "audio_ready"
                session.commit()
        else:
            print("⚠️ No subtitles found for this video")
            job.status = "audio_ready"
            session.commit()

        print(f"\n{'='*60}")
        print("🎉 YouTube Processing Complete!")
        print(f"{'='*60}")
        print(f"Job ID: {job.id}")
        print(f"Status: {job.status}")
        print(f"Segments: {segments_created}")
        print(f"{'='*60}\n")

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
        print(f"\n❌ YouTube processing failed: {e!s}")
        import traceback
        traceback.print_exc()

        job.status = "failed"
        session.add(job)
        session.commit()

        raise HTTPException(
            status_code=500,
            detail=f"YouTube processing failed: {e!s}"
        )


@router.get("/youtube/info")
async def get_youtube_info(url: str):
    """Fetch metadata about a YouTube video without downloading."""
    from app.services.youtube import get_video_info

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
            detail=f"Failed to fetch video info: {e!s}"
        )