import os
import datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import SessionLocal
from app.models import Interaction, Report, Organization
from app.settings import get_settings

settings = get_settings()

SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"

jobstores = {
    "default": SQLAlchemyJobStore(url=settings.database_url)
}

scheduler = BackgroundScheduler(jobstores=jobstores)

def generate_weekly_reports():
    db: Session = SessionLocal()
    try:
        now = dt.datetime.now(dt.timezone.utc)
        start = now - dt.timedelta(days=7)
        
        orgs = db.query(Organization).all()
        for org in orgs:
            total = db.query(func.count(Interaction.id)).filter(
                Interaction.org_id == org.id,
                Interaction.created_at >= start,
                Interaction.created_at < now
            ).scalar() or 0
            
            avg = float(db.query(func.avg(Interaction.sentiment_compound)).filter(
                Interaction.org_id == org.id,
                Interaction.created_at >= start,
                Interaction.created_at < now
            ).scalar() or 0.0)
            
            summary = {
                "total_interactions_this_week": int(total),
                "average_sentiment_this_week": avg
            }
            
            report = Report(
                org_id=org.id,
                period_start=start,
                period_end=now,
                summary_json=summary,
                delivered=False
            )
            db.add(report)
        db.commit()
    except Exception as e:
        print(f"Error generating reports: {e}")
    finally:
        db.close()


def start_scheduler():
    if not SCHEDULER_ENABLED:
        return
        
    scheduler.add_job(
        generate_weekly_reports, 
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="generate_weekly_reports",
        replace_existing=True
    )
    scheduler.start()


def shutdown_scheduler():
    if SCHEDULER_ENABLED:
        scheduler.shutdown()
