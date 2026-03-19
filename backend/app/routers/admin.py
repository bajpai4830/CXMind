import datetime as dt
from fastapi import APIRouter, Depends, HTTPException, status, Request
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
def update_user_role(user_id: int, payload: RoleUpdate, request: Request, adminer: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Self-demotion guard
    if user.id == adminer.id and payload.role != "admin":
        raise HTTPException(status_code=403, detail="Cannot demote your own admin account.")
        
    # Assure at least one active admin remains if demoting an admin
    if user.role == "admin" and payload.role != "admin":
        active_admins = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        if active_admins <= 1:
            raise HTTPException(status_code=403, detail="Cannot demote the last active admin.")
    
    old_role = user.role
    user.role = payload.role
    
    audit = AuditLog(
        actor_id=adminer.id, 
        action="update_role", 
        target_id=user_id,
        target_type="user",
        metadata_={"from": old_role, "to": payload.role},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit)
    db.commit()
    return {"message": "Role updated"}

@router.delete("/users/{user_id}")
def deactivate_user(user_id: int, request: Request, adminer: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user.id == adminer.id:
        raise HTTPException(status_code=403, detail="Cannot deactivate yourself")

    if user.role == "admin":
        active_admins = db.query(User).filter(User.role == "admin", User.is_active == True).count()
        if active_admins <= 1:
            raise HTTPException(status_code=403, detail="Cannot deactivate the last active admin.")

    user.is_active = False
    
    # Cascade invalidation to existing JWT cookies
    user.token_version += 1
    
    audit = AuditLog(
        actor_id=adminer.id, 
        action="deactivate_user", 
        target_id=user_id,
        target_type="user",
        metadata_={},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    db.add(audit)
    db.commit()
    return {"message": "User deactivated and sessions revoked"}

@router.get("/audit-logs")
def list_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    logs = db.query(AuditLog, User.email).outerjoin(User, AuditLog.actor_id == User.id).order_by(desc(AuditLog.created_at)).limit(limit).all()
    return [
        {
            "id": log.AuditLog.id,
            "actor_email": log.email or "System",
            "action": log.AuditLog.action,
            "target": f"Type: {log.AuditLog.target_type} ID: {log.AuditLog.target_id}",
            "timestamp": log.AuditLog.created_at,
            "metadata": log.AuditLog.metadata_
        }
        for log in logs
    ]

@router.post("/retrain-topic-model")
def retrain_topic_model_endpoint(request: Request, adminer: AuthUser = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # DB-level atomic lock (SELECT FOR UPDATE) to conquer TOCTOU race conditions under multi-worker setups
        job = db.query(SystemJob).filter(SystemJob.job_name == "retrain_topic_model").with_for_update(nowait=True).first()
        if not job:
            job = SystemJob(job_name="retrain_topic_model", status="idle")
            db.add(job)
            db.commit()
            # Reacquire lock on newly established row
            job = db.query(SystemJob).filter(SystemJob.job_name == "retrain_topic_model").with_for_update(nowait=True).first()

        if job.status == "running":
            db.rollback()
            raise HTTPException(status_code=400, detail="Job is currently running in the background.")

        if job.last_run:
            time_since_run = dt.datetime.now(dt.timezone.utc) - job.last_run.replace(tzinfo=dt.timezone.utc)
            if time_since_run.total_seconds() < 1800:
                db.rollback()
                raise HTTPException(status_code=400, detail=f"Cooldown active. Please wait {int(30 - time_since_run.total_seconds() / 60)} minutes.")

        job.status = "running"
        job.triggered_by = adminer.id
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Could not obtain lock. Job is already actively provisioning.")

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
        
        audit = AuditLog(
            actor_id=adminer.id, 
            action="retrain_model", 
            target_id=job.id,
            target_type="job",
            metadata_={"samples": len(texts)},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
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
