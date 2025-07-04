# Path: apps/backend/routes/onboarding.py
from flask import Blueprint, request, jsonify, g, current_app
import json
import re # For regex parsing AI responses
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..services.job_service import JobService # For AI analysis after resume parse
from ..app import db # NEW: Import db for session management
from ..models import ResumeSubmission, UserProfile # NEW: Import ResumeSubmission and UserProfile models
from ..config import config
from datetime import datetime # For timestamps
import pytz # For timezone-aware timestamps
from sqlalchemy.exc import IntegrityError # For specific error handling

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
    job_service = JobService(current_app.logger) # Using JobService for AI call

    try: # This outer try block catches all exceptions during the process
        # Step 1: Pre-validation of content type
        content_type_prompt = f"""
        Analyze the following text. Determine if it is a resume.
        Output "RESUME" if it is clearly a resume.
        Output "OTHER" if it is not a resume.
        Text:
        ```text
        {resume_text[:2000]} # Only send a snippet for classification
        ```
        """
        classification_response = job_service._call_gemini_api(content_type_prompt, model_name="gemini-flash") # Use Flash for speed
        if classification_response and "RESUME" not in classification_response.upper(): # Ensure case-insensitivity
            # No rollback needed here yet, as no DB writes have occurred
            return jsonify({"message": "The submitted text does not appear to be a resume."}), 400

        # Step 2: Invalidate existing active resumes for this user
        existing_active_resumes = ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).all()
        for resume in existing_active_resumes:
            resume.is_active = False
            db.session.add(resume) # Mark for update

        # Step 3: Save the new resume submission
        new_submission = ResumeSubmission(
            user_id=user_id,
            raw_text=resume_text,
            source='copy_paste', # Assuming copy_paste for now, will be 'file_upload' later
            is_active=True,
            submitted_at=datetime.now(pytz.utc) # Ensure this is set
        )
        db.session.add(new_submission)

        # Step 4: Call AI to parse resume and enrich user profile
        ai_profile_prompt = f"""
        Extract structured information from the following resume text to enrich a user profile.
        If a field cannot be determined, use null.
        Resume Text:
        ```text
        {resume_text}
        ```
        Output a JSON object with the following structure:
        - current_role (string, nullable)
        - desired_job_titles (string, comma-separated, nullable)
        - target_industries (string, comma-separated, nullable)
        - career_goals (string, nullable)
        - skills (string, comma-separated, nullable)
        - education (string, formatted text, nullable)
        - work_experience (string, formatted text, nullable)
        - personality_16_personalities (string, e.g., 'INTJ', 'ESTP', nullable) - based on implied traits
        - preferred_work_style (enum: "ON_SITE", "REMOTE", "HYBRID", "NO_PREFERENCE", nullable)
        - preferred_company_size (enum: "SMALL_BUSINESS", "MEDIUM_BUSINESS", "LARGE_ENTERPRISE", "STARTUP", "NO_PREFERENCE", nullable)
        - location (string, nullable)
        """
        current_app.logger.info(f"Sending resume for AI parsing for user {user_id}.")
        ai_response = job_service._call_gemini_api(ai_profile_prompt) # Using job_service's AI call method

        parsed_data = None
        if ai_response:
            try:
                # Extract JSON from potential markdown block
                match = re.search(r"```json\n(.+?)\n```", ai_response, re.DOTALL)
                json_string = match.group(1) if match else ai_response
                parsed_data = json.loads(json_string)
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Failed to decode AI response JSON for resume parsing: {e}. Raw response: {ai_response}")
                # Don't re-raise, let it proceed with parsed_data=None or partial data
            except Exception as e:
                current_app.logger.error(f"Error extracting/loading JSON from AI response: {e}. Raw response: {ai_response}", exc_info=True)
                # Don't re-raise, let it proceed with parsed_data=None or partial data

        if not parsed_data: # If AI response was empty or parsing failed
            current_app.logger.warning(f"AI response empty or unparseable for resume parsing for user {user_id}. Proceeding without AI enrichment of profile.")
            # We don't rollback here, as new_submission and invalidation of old resumes should still save.
            # The profile enrichment just won't happen.

        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            profile = UserProfile(user_id=user_id) # Should ideally exist after get_profile
            db.session.add(profile)
        
        # Apply 'enrich-if-empty' logic if parsed_data is available
        if parsed_data:
            # Helper to map and update if empty
            def update_field_if_empty(obj, field_name, value, enum_map=None):
                current_value = getattr(obj, field_name)
                # Check if current value is None, empty string, or explicit 'NO_PREFERENCE' enum
                is_current_value_empty = (current_value is None or
                                         (isinstance(current_value, str) and current_value.strip() == '') or
                                         (hasattr(current_value, 'value') and current_value.value == 'NO_PREFERENCE'))
                
                if is_current_value_empty and value is not None and value != '': # Only update if new value exists and current is empty
                    if enum_map: # It's an ENUM field
                        # Get the actual SQLAlchemy Enum class from the model's column type
                        enum_type = getattr(UserProfile, field_name).type
                        if enum_type and hasattr(enum_type, 'enum_class'):
                            try:
                                enum_member = enum_type.enum_class[value.upper().replace('-', '_')]
                                setattr(obj, field_name, enum_member)
                            except KeyError:
                                current_app.logger.warning(f"AI returned invalid ENUM value '{value}' for {field_name}. Skipping update for this field.")
                                # setattr(obj, field_name, None) # Optionally set to None if invalid AI value
                        else:
                            current_app.logger.warning(f"Could not find enum_class for field {field_name}. Skipping enum mapping.")
                    else: # Not an ENUM field
                        setattr(obj, field_name, value)
            
            update_field_if_empty(profile, 'current_role', parsed_data.get('current_role'))
            update_field_if_empty(profile, 'desired_job_titles', parsed_data.get('desired_job_titles'))
            update_field_if_empty(profile, 'target_industries', parsed_data.get('target_industries'))
            update_field_if_empty(profile, 'career_goals', parsed_data.get('career_goals'))
            update_field_if_empty(profile, 'skills', parsed_data.get('skills'))
            update_field_if_empty(profile, 'education', parsed_data.get('education'))
            update_field_if_empty(profile, 'work_experience', parsed_data.get('work_experience'))
            update_field_if_empty(profile, 'personality_16_personalities', parsed_data.get('personality_16_personalities'))
            update_field_if_empty(profile, 'preferred_work_style', parsed_data.get('preferred_work_style'), enum_map=profile_service.enum_fields.get('preferred_work_style'))
            update_field_if_empty(profile, 'preferred_company_size', parsed_data.get('preferred_company_size'), enum_map=profile_service.enum_fields.get('preferred_company_size'))
            update_field_if_empty(profile, 'location', parsed_data.get('location'))

        profile.updated_at = datetime.now(pytz.utc)

        # This commit now applies changes from Step 2, 3, and 4
        db.session.commit()
        current_app.logger.info(f"Resume parsed and profile updated for user {user_id}.")

        # Check if profile completion is now met
        if profile_service.has_completed_required_profile_fields(user_id):
            profile_orm = UserProfile.query.filter_by(user_id=user_id).first()
            if profile_orm and not profile_orm.has_completed_onboarding:
                profile_orm.has_completed_onboarding = True
                db.session.commit() # Separate commit for onboarding status
                current_app.logger.info(f"User {user_id} has completed onboarding after resume parsing.")
                # Trigger re-analysis for tracked jobs (can be async)
                job_service.trigger_reanalysis_for_user(user_id)

        # Re-fetch profile to send latest status including has_completed_onboarding
        latest_profile_data = profile_service.get_profile(user_id)
        return jsonify({"message": "Resume processed successfully.", "profile": latest_profile_data}), 200

    except Exception as e:
        db.session.rollback() # Rollback all changes if any error occurs in the process
        current_app.logger.error(f"Error processing resume for user {user_id}: {e}", exc_info=True)
        return jsonify({"message": "An unexpected error occurred during resume processing."}), 500

@onboarding_bp.route('/onboarding/check-profile-status', methods=['GET'])
@token_required
def check_profile_status():
    user_id = g.current_user.id
    profile_service = ProfileService(current_app.logger)
    
    try:
        is_complete = profile_service.has_completed_required_profile_fields(user_id)
        return jsonify({"has_completed_onboarding": is_complete}), 200
    except Exception as e:
        current_app.logger.error(f"Error checking profile status for user {user_id}: {e}")
        db.session.rollback() # Ensure rollback on route level if exception happens
        return jsonify({"message": "Error checking profile status."}), 500