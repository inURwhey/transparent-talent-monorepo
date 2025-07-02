# Path: apps/backend/services/tracked_job_service.py
from ..database import get_db
from psycopg2.extras import RealDictCursor
import psycopg2

class TrackedJobService:
    def __init__(self, logger):
        self.logger = logger
        self.db_connection = get_db()

    def update_job(self, user_id, tracked_job_id, data):
        allowed_fields = [
            'status', 'is_excited', 'user_notes', 'status_reason',
            'applied_at', 'first_interview_at', 'offer_received_at',
            'resolved_at', 'next_action_at', 'next_action_notes'
        ]
        
        update_data = {k: v for k, v in data.items() if k in allowed_fields}

        if not update_data:
            raise ValueError("No valid fields provided for update.")

        set_clause = ", ".join([f"{field} = %s" for field in update_data.keys()])
        
        params = list(update_data.values())
        params.append(tracked_job_id)
        params.append(user_id)

        query = f"UPDATE tracked_jobs SET {set_clause}, updated_at = NOW() WHERE id = %s AND user_id = %s RETURNING id;"

        try:
            with self.db_connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, tuple(params))
                updated_row = cursor.fetchone()
                if updated_row:
                    self.db_connection.commit()
                    self.logger.info(f"Successfully updated tracked_job {tracked_job_id} for user {user_id}.")
                    return self._get_formatted_job_by_id(cursor, tracked_job_id, user_id)
                else:
                    self.logger.warning(f"Update failed: Tracked job {tracked_job_id} not found for user {user_id}.")
                    return None
        except psycopg2.Error as e:
            self.db_connection.rollback()
            self.logger.error(f"Database error during tracked job update: {e}")
            raise

    def _get_formatted_job_by_id(self, cursor, tracked_job_id, user_id):
        query = """
            SELECT
                t.id as tracked_job_id,
                t.status,
                t.is_excited,
                t.created_at,
                t.applied_at,
                t.first_interview_at,
                t.offer_received_at,
                t.resolved_at,
                t.next_action_at,
                t.next_action_notes,
                t.status_reason,
                j.id as job_id,
                j.company_id, -- Ensures company_id is fetched
                j.job_title,
                j.company_name,
                j.job_url,
                j.status as job_posting_status,
                j.last_checked_at,
                a.position_relevance_score,
                a.environment_fit_score,
                a.hiring_manager_view,
                a.matrix_rating,
                a.summary,
                a.qualification_gaps,
                a.recommended_testimonials
            FROM tracked_jobs t
            JOIN jobs j ON t.job_id = j.id
            LEFT JOIN job_analyses a ON t.job_id = a.job_id AND t.user_id = a.user_id
            WHERE t.id = %s AND t.user_id = %s;
        """
        cursor.execute(query, (tracked_job_id, user_id))
        job = cursor.fetchone()

        if not job:
            self.logger.warning(f"No tracked job found with ID {tracked_job_id} for user {user_id}")
            return None

        formatted_job = {
            "tracked_job_id": job['tracked_job_id'],
            "job_id": job['job_id'],
            "company_id": job['company_id'], # Ensures company_id is in the response
            "job_title": job['job_title'],
            "company_name": job['company_name'],
            "job_url": job['job_url'],
            "status": job['status'],
            "user_notes": None, # FIX: Removed non-existent column, returning None as placeholder
            "created_at": job['created_at'].isoformat() if job['created_at'] else None,
            "is_excited": job['is_excited'],
            "job_posting_status": job['job_posting_status'],
            "last_checked_at": job['last_checked_at'].isoformat() if job['last_checked_at'] else None,
            "status_reason": job['status_reason'],
            "applied_at": job['applied_at'].isoformat() if job['applied_at'] else None,
            "first_interview_at": job['first_interview_at'].isoformat() if job['first_interview_at'] else None,
            "offer_received_at": job['offer_received_at'].isoformat() if job['offer_received_at'] else None,
            "resolved_at": job['resolved_at'].isoformat() if job['resolved_at'] else None,
            "next_action_at": job['next_action_at'].isoformat() if job['next_action_at'] else None,
            "next_action_notes": job['next_action_notes'],
            "ai_analysis": None
        }

        if job['matrix_rating']:
            formatted_job['ai_analysis'] = {
                'position_relevance_score': job['position_relevance_score'],
                'environment_fit_score': job['environment_fit_score'],
                'hiring_manager_view': job['hiring_manager_view'],
                'matrix_rating': job['matrix_rating'],
                'summary': job['summary'],
                'qualification_gaps': job['qualification_gaps'],
                'recommended_testimonials': job['recommended_testimonials']
            }
        
        return formatted_job

    def _get_active_pipeline_statuses_tuple(self):
        return ('SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS')