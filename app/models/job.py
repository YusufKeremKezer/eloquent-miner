from datetime import datetime
from typing import Optional
import uuid

from sqlmodel import SQLModel, Field


class Job(SQLModel, table=True):
    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )

    status: str = "pending"

    source_type: Optional[str] = None
    source_url: Optional[str] = None
    title: Optional[str] = None

    language: str = "en"

    created_at: datetime = Field(default_factory=datetime.utcnow)