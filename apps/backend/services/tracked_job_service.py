# Path: apps/backend/services/tracked_job_service.py

from ..database import get_db

class TrackedJobService:
    def __init__(self, logger):
        """
        Initializes the TrackedJob Service.
        Args:
            logger: The Flask app's logger instance for logging messages.
        """
        self.logger = logger
        self.allowed_fields = [
            'status', 'notes', 'is_excited', 'status_reason', 
            'applied_at', 'first_interview_at', 'offer_received_at', 
            'resolved_at', 'next_action_at', 'next_action_notes'
        ]

    def update_job(self, user_id: int, tracked_job_id: int, payload: dict):
        """
        Updates a tracked job for a specific user.
        """
        fields_to_update = {k: v for k, v in payload.items() if k in self.allowed_fields}
        
        if not fields_to_update:
            self.logger.warning("Update called with no valid fields for tracked_job_id %s", tracked_job_id)
            raise ValueError("No valid fields to update.")

        set_clauses = [f"{field} = %s" for field in fields_to_update.keys()]
        params = list(fields_to_update.values())
        params.append(tracked_job_id)
        params.append(user_id)
        
        db = get_db()
        with db.cursor() as cursor:
            update_sql = f"UPDATE tracked_jobs SET {', '.join(set_clauses)} WHERE id = %s AND user_id = %s RETURNING id;"
            
            cursor.execute(update_sql, tuple(params))
            updated_row = cursor.fetchone()
            
            if not updated_row:
                self.logger.warning("Update tracked_job_id %s for user_id %s failed (not found or no permission).", tracked_job_id, user_id)
                return None
            
            db.commit()
            self.logger.info("Successfully updated tracked_job_id %s for user_id %s.", tracked_job_id, user_id)
            
            return self._get_formatted_job_by_id(cursor, updated_row['id'], user_id)

    def _get_formatted_job_by_id(self, cursor, tracked_job_id: int, user_id: int):
        """
        Private helper to fetch and format a single tracked job.
        """
        cursor.execute("""
            SELECT 
                j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                j.status as job_posting_status, j.last_checked_at,
                t.id as tracked_job_id, t.status, t.notes, t.applied_at, t.created_at, t.is_excited, t.status_reason,
                t.first_interview_at, t.offer_received_at, t.resolved_at, t.next_action_at, t.next_action_notes,
                ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
            FROM jobs j
            JOIN tracked_jobs t ON j.id = t.job_id
            LEFT JOIN job_analyses ja ON j.id = ja.job_id AND t.user_id = ja.user_id
            WHERE t.id = %s AND t.user_id = %s;
        """, (tracked_job_id, user_id))
        
        row = cursor.fetchone()
        return self._format_job_row(row) if row else None

    def _format_job_row(self, row) -> dict:
        """
        Private helper to format a database row into the standard JSON structure.
        """
        if not row: return None
        
        job = {
            "tracked_job_id": row["tracked_job_id"], "job_id": row["job_id"],
            "job_title": row["job_title"], "company_name": row["company_name"],
            "job_url": row["job_url"], "status": row["status"],
            "user_notes": row["notes"], "created_at": row["created_at"],
            "is_excited": row["is_excited"], "job_posting_status": row["job_posting_status"],
            "last_checked_at": row["last_checked_at"], "status_reason": row["status_reason"],
            "applied_at": row["applied_at"], "first_interview_at": row["first_interview_at"],
            "offer_received_at": row["offer_received_at"], "resolved_at": row["resolved_at"],
            "next_action_at": row["next_action_at"], "next_action_notes": row["next_action_notes"],
            "ai_analysis": None
        }
        if row["position_relevance_score"] is not None:
            job["ai_analysis"] = {
                "position_relevance_score": row["position_relevance_score"],
                "environment_fit_score": row["environment_fit_score"],
                "hiring_manager_view": row["hiring_manager_view"],
                "matrix_rating": row["matrix_rating"],
                "summary": row["ai_summary"],
                "qualification_gaps": row["qualification_gaps"],
                "recommended_testimonials": row["recommended_testimonials"]
            }
        return job