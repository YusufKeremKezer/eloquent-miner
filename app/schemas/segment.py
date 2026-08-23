
from sqlmodel import Field, SQLModel


class SegmentBase(SQLModel):
    start: float | None = None
    end: float | None = None
    text: str


class SegmentCreate(SegmentBase):
    pass


class SegmentRead(SegmentBase):
    id: int
    job_id: str


class TranscriptInput(SQLModel):
    language: str | None = None
    replace: bool = True

    raw_text: str | None = None

    segments: list[SegmentCreate] = Field(default_factory=list)