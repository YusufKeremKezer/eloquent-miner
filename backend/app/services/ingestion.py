import re

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models.job import Job
from app.models.segment import Segment
from app.schemas.segment import TranscriptInput


def delete_segments_for_job(session: Session, job_id: str) -> None:
    statement = select(Segment).where(Segment.job_id == job_id)
    segments = session.exec(statement).all()

    for segment in segments:
        session.delete(segment)


def split_text_into_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()

    parts = re.split(r"(?<=[.!?])\s+", text)

    return [part.strip() for part in parts if part.strip()]


def raw_text_to_segments(raw_text: str) -> list[Segment]:
    segments: list[Segment] = []

    lines = raw_text.splitlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if len(line) <= 300:
            segments.append(
                Segment(
                    start=None,
                    end=None,
                    text=line
                )
            )
        else:
            sentences = split_text_into_sentences(line)

            for sentence in sentences:
                segments.append(
                    Segment(
                        start=None,
                        end=None,
                        text=sentence
                    )
                )

    if not segments and raw_text.strip():
        sentences = split_text_into_sentences(raw_text)

        for sentence in sentences:
            segments.append(
                Segment(
                    start=None,
                    end=None,
                    text=sentence
                )
            )

    return segments


def validate_segment_times(payload: TranscriptInput) -> None:
    for segment in payload.segments:
        if segment.start is not None and segment.end is not None:
            if segment.end < segment.start:
                raise HTTPException(
                    status_code=422,
                    detail="Segment end time cannot be before start time."
                )


def ingest_transcript(
    session: Session,
    job: Job,
    payload: TranscriptInput
) -> list[Segment]:
    has_segments = len(payload.segments) > 0
    has_raw_text = bool(payload.raw_text and payload.raw_text.strip())

    if not has_segments and not has_raw_text:
        raise HTTPException(
            status_code=400,
            detail="Provide either segments or raw_text."
        )

    validate_segment_times(payload)

    if payload.replace:
        delete_segments_for_job(session, job.id)

    if payload.language:
        job.language = payload.language

    new_segments: list[Segment] = []

    if has_segments:
        for item in payload.segments:
            segment = Segment(
                job_id=job.id,
                start=item.start,
                end=item.end,
                text=item.text.strip()
            )
            new_segments.append(segment)
    elif has_raw_text:
        generated_segments = raw_text_to_segments(payload.raw_text)

        for segment in generated_segments:
            segment.job_id = job.id
            new_segments.append(segment)

    for segment in new_segments:
        session.add(segment)

    job.status = "transcript_ready"
    session.add(job)

    session.commit()

    for segment in new_segments:
        session.refresh(segment)

    return new_segments