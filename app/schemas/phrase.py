from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class PhraseBase(SQLModel):
    phrase: str

    start: Optional[float] = None
    end: Optional[float] = None

    definition: Optional[str] = None
    usage: Optional[str] = None

    example_original: Optional[str] = None
    example_new: Optional[str] = None

    register: Optional[str] = None

    alternatives: List[str] = Field(default_factory=list)

    why_eloquent: Optional[str] = None


class PhraseCreate(PhraseBase):
    pass


class PhraseRead(PhraseBase):
    id: int
    job_id: str
    status: str
    audio_filename: Optional[str] = None
    created_at: datetime