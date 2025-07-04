# Path: apps/backend/services/job_matching_service.py
import re
from flask import current_app
from sqlalchemy.orm import joinedload
from ..app import db
from ..models import JobAnalysis, UserProfile, Job, Company # Import necessary models

class JobMatchingService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger

    def calculate_match_score(self, job_analysis: JobAnalysis, user_profile: UserProfile):
        """
        Calculates a comprehensive match score for a job based on AI analysis
        and structured user preferences.
        """
        if not job_analysis or not user_profile:
            return 0, "Missing analysis or profile data."

        score = 0
        reasons = []

        # Base score from AI analysis
        position_relevance = job_analysis.position_relevance_score or 0
        environment_fit = job_analysis.environment_fit_score or 0
        
        # Simple weighted sum for now
        score += position_relevance * 0.6
        score += environment_fit * 0.4
        reasons.append(f"Base AI Relevance (Position: {position_relevance}, Environment: {environment_fit})")

        # --- Apply bonuses/penalties based on structured data ---

        # Work Modality Preference
        if user_profile.preferred_work_style and job_analysis.job.job_modality:
            if user_profile.preferred_work_style.value == job_analysis.job.job_modality.value:
                score += 10
                reasons.append(f"Bonus: Preferred work style ({user_profile.preferred_work_style.value}) matches job.")
            elif user_profile.preferred_work_style.value == 'HYBRID' and job_analysis.job.job_modality.value in ['ON_SITE', 'REMOTE']:
                score += 5 # Hybrid users might tolerate either
                reasons.append(f"Small Bonus: Hybrid preference matches On-site/Remote job.")
            else:
                score -= 5 # Minor penalty for mismatch
                reasons.append(f"Penalty: Work style mismatch ({user_profile.preferred_work_style.value} vs {job_analysis.job.job_modality.value}).")

        # Salary Range Preference
        if user_profile.desired_salary_min and user_profile.desired_salary_max and job_analysis.job.salary_min and job_analysis.job.salary_max:
            if (job_analysis.job.salary_min >= user_profile.desired_salary_min and
                job_analysis.job.salary_max <= user_profile.desired_salary_max):
                score += 15
                reasons.append("Bonus: Job salary range perfectly within desired range.")
            elif (job_analysis.job.salary_min <= user_profile.desired_salary_max and
                  job_analysis.job.salary_max >= user_profile.desired_salary_min): # Overlap
                score += 5
                reasons.append("Small Bonus: Job salary range overlaps desired range.")
            else:
                score -= 10
                reasons.append("Penalty: Job salary range outside desired range.")

        # Company Size Preference
        if user_profile.preferred_company_size and job_analysis.job.company and job_analysis.job.company.company_size_min:
            user_pref = user_profile.preferred_company_size.value
            company_size_min = job_analysis.job.company.company_size_min
            company_size_max = job_analysis.job.company.company_size_max or company_size_min # Use min if max is null

            # This mapping needs to be precise based on your ENUM definitions and company size ranges
            if user_pref == 'STARTUP' and company_size_max and company_size_max <= 50:
                score += 10
                reasons.append("Bonus: Company is a Startup, matching preference.")
            elif user_pref == 'SMALL_BUSINESS' and company_size_min and company_size_max and 1 <= company_size_max <= 50:
                score += 10
                reasons.append("Bonus: Company is Small Business, matching preference.")
            elif user_pref == 'MEDIUM_BUSINESS' and company_size_min and company_size_max and 51 <= company_size_max <= 250:
                score += 10
                reasons.append("Bonus: Company is Medium Business, matching preference.")
            elif user_pref == 'LARGE_ENTERPRISE' and company_size_min and company_size_min >= 251:
                score += 10
                reasons.append("Bonus: Company is Large Enterprise, matching preference.")
            elif user_pref == 'NO_PREFERENCE':
                pass # No bonus/penalty
            else:
                score -= 5 # Minor penalty for mismatch
                reasons.append(f"Penalty: Company size mismatch ({user_pref} vs {company_size_min}-{company_size_max}).")


        # Leadership Tier Gap (if applicable - needs more sophisticated logic)
        # Assuming you have a way to deduce user's current level vs. desired job level
        # For example: if user_profile.current_level and job_analysis.job.deduced_job_level:
        #    if user is applying for a role significantly above/below their level
        #    score -= penalty / score += bonus

        # Ensure score is within 0-100 bounds
        final_score = max(0, min(100, int(score)))
        return final_score, reasons

    def get_job_recommendations(self, user_id: int, limit: int = 10):
        """
        Generates job recommendations for a user based on their profile and existing analyses.
        This will look for JobAnalysis records and then apply the match score logic.
        """
        self.logger.info(f"Generating recommendations for user_id: {user_id}")

        user_profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not user_profile or not user_profile.has_completed_onboarding:
            self.logger.warning(f"User {user_id} profile incomplete. Cannot generate recommendations.")
            return {"message": "Please complete your profile to receive recommendations.", "jobs": []}

        # Fetch all JobAnalysis records for this user, eager loading related Job and Company
        # We need to load Job, Company and JobOpportunity for each JobAnalysis
        analyses = db.session.query(JobAnalysis).options(
            joinedload(JobAnalysis.job).joinedload(Job.company),
            joinedload(JobAnalysis.job).joinedload(Job.opportunities)
        ).filter(JobAnalysis.user_id == user_id).all()

        recommended_jobs = []
        for analysis in analyses:
            score, reasons = self.calculate_match_score(analysis, user_profile)
            
            # Get one active opportunity URL if available for the frontend display
            display_url = None
            if analysis.job and analysis.job.opportunities:
                active_opportunities = [o for o in analysis.job.opportunities if o.is_active]
                if active_opportunities:
                    display_url = active_opportunities[0].url # Just pick the first active one

            recommended_jobs.append({
                "job_id": analysis.job_id,
                "job_title": analysis.job.job_title if analysis.job else "N/A",
                "company_id": analysis.job.company_id if analysis.job else None,
                "company_name": analysis.job.company.name if analysis.job and analysis.job.company else "N/A",
                "match_score": score,
                "ai_grade": analysis.matrix_rating,
                "reasons": reasons,
                "summary": analysis.summary,
                "job_url": display_url # Providing one URL for frontend
            })

        # Sort recommendations by match_score (descending)
        recommended_jobs.sort(key=lambda x: x['match_score'], reverse=True)

        return {"message": "Recommendations generated successfully.", "jobs": recommended_jobs[:limit]}