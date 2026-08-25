
from sqlmodel import Field, SQLModel


class Segment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)

    job_id: str = Field(index=True)

    start: float | None = None
    end: float | None = None

    text: str