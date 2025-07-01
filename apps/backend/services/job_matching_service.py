# Path: apps/backend/services/job_matching_service.py

import re
from ..database import get_db

class JobMatchingService:
    def __init__(self, logger):
        self.logger = logger
        self.GRADE_TO_SCORE = {
            'A+': 100, 'A': 95, 'A-': 90,
            'B+': 88, 'B': 85, 'B-': 80,
            'C+': 75, 'C': 70, 'C-': 65,
            'D': 60, 'F': 50
        }
        self.JOB_LEVEL_TO_INT = {
            'Entry': 1, 'Mid': 2, 'Senior': 3, 'Staff': 4, 
            'Principal': 5, 'Manager': 6, 'Director': 7, 'VP': 8, 'C-Suite': 9
        }

    def _get_user_profile(self, cursor, user_id):
        cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
        return cursor.fetchone()

    def _get_relevant_jobs(self, cursor, user_id):
        query = """
            SELECT
                j.id, j.job_title, j.company_name, j.job_url,
                j.salary_min, j.salary_max, j.required_experience_years,
                j.job_modality, j.deduced_job_level,
                a.matrix_rating
            FROM jobs j
            JOIN job_analyses a ON j.id = a.job_id
            WHERE a.matrix_rating IS NOT NULL
            AND j.id NOT IN (SELECT job_id FROM tracked_jobs WHERE user_id = %s);
        """
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

    def _infer_user_leadership_tier(self, profile):
        if not profile or not profile['desired_title']:
            return 1 
        title = profile['desired_title'].lower()
        if 'c-suite' in title or 'chief' in title: return 9
        if 'vp' in title or 'vice president' in title: return 8
        if 'director' in title: return 7
        if 'manager' in title: return 6
        if 'principal' in title: return 5
        if 'staff' in title: return 4
        if 'senior' in title or 'sr.' in title: return 3
        if 'mid' in title or 'intermediate' in title: return 2
        return 1

    def get_recommendations(self, user_id: int, limit: int = 20):
        self.logger.info(f"Generating recommendations for user_id: {user_id}")
        db = get_db()
        try:
            with db.cursor() as cursor:
                user_profile = self._get_user_profile(cursor, user_id)
                if not user_profile or not user_profile['has_completed_onboarding']:
                    self.logger.warning(f"Profile for user_id {user_id} is incomplete or not found. No recommendations generated.")
                    return []

                all_jobs = self._get_relevant_jobs(cursor, user_id)
                self.logger.info(f"Found {len(all_jobs)} candidate jobs for scoring.")
                
                scored_jobs = []
                for job in all_jobs:
                    score = 0
                    score += self.GRADE_TO_SCORE.get(job['matrix_rating'], 60)
                    if job['job_modality'] and user_profile['preferred_work_style'] and job['job_modality'] == user_profile['preferred_work_style']:
                        score += 10
                    user_sal_min = user_profile.get('desired_salary_min')
                    user_sal_max = user_profile.get('desired_salary_max')
                    job_sal_min = job.get('salary_min')
                    job_sal_max = job.get('salary_max')
                    if user_sal_min and user_sal_max and job_sal_min and job_sal_max:
                        if max(user_sal_min, job_sal_min) <= min(user_sal_max, job_sal_max):
                            score += 8
                    user_tier = self._infer_user_leadership_tier(user_profile)
                    job_tier = self.JOB_LEVEL_TO_INT.get(job['deduced_job_level'])
                    if user_tier and job_tier:
                        tier_gap = job_tier - user_tier
                        if tier_gap == 1: score -= 1
                        elif tier_gap == 2: score -= 5
                        elif tier_gap >= 3: score -= 15
                    
                    job_dict = dict(job)
                    job_dict['match_score'] = score
                    scored_jobs.append(job_dict)

                ranked_jobs = sorted(scored_jobs, key=lambda x: x['match_score'], reverse=True)
                
                self.logger.info(f"Successfully scored and ranked {len(ranked_jobs)} jobs for user_id: {user_id}.")
                return ranked_jobs[:limit]

        except Exception as e:
            self.logger.error(f"Error generating recommendations for user_id {user_id}: {e}")
            return []