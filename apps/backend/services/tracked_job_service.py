# Path: apps/backend/services/tracked_job_service.py
from flask import current_app
from sqlalchemy.orm import joinedload, contains_eager
from datetime import datetime
import pytz

from ..app import db
from ..models import TrackedJob, JobOpportunity, Job, Company, JobAnalysis

class TrackedJobService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger

    def get_tracked_jobs(self, user_id: int, status_filter: str = None, search_query: str = None,
                         page: int = 1, limit: int = 10, job_id_filter: int = None):
        query = db.session.query(TrackedJob).filter(TrackedJob.user_id == user_id)
        query = query.join(TrackedJob.job_opportunity).join(JobOpportunity.job).outerjoin(Job.company)
        query = query.outerjoin(
            JobAnalysis,
            (JobAnalysis.job_id == Job.id) & (JobAnalysis.user_id == user_id)
        )
        query = query.options(
            contains_eager(TrackedJob.job_opportunity)
                .contains_eager(JobOpportunity.job)
                .contains_eager(Job.company),
            contains_eager(TrackedJob.job_opportunity)
                .contains_eager(JobOpportunity.job)
                .joinedload(Job.analyses)
        )

        if job_id_filter:
            query = query.filter(TrackedJob.id == job_id_filter)

        if status_filter:
            active_statuses = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS']
            inactive_statuses = ['REJECTED', 'WITHDRAWN', 'EXPIRED', 'OFFER_ACCEPTED']
            if status_filter == "Active Applications":
                query = query.filter(TrackedJob.status.in_(active_statuses))
            elif status_filter == "Inactive Applications":
                query = query.filter(TrackedJob.status.in_(inactive_statuses))

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Job.job_title.ilike(search_pattern),
                    Company.name.ilike(search_pattern)
                )
            )
        
        query = query.order_by(TrackedJob.updated_at.desc(), TrackedJob.id.desc())
        total_count = query.count() if not job_id_filter else 1
        offset = (page - 1) * limit
        tracked_jobs = query.offset(offset).limit(limit).all()

        results = []
        for tj in tracked_jobs:
            item = tj.to_dict()
            if tj.job_opportunity and tj.job_opportunity.job:
                job_obj = tj.job_opportunity.job
                item['job'] = job_obj.to_dict()
                item['company'] = job_obj.company.to_dict() if job_obj.company else None
                user_analysis = next((a for a in job_obj.analyses if a.user_id == user_id), None)
                if user_analysis:
                    item['job_analysis'] = user_analysis.to_dict()
                    item['ai_grade'] = user_analysis.matrix_rating
                else:
                    item['job_analysis'] = None
                    item['ai_grade'] = None
            if tj.job_opportunity:
                item['job_opportunity'] = tj.job_opportunity.to_dict()
            results.append(item)

        return {"jobs": results, "total_count": total_count, "page": page, "limit": limit}

    def update_tracked_job(self, user_id: int, tracked_job_id: int, payload: dict):
        tracked_job = db.session.query(TrackedJob).filter_by(id=tracked_job_id, user_id=user_id).first()
        if not tracked_job:
            self.logger.warning(f"Tracked job {tracked_job_id} not found for user {user_id}.")
            return None

        for field, value in payload.items():
            self.logger.info(f"Updating tracked_job {tracked_job_id}, field: {field}, value: {value}")
            if hasattr(tracked_job, field):
                if field == 'status':
                    old_status = tracked_job.status.value if tracked_job.status else None
                    new_status_str = value
                    if old_status != 'APPLIED' and new_status_str == 'APPLIED' and not tracked_job.applied_at:
                        tracked_job.applied_at = datetime.now(pytz.utc)
                    elif old_status == 'APPLIED' and new_status_str != 'APPLIED':
                        tracked_job.applied_at = None
                
                setattr(tracked_job, field, value)
            else:
                self.logger.warning(f"Attempted to update unknown or disallowed field: {field}")

        tracked_job.updated_at = datetime.now(pytz.utc)

        try:
            db.session.commit()
            db.session.refresh(tracked_job)
            full_job_data = self.get_tracked_jobs(user_id, job_id_filter=tracked_job_id)
            return full_job_data['jobs'][0] if full_job_data.get('jobs') else None
        except Exception as e:
            db.session.rollback()
            raise e

    def remove_tracked_job(self, user_id: int, tracked_job_id: int):
        tracked_job = db.session.query(TrackedJob).filter_by(id=tracked_job_id, user_id=user_id).first()
        if not tracked_job:
            return False
        try:
            db.session.delete(tracked_job)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise e

    def track_job(self, user_id: int, job_opportunity_id: int):
        existing_tracked_job = db.session.query(TrackedJob).filter_by(user_id=user_id, job_opportunity_id=job_opportunity_id).first()
        if existing_tracked_job:
            return existing_tracked_job
        
        new_tracked_job = TrackedJob(user_id=user_id, job_opportunity_id=job_opportunity_id, status='SAVED')
        db.session.add(new_tracked_job)
        try:
            db.session.commit()
            return new_tracked_job
        except Exception as e:
            db.session.rollback()
            raise e

    def get_tracked_job_by_opportunity_id(self, user_id: int, job_opportunity_id: int):
        return db.session.query(TrackedJob).filter_by(user_id=user_id, job_opportunity_id=job_opportunity_id).first()