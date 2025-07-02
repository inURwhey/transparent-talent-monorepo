# Path: apps/backend/services/profile_service.py

from psycopg2.extras import DictCursor, Json
from ..database import get_db
from decimal import Decimal
# The circular import is removed from here.
# from ..services.job_service import JobService
from ..config import config

class ProfileService:
    def __init__(self, logger):
        self.logger = logger
        self.allowed_fields = [
            "full_name", "current_location", "linkedin_profile_url", "resume_url",
            "short_term_career_goal", "long_term_career_goals", 
            "desired_salary_min", "desired_salary_max",
            "desired_title", "ideal_role_description", "preferred_company_size",
            "ideal_work_culture", "disliked_work_culture", "core_strengths",
            "skills_to_avoid", "non_negotiable_requirements", "deal_breakers",
            "preferred_industries", "industries_to_avoid", "personality_adjectives",
            "personality_16_personalities", "personality_disc", "personality_gallup_strengths",
            "preferred_work_style", "is_remote_preferred", "latitude", "longitude",
            "has_completed_onboarding", "work_style_preference",
            "conflict_resolution_style", "communication_preference", "change_tolerance"
        ]

    def get_profile(self, user_id: int):
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            profile = cursor.fetchone()

            if not profile:
                self.logger.info(f"No profile for user_id {user_id}. Creating default.")
                cursor.execute("INSERT INTO user_profiles (user_id) VALUES (%s) RETURNING *;", (user_id,))
                profile = cursor.fetchone()
                db.commit()

            return self._format_profile(profile, cursor.description)

    def get_profile_for_analysis(self, user_id: int):
        profile = self.get_profile(user_id)
        analysis_columns = [
            "short_term_career_goal", "ideal_role_description", "core_strengths",
            "skills_to_avoid", "preferred_industries", "industries_to_avoid",
            "desired_title", "non_negotiable_requirements", "deal_breakers",
            "preferred_work_style", "is_remote_preferred",
            "desired_salary_min", "desired_salary_max"
        ]
        profile_labels = {
            "short_term_career_goal": "Short-Term Career Goal", "ideal_role_description": "Ideal Role",
            "core_strengths": "Core Strengths", "skills_to_avoid": "Skills To Avoid",
            "preferred_industries": "Preferred Industries", "industries_to_avoid": "Industries To Avoid",
            "desired_title": "Desired Title", "non_negotiable_requirements": "Non-Negotiables",
            "deal_breakers": "Deal Breakers", "preferred_work_style": "Preferred Work Style",
            "is_remote_preferred": "Remote Preference",
            "desired_salary_min": "Desired Minimum Salary",
            "desired_salary_max": "Desired Maximum Salary"
        }
        profile_parts = []
        for col in analysis_columns:
            value = profile.get(col)
            if col == 'is_remote_preferred':
                if value: profile_parts.append(f"- {profile_labels[col]}: Yes, remote is preferred.")
                else: profile_parts.append(f"- {profile_labels[col]}: No, remote is not preferred.")
            elif col in ['desired_salary_min', 'desired_salary_max']:
                if value is not None:
                    profile_parts.append(f"- {profile_labels[col]}: {int(value)}")
            elif value and str(value).strip():
                profile_parts.append(f"- {profile_labels[col]}: {value}")
        if len(profile_parts) <= 1:
             raise ValueError("User profile is too sparse. Please fill out your profile to enable analysis.")
        return "\n".join(profile_parts)

    def update_profile(self, user_id: int, data: dict):
        fields_to_update = []
        params = []
        for field, value in data.items():
            if field in self.allowed_fields:
                fields_to_update.append(f"{field} = %s")
                if field in ['is_remote_preferred', 'has_completed_onboarding']:
                    params.append(bool(value))
                elif field in ['desired_salary_min', 'desired_salary_max']:
                    params.append(int(value) if value is not None else None)
                else:
                    params.append(value if value else None)
        if not fields_to_update:
            self.logger.warning("Update profile called with no valid fields.")
            return None
        db = get_db()
        with db.cursor() as cursor:
            sql = f"UPDATE user_profiles SET {', '.join(fields_to_update)} WHERE user_id = %s RETURNING *;"
            params.append(user_id)
            cursor.execute(sql, tuple(params))
            updated_profile = cursor.fetchone()
            db.commit()
            return self._format_profile(updated_profile, cursor.description)

    def create_or_update_active_resume_submission(self, user_id: int, raw_text: str, source: str):
        db = get_db()
        try:
            with db.cursor() as cursor:
                self.logger.info(f"Deactivating old resumes for user_id: {user_id}")
                cursor.execute("UPDATE resume_submissions SET is_active = FALSE WHERE user_id = %s;",(user_id,))
                self.logger.info(f"Inserting new active resume for user_id: {user_id}, source: {source}")
                cursor.execute(
                    "INSERT INTO resume_submissions (user_id, raw_text, source, is_active) VALUES (%s, %s, %s, TRUE) RETURNING id;",
                    (user_id, raw_text, source)
                )
                new_resume_id = cursor.fetchone()[0]
                db.commit()
                self.logger.info(f"Successfully saved new resume submission with id: {new_resume_id} for user_id: {user_id}")
                return new_resume_id
        except Exception as e:
            db.rollback()
            self.logger.error(f"Failed to save resume submission for user_id {user_id}: {e}")
            raise

    def trigger_reanalysis_for_user(self, user_id: int):
        # Import JobService here, inside the method, to break the circular dependency.
        from ..services.job_service import JobService
        
        self.logger.info(f"Checking for jobs to re-analyze for user_id: {user_id}")
        db = get_db()
        job_service = JobService(self.logger)
        
        try:
            with db.cursor() as cursor:
                cursor.execute("""
                    SELECT t.job_id
                    FROM tracked_jobs t
                    LEFT JOIN job_analyses a ON t.job_id = a.job_id AND a.user_id = t.user_id
                    WHERE t.user_id = %s AND a.job_id IS NULL;
                """, (user_id,))
                
                jobs_to_analyze = cursor.fetchall()
                self.logger.info(f"Found {len(jobs_to_analyze)} jobs to re-analyze for user {user_id}.")

                if not jobs_to_analyze:
                    return {"message": "No jobs needed re-analysis."}

                user_profile_text = self.get_profile_for_analysis(user_id)

                for job_row in jobs_to_analyze:
                    job_id = job_row['job_id']
                    try:
                        self.logger.info(f"Re-analyzing job_id {job_id} for user_id {user_id}")
                        job_data = job_service.analyze_existing_job(job_id, user_profile_text)
                        analysis_result = job_data['analysis']

                        cursor.execute("""
                            INSERT INTO job_analyses (job_id, user_id, analysis_protocol_version, position_relevance_score, environment_fit_score, hiring_manager_view, matrix_rating, summary, qualification_gaps, recommended_testimonials)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (job_id, user_id) DO NOTHING;
                        """, (
                            job_id, user_id, config.ANALYSIS_PROTOCOL_VERSION,
                            analysis_result.get('position_relevance_score'), analysis_result.get('environment_fit_score'),
                            analysis_result.get('hiring_manager_view'), analysis_result.get('matrix_rating'),
                            analysis_result.get('summary'), Json(analysis_result.get('qualification_gaps', [])),
                            Json(analysis_result.get('recommended_testimonials', []))
                        ))
                    except Exception as e:
                        self.logger.error(f"Failed to re-analyze job_id {job_id} for user {user_id}: {e}")
                        continue
                
                db.commit()
                self.logger.info(f"Completed re-analysis for user {user_id}.")
                return {"message": f"Successfully re-analyzed {len(jobs_to_analyze)} jobs."}
        
        except Exception as e:
            db.rollback()
            self.logger.error(f"A critical error occurred during trigger_reanalysis_for_user for user_id {user_id}: {e}")
            raise

    def _format_profile(self, profile_row: DictCursor, description) -> dict:
        if not profile_row: return {}
        profile_dict = {}
        string_fields = [
            'full_name', 'current_location', 'linkedin_profile_url', 'resume_url',
            'short_term_career_goal', 'long_term_career_goals', 
            'desired_title', 'ideal_role_description', 'preferred_company_size',
            'ideal_work_culture', 'disliked_work_culture', 'core_strengths', 'skills_to_avoid',
            'preferred_industries', 'industries_to_avoid', 'personality_adjectives',
            'personality_16_personalities', 'personality_disc', 'personality_gallup_strengths',
            'preferred_work_style', 'non_negotiable_requirements', 'deal_breakers',
            'work_style_preference', 'conflict_resolution_style', 'communication_preference', 'change_tolerance'
        ]
        for col in description:
            col_name = col.name
            value = profile_row[col_name]
            if isinstance(value, Decimal):
                profile_dict[col_name] = float(value)
            elif col_name in ['desired_salary_min', 'desired_salary_max']: # No latitude/longitude here
                 profile_dict[col_name] = int(value) if value is not None else None
            elif col_name in string_fields and value is None:
                profile_dict[col_name] = ""
            elif col_name in ['is_remote_preferred', 'has_completed_onboarding'] and value is None:
                profile_dict[col_name] = False
            else:
                profile_dict[col_name] = value
        return profile_dict