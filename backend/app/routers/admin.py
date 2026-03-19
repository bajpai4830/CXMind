import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db import get_db
from app.deps import require_role, get_current_user, AuthUser
from app.models import Interaction, User, AuditLog, SystemJob
from app.topic_clustering import train_topic_model
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])

class RoleUpdate(BaseModel):
    role: str

@router.get("/users")
def list_users(limit: int = 25, offset: int = 0, db: Session = Depends(get_db)):
    users = db.query(User).order_by(desc(User.created_at)).offset(offset).limit(limit).all()
    total = db.query(User).count()
    return {
        "items": [
            {"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active, "created_at": u.created_at}
            for u in users
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.patch("/users/{user_id}/role")
def update_user_role(user_id: int, payload: RoleUpdate, adminer: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == adminer.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    old_role = user.role
    user.role = payload.role
    
    audit = AuditLog(actor_id=adminer.id, action="update_role", target_string=f"user_id={user_id}, from={old_role}, to={payload.role}")
    db.add(audit)
    db.commit()
    return {"message": "Role updated"}

@router.delete("/users/{user_id}")
def deactivate_user(user_id: int, adminer: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == adminer.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    user.is_active = False
    audit = AuditLog(actor_id=adminer.id, action="deactivate_user", target_string=f"user_id={user_id}")
    db.add(audit)
    db.commit()
    return {"message": "User deactivated"}

@router.get("/audit-logs")
def list_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog, User.email).outerjoin(User, AuditLog.actor_id == User.id).order_by(desc(AuditLog.created_at)).limit(limit).all()
    return [
        {
            "id": log.AuditLog.id,
            "actor_email": log.email or "System",
            "action": log.AuditLog.action,
            "target": log.AuditLog.target_string,
            "timestamp": log.AuditLog.created_at
        }
        for log in logs
    ]

@router.post("/retrain-topic-model")
def retrain_topic_model_endpoint(adminer: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(SystemJob).filter(SystemJob.job_name == "retrain_topic_model").first()
    if not job:
        job = SystemJob(job_name="retrain_topic_model", status="idle")
        db.add(job)
        db.commit()

    if job.status == "running":
        raise HTTPException(status_code=400, detail="Job is currently running in the background.")

    if job.last_run:
        time_since_run = dt.datetime.now(dt.timezone.utc) - job.last_run.replace(tzinfo=dt.timezone.utc)
        if time_since_run.total_seconds() < 1800:
            raise HTTPException(status_code=400, detail=f"Cooldown active. Please wait {int(30 - time_since_run.total_seconds() / 60)} minutes.")

    job.status = "running"
    job.triggered_by = adminer.id
    db.commit()

    try:
        interactions = db.query(Interaction).all()
        texts = [i.text for i in interactions]

        if len(texts) < 5:
            job.status = "idle"
            db.commit()
            return {"status": "not enough data", "count": len(texts)}

        train_topic_model(texts)

        job.status = "idle"
        job.last_run = dt.datetime.now(dt.timezone.utc)
        
        audit = AuditLog(actor_id=adminer.id, action="retrain_model", target_string=f"samples={len(texts)}")
        db.add(audit)
        db.commit()
        
        return {"status": "topic model retrained", "samples_used": len(texts)}
    except Exception as e:
        job.status = "idle"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Model error: {str(e)}")

@router.get("/system-jobs")
def get_system_jobs(db: Session = Depends(get_db)):
    jobs = db.query(SystemJob).all()
    return [{"job_name": j.job_name, "status": j.status, "last_run": j.last_run} for j in jobs]
