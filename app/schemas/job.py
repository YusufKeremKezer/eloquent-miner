from datetime import datetime

from sqlmodel import SQLModel


class JobBase(SQLModel):
    source_type: str
    source_url: str | None = None
    title: str | None = None
    language: str = "en"


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    id: str
    status: str
    created_at: datetime