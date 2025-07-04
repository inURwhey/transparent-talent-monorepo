# Path: apps/backend/routes/onboarding.py
from flask import Blueprint, request, jsonify, g, current_app
import json
import re
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..services.job_service import JobService
from ..app import db
from ..models import ResumeSubmission, UserProfile
from ..config import config
from datetime import datetime
import pytz

onboarding_bp = Blueprint('onboarding', __name__)

@onboarding_bp.route('/onboarding/parse-resume', methods=['POST'])
@token_required
def parse_resume():
    user_id = g.current_user.id
    resume_text = request.json.get('resume_text')

    if not resume_text:
        return jsonify({"message": "Resume text is required."}), 400
    
    if len(resume_text) > config.MAX_RESUME_TEXT_LENGTH:
        return jsonify({"message": f"Resume text exceeds maximum allowed length of {config.MAX_RESUME_TEXT_LENGTH} characters."}), 400

    profile_service = ProfileService(current_app.logger)
    job_service = JobService(current_app.logger)

    try:
        content_type_prompt = f"Is the following text a resume? Answer RESUME or OTHER.\n\n{resume_text[:1000]}"
        # Use the job service's AI call with the fast model
        classification_response = job_service._call_gemini_api(content_type_prompt, model_name="gemini-pro") # Using pro as flash is unavailable
        if not classification_response or "RESUME" not in classification_response.upper():
            return jsonify({"message": "The submitted text does not appear to be a resume."}), 400

        ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).update({"is_active": False})
        
        new_submission = ResumeSubmission(user_id=user_id, raw_text=resume_text, source='copy_paste')
        db.session.add(new_submission)

        ai_profile_prompt = f"""
        Extract structured information from the following resume text.
        Resume Text:
        ```{resume_text}```
        Output a JSON object with the following structure:
        - current_role (string, nullable)
        - desired_job_titles (string, comma-separated, nullable)
        - target_industries (string, comma-separated, nullable)
        - career_goals (string, nullable)
        - skills (string, comma-separated, nullable)
        - education (string, formatted text, nullable)
        - work_experience (string, formatted text, nullable)
        - personality_16_personalities (string, nullable)
        - preferred_work_style (enum: "ON_SITE", "REMOTE", "HYBRID", "NO_PREFERENCE", nullable)
        - preferred_company_size (enum: "SMALL_BUSINESS", "MEDIUM_BUSINESS", "LARGE_ENTERPRISE", "STARTUP", "NO_PREFERENCE", nullable)
        - location (string, nullable)
        """
        ai_response = job_service._call_gemini_api(ai_profile_prompt)
        
        parsed_data = job_service._parse_ai_response(ai_response) if ai_response else None

        if not parsed_data:
            current_app.logger.warning(f"AI enrichment failed for user {user_id}. Saving resume text only.")
        else:
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not profile:
                profile = UserProfile(user_id=user_id)
                db.session.add(profile)
            
            # Simplified 'enrich-if-empty' logic
            for field, value in parsed_data.items():
                if hasattr(profile, field) and getattr(profile, field) is None and value:
                    setattr(profile, field, value)

        db.session.commit()
        
        if profile_service.has_completed_required_profile_fields(user_id):
            profile = UserProfile.query.filter_by(user_id=user_id).first()
            if not profile.has_completed_onboarding:
                profile.has_completed_onboarding = True
                db.session.commit()
                job_service.trigger_reanalysis_for_user(user_id)

        latest_profile_data = profile_service.get_profile(user_id)
        return jsonify({"message": "Resume processed successfully.", "profile": latest_profile_data}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error processing resume for user {user_id}: {e}", exc_info=True)
        return jsonify({"message": "An unexpected error occurred during resume processing."}), 500

@onboarding_bp.route('/onboarding/check-profile-status', methods=['GET'])
@token_required
def check_profile_status():
    user_id = g.current_user.id
    profile_service = ProfileService(current_app.logger)
    is_complete = profile_service.has_completed_required_profile_fields(user_id)
    return jsonify({"has_completed_onboarding": is_complete}), 200