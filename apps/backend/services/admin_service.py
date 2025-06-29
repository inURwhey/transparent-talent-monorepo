from datetime import datetime, timezone, timedelta
from ..config import config
from ..database import get_db
from .job_service import JobService # We need the URL validity checker

class AdminService:
    def __init__(self, logger):
        """
        Initializes the Admin Service.
        Args:
            logger: The Flask app's logger instance.
        """
        self.logger = logger
        # The AdminService needs to check URL validity, so it uses an instance of JobService.
        self.job_service = JobService(logger)

    def check_and_expire_job_postings(self):
        """
        Checks job postings for validity and age, updating their status accordingly.
        This is intended to be run as a scheduled task.
        Returns a summary of the operation.
        """
        db = get_db()
        with db.cursor() as cur:
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=config.JOB_POSTING_MAX_AGE_DAYS)

            # Select jobs that need checking based on several criteria
            cur.execute("""
                SELECT id, job_url, status, found_at, last_checked_at
                FROM jobs
                WHERE status = 'Active' AND (
                    last_checked_at IS NULL OR last_checked_at < %s OR found_at < %s
                )
                LIMIT 1000;
            """, (twenty_four_hours_ago, sixty_days_ago))
            jobs_to_check = cur.fetchall()

            self.logger.info(f"Found {len(jobs_to_check)} job postings to check for expiration.")
            
            updated_count = 0
            for job in jobs_to_check:
                new_status = job['status']
                
                # 1. Check for age first
                if job['found_at'] and job['found_at'] < sixty_days_ago:
                    new_status = 'Expired - Time Based'
                    self.logger.info(f"Job ID {job['id']} is >{config.JOB_POSTING_MAX_AGE_DAYS} days old. Marking as '{new_status}'.")
                
                # 2. If not expired by age, check URL validity
                elif not self.job_service.check_url_validity(job['job_url']):
                    new_status = 'Expired - Unreachable'
                    self.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' is unreachable. Marking as '{new_status}'.")
                
                # 3. If status changed, update the record
                if new_status != job['status']:
                    cur.execute(
                        "UPDATE jobs SET status = %s, last_checked_at = %s WHERE id = %s;",
                        (new_status, datetime.now(timezone.utc), job['id'])
                    )
                    updated_count += 1
                else: # Even if status is the same, update the check time
                    cur.execute(
                        "UPDATE jobs SET last_checked_at = %s WHERE id = %s;",
                        (datetime.now(timezone.utc), job['id'])
                    )

            db.commit()
            self.logger.info(f"Job expiration check complete. Checked: {len(jobs_to_check)}, Updated: {updated_count}")
            return {
                "jobs_checked": len(jobs_to_check),
                "jobs_status_updated": updated_count,
            }

    def check_and_expire_tracked_jobs(self):
        """
        Checks for tracked jobs that have been inactive for too long and marks them as expired.
        This is intended to be run as a scheduled task.
        Returns a summary of the operation.
        """
        db = get_db()
        with db.cursor() as cur:
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=config.TRACKED_JOB_STALE_DAYS)
            
            # Select active applications where there has been no update for 30 days
            cur.execute("""
                SELECT id, user_id
                FROM tracked_jobs
                WHERE status NOT IN ('Expired', 'Rejected', 'Offer Accepted', 'Withdrawn')
                  AND updated_at < %s
                LIMIT 1000;
            """, (thirty_days_ago,))
            
            jobs_to_expire = cur.fetchall()

            self.logger.info(f"Found {len(jobs_to_expire)} tracked jobs to mark as expired due to inactivity.")
            
            if not jobs_to_expire:
                return {"tracked_jobs_checked": 0, "tracked_jobs_marked_expired": 0}

            # Perform a bulk update for efficiency
            job_ids_to_expire = [job['id'] for job in jobs_to_expire]
            new_status = 'Expired'
            new_reason = f'Stale - No action in {config.TRACKED_JOB_STALE_DAYS} days'
            
            cur.execute("""
                UPDATE tracked_jobs
                SET status = %s, status_reason = %s, updated_at = %s
                WHERE id = ANY(%s);
            """, (new_status, new_reason, datetime.now(timezone.utc), job_ids_to_expire))
            
            expired_count = cur.rowcount
            db.commit()
            
            self.logger.info(f"Tracked job expiration check complete. Marked Expired: {expired_count}")
            return {
                "tracked_jobs_checked": len(jobs_to_expire),
                "tracked_jobs_marked_expired": expired_count
            }