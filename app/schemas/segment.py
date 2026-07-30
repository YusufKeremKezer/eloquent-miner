from typing import Optional, List

from sqlmodel import SQLModel, Field


class SegmentBase(SQLModel):
    start: Optional[float] = None
    end: Optional[float] = None
    text: str


class SegmentCreate(SegmentBase):
    pass


class SegmentRead(SegmentBase):
    id: int
    job_id: str


class TranscriptInput(SQLModel):
    language: Optional[str] = None
    replace: bool = True

    raw_text: Optional[str] = None

    segments: List[SegmentCreate] = Field(default_factory=list)