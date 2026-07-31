from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, JSON


class Phrase(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    job_id: str = Field(index=True)

    phrase: str

    start: Optional[float] = None
    end: Optional[float] = None

    definition: Optional[str] = None
    usage: Optional[str] = None

    example_original: Optional[str] = None
    example_new: Optional[str] = None

    register: Optional[str] = None

    alternatives: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )

    why_eloquent: Optional[str] = None

    status: str = "candidate"

    audio_filename: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)