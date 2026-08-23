from datetime import datetime

from sqlmodel import Field, SQLModel


class PhraseBase(SQLModel):
    phrase: str

    start: float | None = None
    end: float | None = None

    definition: str | None = None
    usage: str | None = None

    example_original: str | None = None
    example_new: str | None = None

    register: str | None = None

    alternatives: list[str] = Field(default_factory=list)

    why_eloquent: str | None = None


class PhraseCreate(PhraseBase):
    pass


class PhraseRead(PhraseBase):
    id: int
    job_id: str
    status: str
    audio_filename: str | None = None
    created_at: datetime