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
                         page: int = 1, limit: int = 10):
        """
        Retrieves tracked jobs for a user with optional filtering, search, and pagination.
        This version is refactored to be robust against missing relational data and to
        correctly serialize SQLAlchemy ORM objects.
        """
        # Start with the base query for TrackedJob
        query = db.session.query(TrackedJob).filter(TrackedJob.user_id == user_id)

        # Explicitly join all related tables for filtering and eager loading
        query = query.join(TrackedJob.job_opportunity).join(JobOpportunity.job).outerjoin(Job.company)
        
        # We need the analysis specific to the user, so we do a specific outer join for that.
        query = query.outerjoin(
            JobAnalysis,
            (JobAnalysis.job_id == Job.id) & (JobAnalysis.user_id == user_id)
        )

        # Use contains_eager to load the data from the tables we've already joined.
        # This is more efficient than separate joinedload calls.
        query = query.options(
            contains_eager(TrackedJob.job_opportunity)
                .contains_eager(JobOpportunity.job)
                .contains_eager(Job.company),
            contains_eager(TrackedJob.job_opportunity)
                .contains_eager(JobOpportunity.job)
                .contains_eager(Job.analyses) # This now refers to the specific user's analysis
        )

        # --- Filtering Logic ---
        if status_filter:
            active_statuses = ['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS']
            inactive_statuses = ['REJECTED', 'WITHDRAWN', 'EXPIRED', 'OFFER_ACCEPTED']
            if status_filter == "Active Applications":
                query = query.filter(TrackedJob.status.in_(active_statuses))
            elif status_filter == "Inactive Applications":
                query = query.filter(TrackedJob.status.in_(inactive_statuses))
            # No need to handle job posting status here, as the frontend can derive it.

        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                db.or_(
                    Job.job_title.ilike(search_pattern),
                    Company.name.ilike(search_pattern),
                    TrackedJob.notes.ilike(search_pattern),
                    TrackedJob.next_action_notes.ilike(search_pattern)
                )
            )
        
        # Order by created_at or updated_at, and then by ID for stable pagination
        query = query.order_by(TrackedJob.updated_at.desc(), TrackedJob.id.desc())

        # --- Pagination ---
        total_count = query.count()
        offset = (page - 1) * limit
        tracked_jobs = query.offset(offset).limit(limit).all()

        # --- Safe and Robust Serialization ---
        results = []
        for tj in tracked_jobs:
            item = tj.to_dict()
            
            # The query is structured to eagerly load the correct nested objects.
            # We just need to serialize them safely.
            if tj.job_opportunity and tj.job_opportunity.job:
                job_obj = tj.job_opportunity.job
                item['job'] = job_obj.to_dict()
                
                # Safely add company info
                item['company'] = job_obj.company.to_dict() if job_obj.company else None
                
                # The join and contains_eager for JobAnalysis loads the specific user's analysis
                # into the 'analyses' relationship on the job object. It will either be a list
                # with one item, or an empty list.
                user_analysis = job_obj.analyses[0] if job_obj.analyses else None
                
                if user_analysis:
                    item['job_analysis'] = user_analysis.to_dict()
                    item['ai_grade'] = user_analysis.matrix_rating
                else:
                    item['job_analysis'] = None
                    item['ai_grade'] = None
            
            # Always include the job_opportunity itself for the frontend
            if tj.job_opportunity:
                item['job_opportunity'] = tj.job_opportunity.to_dict()

            results.append(item)

        return {
            "jobs": results,
            "total_count": total_count,
            "page": page,
            "limit": limit
        }

    def update_tracked_job_field(self, user_id: int, tracked_job_id: int, field: str, value):
        """
        Updates a specific field of a tracked job.
        Handles special logic for status changes (e.g., applied_at).
        """
        tracked_job = db.session.query(TrackedJob).filter_by(id=tracked_job_id, user_id=user_id).first()
        if not tracked_job:
            self.logger.warning(f"Tracked job {tracked_job_id} not found for user {user_id}.")
            return None

        self.logger.info(f"Updating tracked_job {tracked_job_id}, field: {field}, value: {value}")

        if field == 'status':
            old_status = tracked_job.status.value if tracked_job.status else None
            new_status_str = value

            if old_status != 'APPLIED' and new_status_str == 'APPLIED':
                tracked_job.applied_at = datetime.now(pytz.utc)
            elif old_status == 'APPLIED' and new_status_str != 'APPLIED':
                tracked_job.applied_at = None

            terminal_states = ['OFFER_ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXPIRED']
            if new_status_str in terminal_states and tracked_job.resolved_at is None:
                tracked_job.resolved_at = datetime.now(pytz.utc)
            elif old_status in terminal_states and new_status_str not in terminal_states:
                tracked_job.resolved_at = None

            if new_status_str == 'INTERVIEWING' and tracked_job.first_interview_at is None:
                tracked_job.first_interview_at = datetime.now(pytz.utc)
            if new_status_str == 'OFFER_NEGOTIATIONS' and tracked_job.offer_received_at is None:
                tracked_job.offer_received_at = datetime.now(pytz.utc)

            try:
                # Safely convert string to Enum member
                tracked_job.status = new_status_str
            except (ValueError, KeyError) as e:
                self.logger.error(f"Invalid status value provided: {new_status_str}. Error: {e}")
                return None

        elif field == 'is_excited':
            tracked_job.is_excited = bool(value)
        elif field == 'notes':
            tracked_job.notes = value
        elif field == 'next_action_at':
            if value:
                try:
                    dt_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    tracked_job.next_action_at = dt_obj.astimezone(pytz.utc) if dt_obj.tzinfo is None else dt_obj
                except (ValueError, TypeError):
                    self.logger.error(f"Invalid date format for next_action_at: {value}. Setting to None.")
                    tracked_job.next_action_at = None
            else:
                tracked_job.next_action_at = None
        elif field == 'next_action_notes':
            tracked_job.next_action_notes = value
        else:
            self.logger.warning(f"Attempted to update unknown or disallowed field: {field}")
            return None

        tracked_job.updated_at = datetime.now(pytz.utc)

        try:
            db.session.commit()
            db.session.refresh(tracked_job)
            # Re-fetch the full object for the response to ensure all relations are current
            full_job_data = self.get_tracked_jobs(user_id, page=1, limit=1, search_query=f"id:{tracked_job_id}")
            if full_job_data['jobs']:
                 return full_job_data['jobs'][0]
            return tracked_job.to_dict() # Fallback
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating tracked job {tracked_job_id}: {e}")
            raise e

    def remove_tracked_job(self, user_id: int, tracked_job_id: int):
        """Removes a tracked job for a user."""
        tracked_job = db.session.query(TrackedJob).filter_by(id=tracked_job_id, user_id=user_id).first()
        if not tracked_job:
            self.logger.warning(f"Tracked job {tracked_job_id} not found for user {user_id}.")
            return False

        try:
            db.session.delete(tracked_job)
            db.session.commit()
            self.logger.info(f"Tracked job {tracked_job_id} deleted for user {user_id}.")
            return True
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deleting tracked job {tracked_job_id}: {e}")
            raise e

    def track_job(self, user_id: int, job_opportunity_id: int):
        """
        Allows a user to track a specific job opportunity.
        Checks for existing tracking to prevent duplicates.
        """
        existing_tracked_job = db.session.query(TrackedJob).filter_by(user_id=user_id, job_opportunity_id=job_opportunity_id).first()
        if existing_tracked_job:
            self.logger.info(f"Job opportunity {job_opportunity_id} already tracked by user {user_id}.")
            return existing_tracked_job
        
        new_tracked_job = TrackedJob(
            user_id=user_id,
            job_opportunity_id=job_opportunity_id,
            status='SAVED'
        )
        db.session.add(new_tracked_job)
        try:
            db.session.commit()
            return new_tracked_job
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error tracking job opportunity {job_opportunity_id} for user {user_id}: {e}")
            raise e

    def get_tracked_job_by_opportunity_id(self, user_id: int, job_opportunity_id: int):
        """Fetches a single tracked job by user ID and job opportunity ID."""
        return db.session.query(TrackedJob).filter_by(user_id=user_id, job_opportunity_id=job_opportunity_id).first()