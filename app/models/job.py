import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


class Job(SQLModel, table=True):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )

    status: str = "pending"

    source_type: str | None = None
    source_url: str | None = None
    title: str | None = None

    language: str = "en"

    created_at: datetime = Field(default_factory=datetime.utcnow)