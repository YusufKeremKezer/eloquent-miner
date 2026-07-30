from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class JobBase(SQLModel):
    source_type: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    language: str = "en"


class JobCreate(JobBase):
    pass


class JobRead(JobBase):
    id: str
    status: str
    created_at: datetime