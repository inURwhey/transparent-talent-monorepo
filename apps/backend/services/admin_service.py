# Path: apps/backend/services/admin_service.py
from flask import current_app
from ..app import db # NEW: Import db
from ..config import config
from ..models import Job, JobOpportunity, TrackedJob, JobAnalysis, Company, User # Import all models
from .job_service import JobService # We need the URL validity checker
from .company_service import CompanyService # NEW: Import CompanyService
from datetime import datetime, timedelta
import pytz
import re # for URL patterns
import hashlib # For job_description_hash computation

class AdminService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.job_service = JobService(self.logger)
        self.company_service = CompanyService(self.logger)

    # Note: DB reset moved to admin route for direct endpoint access and safety

    # Method to run URL validity checks (previously in app.py)
    def check_job_url_validity(self):
        """
        Checks the validity of job URLs and updates their status.
        - Marks URLs as expired if unreachable or older than 60 days.
        - Identifies and marks legacy malformed URLs.
        This operates on JobOpportunity records now.
        """
        self.logger.info("Starting job URL validity check.")
        
        # Step 1: Mark unreachable or malformed URLs
        opportunities_to_check = JobOpportunity.query.filter(
            JobOpportunity.is_active == True,
            # Only check opportunities that haven't been checked recently (e.g., last 7 days)
            db.or_(
                JobOpportunity.last_checked_at == None,
                JobOpportunity.last_checked_at < datetime.now(pytz.utc) - timedelta(days=7)
            )
        ).limit(100).all() # Process in batches

        checked_count = 0
        marked_unreachable_count = 0
        marked_legacy_malformed_count = 0

        # Regex for common malformed placeholders from old system
        MALFORMED_URL_PATTERNS = [
            re.compile(r'https?://[a-zA-Z0-9.-]+\.com/job-not-found'),
            re.compile(r'https?://[a-zA-Z0-9.-]+\.com/temp-url'),
            re.compile(r'https?://[a-zA-Z0-9.-]+\.com/placeholder-url')
        ]

        for opportunity in opportunities_to_check:
            is_malformed_legacy = any(pattern.match(opportunity.url) for pattern in MALFORMED_URL_PATTERNS)
            
            if is_malformed_legacy:
                opportunity.is_active = False
                opportunity.last_checked_at = datetime.now(pytz.utc)
                # You might want a specific status_reason for the opportunity if needed
                marked_legacy_malformed_count += 1
                self.logger.info(f"Marked legacy malformed URL: {opportunity.url}")
            else:
                try:
                    # Perform a HEAD request to check reachability without downloading full content
                    response = requests.head(opportunity.url, timeout=5)
                    if response.status_code >= 400: # Client error or server error
                        opportunity.is_active = False
                        marked_unreachable_count += 1
                        self.logger.info(f"Marked unreachable URL (status {response.status_code}): {opportunity.url}")
                    else:
                        opportunity.is_active = True # Ensure it's active if reachable
                except requests.exceptions.RequestException as e:
                    opportunity.is_active = False
                    marked_unreachable_count += 1
                    self.logger.info(f"Marked unreachable URL (exception {e.__class__.__name__}): {opportunity.url}")
                except Exception as e:
                    self.logger.error(f"Unexpected error checking URL {opportunity.url}: {e}", exc_info=True)
                    opportunity.is_active = False # Mark as inactive on unexpected error too

            opportunity.last_checked_at = datetime.now(pytz.utc)
            db.session.add(opportunity) # Mark for update
            checked_count += 1
        
        try:
            db.session.commit()
            self.logger.info(f"URL validity check complete. Checked {checked_count} opportunities. Marked {marked_unreachable_count} unreachable, {marked_legacy_malformed_count} legacy malformed.")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during URL validity check commit: {e}", exc_info=True)

    # Method to check for stale tracked applications
    def check_stale_applications(self):
        """
        Checks for tracked jobs that are considered stale (no activity for X days)
        and marks them as 'EXPIRED' with a 'Stale - No action in X days' reason.
        This operates on TrackedJob records.
        """
        self.logger.info("Starting stale application check.")
        stale_threshold_days = 30 # Configurable threshold

        stale_applications = TrackedJob.query.filter(
            # Exclude already terminal states
            TrackedJob.status.in_(['SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS']),
            TrackedJob.updated_at < datetime.now(pytz.utc) - timedelta(days=stale_threshold_days),
            db.or_(
                TrackedJob.next_action_at == None, # No next action planned
                TrackedJob.next_action_at < datetime.now(pytz.utc) # Next action date is in the past
            )
        ).limit(100).all() # Process in batches

        marked_stale_count = 0
        for app in stale_applications:
            app.status = 'EXPIRED' # Set to ENUM member
            app.status_reason = f"Stale - No action in {stale_threshold_days} days"
            app.resolved_at = datetime.now(pytz.utc)
            app.updated_at = datetime.now(pytz.utc)
            db.session.add(app)
            marked_stale_count += 1
            self.logger.info(f"Marked stale tracked job ID: {app.id}")
        
        try:
            db.session.commit()
            self.logger.info(f"Stale application check complete. Marked {marked_stale_count} applications as stale.")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during stale application check commit: {e}", exc_info=True)