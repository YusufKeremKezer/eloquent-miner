from typing import Optional

from sqlmodel import SQLModel, Field


class Segment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    job_id: str = Field(index=True)

    start: Optional[float] = None
    end: Optional[float] = None

    text: str