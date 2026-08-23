from datetime import datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class Phrase(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    job_id: str = Field(index=True)

    phrase: str

    start: float | None = None
    end: float | None = None

    definition: str | None = None
    usage: str | None = None

    example_original: str | None = None
    example_new: str | None = None

    register: str | None = None

    alternatives: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON)
    )

    why_eloquent: str | None = None

    status: str = "candidate"

    audio_filename: str | None = None

    created_at: datetime = Field(default_factory=datetime.utcnow)