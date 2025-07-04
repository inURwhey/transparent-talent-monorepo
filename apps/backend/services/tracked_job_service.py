# Path: apps/backend/services/tracked_job_service.py
from flask import current_app
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import pytz
from sqlalchemy.exc import IntegrityError # For duplicate tracking errors

from ..app import db
from ..models import TrackedJob, User, JobOpportunity, Job, Company, JobAnalysis # Import all relevant models
from ..config import config

class TrackedJobService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger

    def get_tracked_jobs(self, user_id: int, status_filter: str = None, search_query: str = None,
                         page: int = 1, limit: int = 10):
        """
        Retrieves tracked jobs for a user with optional filtering, search, and pagination.
        Includes related JobOpportunity, canonical Job, Company, and JobAnalysis data.
        """
        query = db.session.query(TrackedJob).filter(TrackedJob.user_id == user_id)

        # Eager load relationships to avoid N+1 queries
        query = query.options(
            joinedload(TrackedJob.job_opportunity).joinedload(JobOpportunity.job).joinedload(Job.company),
            # Load all analyses for the canonical job, then filter in Python for this user
            # This is less efficient than a subqueryload for a single analysis, but robust.
            # A more optimized query for *just one* analysis for *this* user would involve a subquery/correlation.
            joinedload(TrackedJob.job_opportunity).joinedload(JobOpportunity.job).joinedload(Job.analyses)
        )

        if status_filter:
            if status_filter == "Active Applications":
                query = query.filter(TrackedJob.status.in_(['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS']))
            elif status_filter == "Inactive Applications":
                query = query.filter(TrackedJob.status.in_(['REJECTED', 'WITHDRAWN', 'EXPIRED', 'OFFER_ACCEPTED']))
            elif status_filter == "Active Job Postings":
                # Filter on the JobOpportunity status
                query = query.filter(JobOpportunity.is_active == True)
            elif status_filter == "Expired Job Postings":
                # Filter on the JobOpportunity status
                query = query.filter(JobOpportunity.is_active == False)
            else:
                # Direct match for specific ENUM status
                query = query.filter(TrackedJob.status == status_filter)

        if search_query:
            search_pattern = f"%{search_query}%"
            # Search across job title, company name, notes, next_action_notes
            query = query.filter(
                (Job.job_title.ilike(search_pattern)) |
                (Company.name.ilike(search_pattern)) |
                (TrackedJob.notes.ilike(search_pattern)) |
                (TrackedJob.next_action_notes.ilike(search_pattern))
            )
        
        # Order by created_at or updated_at, and then by ID for stable pagination
        query = query.order_by(TrackedJob.updated_at.desc(), TrackedJob.id.desc())

        # Pagination
        total_count = query.count()
        offset = (page - 1) * limit
        tracked_jobs = query.offset(offset).limit(limit).all()

        results = []
        for tj in tracked_jobs:
            item = tj.to_dict()
            
            # Manually add nested data using relationships
            if tj.job_opportunity:
                item['job_opportunity'] = tj.job_opportunity.to_dict()
                if tj.job_opportunity.job:
                    item['job'] = tj.job_opportunity.job.to_dict()
                    # Add company info
                    if tj.job_opportunity.job.company:
                        item['company'] = tj.job_opportunity.job.company.to_dict()
                    
                    # Find the correct analysis for this user and canonical job
                    # Each canonical job can have many analyses (one per user)
                    user_analysis = next((a for a in tj.job_opportunity.job.analyses if a.user_id == user_id), None)
                    if user_analysis:
                        item['job_analysis'] = user_analysis.to_dict()
                        item['ai_grade'] = user_analysis.matrix_rating # Expose AI grade directly
                    else:
                        item['job_analysis'] = None
                        item['ai_grade'] = None # No analysis yet
            
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
        tracked_job = TrackedJob.query.filter_by(id=tracked_job_id, user_id=user_id).first()
        if not tracked_job:
            self.logger.warning(f"Tracked job {tracked_job_id} not found for user {user_id}.")
            return None

        current_app.logger.info(f"Updating tracked_job {tracked_job_id}, field: {field}, value: {value}")

        if field == 'status':
            old_status = tracked_job.status.value if tracked_job.status else None # Get string value
            new_status_str = value # Value from frontend is string
            
            # Convert string to ENUM member
            try:
                new_status_enum = tracked_job.status.type.enum_class[new_status_str]
                tracked_job.status = new_status_enum
            except KeyError:
                self.logger.error(f"Invalid status value: {new_status_str}")
                return None # Or raise an error

            # Set applied_at timestamp if status changes to 'APPLIED'
            if old_status != 'APPLIED' and new_status_str == 'APPLIED':
                tracked_job.applied_at = datetime.now(pytz.utc)
            elif old_status == 'APPLIED' and new_status_str not in ['APPLIED', 'OFFER_ACCEPTED', 'REJECTED', 'INTERVIEWING']:
                # Clear applied_at if changing from applied to non-terminal/non-interview states
                tracked_job.applied_at = None
            
            # Set milestone timestamps based on state transitions from DATA_LIFECYCLE.md
            if new_status_str == 'INTERVIEWING' and tracked_job.first_interview_at is None:
                tracked_job.first_interview_at = datetime.now(pytz.utc)
            if new_status_str == 'OFFER_NEGOTIATIONS' and tracked_job.offer_received_at is None:
                tracked_job.offer_received_at = datetime.now(pytz.utc)
            
            # Set resolved_at for terminal states
            terminal_states = ['OFFER_ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXPIRED']
            if new_status_str in terminal_states and tracked_job.resolved_at is None:
                tracked_job.resolved_at = datetime.now(pytz.utc)
            elif old_status in terminal_states and new_status_str not in terminal_states:
                # If moving out of a terminal state, clear resolved_at
                tracked_job.resolved_at = None


        elif field == 'is_excited':
            tracked_job.is_excited = bool(value)
        elif field == 'notes':
            tracked_job.notes = value
        elif field == 'next_action_at':
            if value:
                try:
                    # Assume value is an ISO 8601 string or similar
                    # Ensure datetime object is timezone-aware before saving
                    dt_obj = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    tracked_job.next_action_at = dt_obj.astimezone(pytz.utc) if dt_obj.tzinfo is None else dt_obj
                except ValueError:
                    self.logger.error(f"Invalid date format for next_action_at: {value}. Setting to None.")
                    tracked_job.next_action_at = None
            else:
                tracked_job.next_action_at = None # Clear if value is empty/null
        elif field == 'next_action_notes':
            tracked_job.next_action_notes = value
        else:
            self.logger.warning(f"Attempted to update unknown or disallowed field: {field}")
            return None

        tracked_job.updated_at = datetime.now(pytz.utc) # Always update timestamp

        try:
            db.session.commit()
            db.session.refresh(tracked_job)
            return tracked_job.to_dict()
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating tracked job {tracked_job_id}: {e}")
            raise e

    def remove_tracked_job(self, user_id: int, tracked_job_id: int):
        """Removes a tracked job for a user."""
        tracked_job = TrackedJob.query.filter_by(id=tracked_job_id, user_id=user_id).first()
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
        existing_tracked_job = TrackedJob.query.filter_by(user_id=user_id, job_opportunity_id=job_opportunity_id).first()

        if existing_tracked_job:
            self.logger.info(f"Job opportunity {job_opportunity_id} already tracked by user {user_id}.")
            # Return existing tracked job (e.g., to indicate it's already there)
            return existing_tracked_job
        
        new_tracked_job = TrackedJob(
            user_id=user_id,
            job_opportunity_id=job_opportunity_id,
            created_at=datetime.now(pytz.utc),
            updated_at=datetime.now(pytz.utc),
            status='SAVED' # Initial status
        )
        db.session.add(new_tracked_job)
        try:
            db.session.commit()
            db.session.refresh(new_tracked_job)
            self.logger.info(f"Job opportunity {job_opportunity_id} successfully tracked for user {user_id}.")
            return new_tracked_job
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error tracking job opportunity {job_opportunity_id} for user {user_id}: {e}")
            raise e

    def get_tracked_job_by_opportunity_id(self, user_id: int, job_opportunity_id: int):
        """Fetches a single tracked job by user ID and job opportunity ID."""
        return TrackedJob.query.filter_by(user_id=user_id, job_opportunity_id=job_opportunity_id).first()