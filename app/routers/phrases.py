from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.job import Job
from app.models.phrase import Phrase
from app.schemas.phrase import PhraseCreate, PhraseRead


router = APIRouter()


@router.post("/jobs/{job_id}/phrases", response_model=PhraseRead, status_code=201)
def create_phrase(
    job_id: str,
    payload: PhraseCreate,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    phrase = Phrase.model_validate(payload)
    phrase.job_id = job_id

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase


@router.get("/jobs/{job_id}/phrases", response_model=List[PhraseRead])
def list_phrases_for_job(
    job_id: str,
    session: Session = Depends(get_session)
):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    statement = (
        select(Phrase)
        .where(Phrase.job_id == job_id)
        .order_by(Phrase.created_at.desc())
    )

    phrases = session.exec(statement).all()
    return phrases


@router.get("/phrases/{phrase_id}", response_model=PhraseRead)
def get_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    return phrase


@router.post("/phrases/{phrase_id}/approve", response_model=PhraseRead)
def approve_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    phrase.status = "approved"

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase


@router.post("/phrases/{phrase_id}/reject", response_model=PhraseRead)
def reject_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    phrase.status = "rejected"

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

    return phrase