from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.job import Job
from app.schemas.job import JobCreate, JobRead


router = APIRouter()


@router.post("", response_model=JobRead, status_code=201)
def create_job(payload: JobCreate, session: Session = Depends(get_session)):
    job = Job.model_validate(payload)

    session.add(job)
    session.commit()
    session.refresh(job)

    return job


@router.get("", response_model=List[JobRead])
def list_jobs(session: Session = Depends(get_session)):
    statement = select(Job).order_by(Job.created_at.desc())
    jobs = session.exec(statement).all()
    return jobs


@router.get("/{job_id}", response_model=JobRead)
def get_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, session: Session = Depends(get_session)):
    job = session.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    session.delete(job)
    session.commit()

    return None