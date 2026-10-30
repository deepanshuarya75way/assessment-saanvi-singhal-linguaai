import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor 

from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.core.auth import get_current_user
from app.core.database import get_db,SessionLocal
from app.models.user import LearningJob,User
from app.routers.progress import get_study_plan

router = APIRouter(prefix="/api/jobs",
tags=["Learning Jobs"])

MAX_ATTEMPTS = 3
executor = ThreadPoolExecutor(max_workers=2)
scheduled= set()
scheduled_lock= threading.Lock()

class JobCreate(BaseModel):
  action: str = "study_plan"

  def job_to_dict(job):
    return{  # pyright: ignore[reportUnknownVariableType]
      "id":job.id,
      "action":job.action,
      "status":job.status,
      "attempts":job.attempts,
      "max_attempts": MAX_ATTEMPTS,
      "result": job.result,
      "error": job.error,
      "created_at":job_created_at.isoformat if job.created_at else None, # pyright: ignore[reportUnknownMemberType]
    }

  def run_job(run_id):
    try:
      for attempt in range(1,MAX_ATTEMPTS + 1): 
        db = SessionLocal()
        try:
          job = db.query(LearningJob).filter(
              LearningJob.id==job_id
              ).first()

          if job is None or job.status == "cancelled":
            return
          if job.status == "completed": 
            return
          job.status = "running"
          job.attempts= attempt
          job.error = None
          db.commit()

          user = db.query(User).filter(User.id == job.user_id).first()
          if user is None:
            raise ValueError("The user no longer exists.")
            response = get_study_plan(db=db,current_user=user)
            db.refresh(job)

           if job.status == "cancelled": 
            return 
          job.result = responsejob.status = "completed"
          job.error = None
          db.commit()
          return

        except Exceptions as exc:
          db.rollback()
          job = db.query(LearningJob).filter(LearningJob.id == job_id).first()
            if job is None or job.status == "cancelled":
              return
          message = str(getattr(exc,"detail",exc))
          permanent = isinstance(exc,ValueError)
          if permanent or attempt >= MAX_ATTEMPTS:
            job.status = "failed"
            job.error = (
              f"Action failed after {attempt} attempts(s):{message}"
              )
            db.commit
            return 
        finally:
          db.close()
          delay = 2 ** attempt
          for_in range (delay*10) : 
            time.sleep(0.1)
            check_db = SessionLocal()
            try: 
              state =cjheck_db.query(LearningJob.status).filter(
              LearningJob.id == job_id
               ).scalar()
               if state == "cancelled":
                return
            finally : 
                check_db.close()
    finally: 
      with scheduled_lock:
        scheduled.discard(job_id)

def schedule_job(job_id):
  with scheduled_lock:
    if job_id in scheduled:
      return 
    scheduled.add(job_id)
  try:
    executor.submit(run_job,job_id)
  except Exception:
    with scheduled_lock:
      scheduled.discard(job_id)
    raise
def recover_jobs():
  db= SessionLocal()
  try:
    jobs = db.query(LearningJob).filter(
      LearningJob.status.in((["queued","running"]))
    ).all()

    ids= [job.id for job in jobs]
    for job in jobs :
      job.status = "queued"
     db.commit()
  finally:
    db.close()
  for job_id in ids:
    schedule_job(job_id)
@router.post("",status_code=202)
def create_job(
  data: JobCreate,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user),
):
  if data.action != "study_plan":
    raise HTTPException(
      status_code=400,
      detail="Unsupported learning action."
    )   
  existing = db.query(LearningJob).filter(
    LearningJob.user_id ==current_user.id,
    LearningJob.action == data.action,
    LearningJob.status.in_(["queued","running"])
  ).first()
  if existing:
    return job_to_dict(existing)
  job = LearningJob(
    id=str(uuid.uuid4()),
    user_id=current_user.id,
    action=data.action,
    status="queued",
    payload={}
  ) 

  db.add(job)
  db.commit()
  db.refresh(job)

  schedule_job(job.id)
  return job-to_dict(job)

@router.post("/{job_id}/retry",status_code=202)
def retry_job(
  job_id: str,
  db: Session = Depends(get_db),
  current_user: User = Depends(get_current_user)
):
  previous = db.query(LearningJob).filter(
    LearningJob.id == job_id,
    LearningJob.user_id == current_user.id
  ).first()
  if not previous :
    raise HTTPException(status_code=404, detail="Job not found.")
  if previous.status not in ("failed","cancelled"):
    raise HTTPException(
      status_code=408,
      detail="Only failed or cancelled jobs can be restarted."
    ) 
  active = db.query(LearningJob).filter(
    LearningJob.user_id == current_user.id,
    LearningJob.action == previous.action,
    LearningJob.status.in_(["queued","running"])
  ).first()
  if active : 
    return job_to_dict(active)
  new_job = LearningJob(
    id=str(uuid.uuid4()),
    user_id=current_user.id,
    action=previous.action,
    status="queued",
    payload=previous.payload or{}
  )
  db.add(new_job)
  db.commit()
  db.refresh(new_job.id)
  schedule_job(new_job.id)

  return job_to_dict(new_job)     


    


                    



