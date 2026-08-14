from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.job import Job
from app.models.phrase import Phrase
from app.schemas.phrase import PhraseCreate, PhraseRead

router = APIRouter()


class PhraseUpdate(BaseModel):
    phrase: Optional[str] = None
    definition: Optional[str] = None
    usage: Optional[str] = None
    example_original: Optional[str] = None
    example_new: Optional[str] = None
    register: Optional[str] = None
    alternatives: Optional[List[str]] = None
    why_eloquent: Optional[str] = None
    start: Optional[float] = None
    end: Optional[float] = None
    status: Optional[str] = None


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


@router.patch("/phrases/{phrase_id}", response_model=PhraseRead)
def update_phrase(
    phrase_id: int,
    payload: PhraseUpdate,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    # Update only provided fields
    update_data = payload.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(phrase, key, value)

    session.add(phrase)
    session.commit()
    session.refresh(phrase)

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


@router.delete("/phrases/{phrase_id}", status_code=204)
def delete_phrase(
    phrase_id: int,
    session: Session = Depends(get_session)
):
    phrase = session.get(Phrase, phrase_id)

    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    session.delete(phrase)
    session.commit()

    return None