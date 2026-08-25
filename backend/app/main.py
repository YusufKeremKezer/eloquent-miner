from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import app.models
from app.core.config import settings
from app.core.database import create_db_and_tables
from app.routers import (
    clips,
    export,
    extraction,
    jobs,
    phrases,
    segments,
    subtitles,
    uploads,
    youtube,
)


def create_data_directories():
    Path(settings.media_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.jobs_dir).mkdir(parents=True, exist_ok=True)

    if settings.database_url.startswith("sqlite:///"):
        db_path = settings.database_url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


app = FastAPI(
    title=settings.app_name,
    version="0.7.0",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

create_data_directories()
create_db_and_tables()

app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(phrases.router, tags=["phrases"])
app.include_router(segments.router, tags=["segments"])
app.include_router(subtitles.router, tags=["subtitles"])
app.include_router(youtube.router, tags=["youtube"])
app.include_router(extraction.router, tags=["extraction"])
app.include_router(uploads.router, tags=["uploads"])
app.include_router(clips.router, tags=["clips"])
app.include_router(export.router, tags=["export"])

@app.get("/")
def health_check():
    return {
        "app": settings.app_name,
        "status": "ok"
    }

app.mount("/media", StaticFiles(directory=settings.media_dir), name="media")