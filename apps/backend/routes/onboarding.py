# Path: apps/backend/routes/onboarding.py

from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..services.job_service import JobService
from ..config import config
import google.generativeai as genai
import json
import re

onboarding_bp = Blueprint('onboarding_bp', __name__)

# Define allowed values for strict validation
ALLOWED_PREFERRED_WORK_STYLES = {"On-site", "Remote", "Hybrid"}
MAX_PERSONALITY_16_CHARS = 10 # Slightly more lenient than 6 to allow for common variations, but still strict.

@onboarding_bp.route('/onboarding/parse-resume', methods=['POST'])
@token_required
def parse_resume():
    """
    Receives raw resume text, parses it using an AI model, and populates
    the user's profile with the extracted data.
    Also saves the raw resume text to the resume_submissions table.
    """
    user_id = g.current_user['id']
    data = request.get_json()
    resume_text = data.get('resume_text')

    if not resume_text:
        return jsonify({"error": "Resume text is missing."}), 400

    # Resume text length validation
    if len(resume_text) < 100:
        return jsonify({"error": "Resume text is too short for meaningful analysis. Please provide more detail."}), 400
    if len(resume_text) > config.MAX_RESUME_TEXT_LENGTH:
        return jsonify({"error": f"Resume text too long ({len(resume_text)} characters). Please keep it under {config.MAX_RESUME_TEXT_LENGTH} characters."}), 400

    profile_service = ProfileService(current_app.logger)
    job_service = JobService(current_app.logger)
    
    try:
        current_app.logger.info(f"Starting resume parse for user_id: {user_id}")

        # AI Classification Check
        is_resume = job_service.is_resume_content(resume_text)
        if not is_resume:
            return jsonify({"error": "The provided text does not appear to be a resume. Please submit valid resume content."}), 400
        
        # Manually define specific schema requirements to constrain AI output for the prompt
        json_output_schema_dict = {
            "full_name": "string (or null)",
            "current_location": "string (City, State, e.g., \"San Francisco, CA\", or null)",
            "linkedin_profile_url": "string (URL or null)",
            "resume_url": "string (URL or null)",
            "short_term_career_goal": "string (concise summary of candidate's likely next step, or null)",
            "long_term_career_goals": "string (or null)",
            "desired_annual_compensation": "string (e.g., \"$150,000 - $180,000\", or null)",
            "desired_title": "string (or null)",
            "ideal_role_description": "string (or null)",
            "preferred_company_size": "string (e.g., \"Startup (1-50 employees)\", \"Enterprise (10000+ employees)\", or null)",
            "ideal_work_culture": "string (or null)",
            "disliked_work_culture": "string (or null)",
            "core_strengths": "string (comma-separated list of strengths, or null)",
            "skills_to_avoid": "string (comma-separated list of skills, or null)",
            "non_negotiable_requirements": "string (or null)",
            "deal_breakers": "string (or null)",
            "preferred_industries": "string (comma-separated list of industries, or null)",
            "industries_to_avoid": "string (comma-separated list of industries, or null)",
            "personality_adjectives": "string (comma-separated list of adjectives, or null)",
            # --- IMPORTANT: Constrain AI output for personality_16_personalities (MAX 6 CHARS from prompt) ---
            "personality_16_personalities": "string (One of 16 Myers-Briggs types, optionally with -A or -T suffix, e.g., 'INTJ', 'ESTP-A', or null. KEEP CONCISE, MAX 6 CHARS)",
            "personality_disc": "string (e.g., 'D', 'I', 'S', 'C', 'Di', 'IS', 'SC', 'CD', or null)",
            "personality_gallup_strengths": "string (comma-separated list of top 5 strengths, or null)",
            # --- IMPORTANT: Constrain AI output for preferred_work_style ---
            "preferred_work_style": "string ('On-site', 'Remote', 'Hybrid', or null)",
            # Note: is_remote_preferred, latitude, longitude, has_completed_onboarding are handled separately or frontend-derived
            "work_style_preference": "string ('An ambiguous environment where I can create my own structure.' or 'A structured environment with clearly defined tasks.', or null)",
            "conflict_resolution_style": "string ('Have a direct, open debate to resolve the issue quickly.' or 'Build consensus with stakeholders before presenting a solution.', or null)",
            "communication_preference": "string ('Detailed written documentation (e.g., docs, wikis, Notion).' or 'Real-time synchronous meetings (e.g., Zoom, Slack huddles).', or null)",
            "change_tolerance": "string ('Priorities are stable and I can focus on a long-term roadmap.' or 'The team is nimble and priorities pivot often based on new data.', or null)"
        }
        json_schema_str = json.dumps(json_output_schema_dict, indent=2)

        prompt = f"""
            You are a meticulous HR data-entry specialist. Your task is to parse the following resume text and extract the information into a structured JSON object.
            
            - Infer and summarize where necessary. For example, 'short_term_career_goal' should be a concise summary of the candidate's likely next step based on their most recent role.
            - If a field is not present in the resume, the value should be `null`.
            - The `current_location` should be just the City, State (e.g., "San Francisco, CA").
            - Do not invent information.
            - STRICTLY adhere to the specified format and value constraints for each field as detailed in the JSON_OUTPUT_SCHEMA.

            RESUME TEXT:
            ---
            {resume_text}
            ---

            JSON_OUTPUT_SCHEMA:
            {json_schema_str}
        """

        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        cleaned_response = re.sub(r'```json\s*|\s*```', '', response.text.strip())
        parsed_data = json.loads(cleaned_response)

        # --- NEW: Post-parsing validation and discard ---
        if 'preferred_work_style' in parsed_data:
            if parsed_data['preferred_work_style'] not in ALLOWED_PREFERRED_WORK_STYLES and parsed_data['preferred_work_style'] is not None:
                current_app.logger.warning(f"Discarding invalid preferred_work_style '{parsed_data['preferred_work_style']}' from AI for user {user_id}. Setting to null.")
                parsed_data['preferred_work_style'] = None
        
        if 'personality_16_personalities' in parsed_data:
            p16_val = parsed_data['personality_16_personalities']
            if p16_val is not None and (not isinstance(p16_val, str) or len(p16_val) > MAX_PERSONALITY_16_CHARS or not re.fullmatch(r'^[A-Z]{4}(-[AT])?$', p16_val)):
                current_app.logger.warning(f"Discarding invalid personality_16_personalities '{p16_val}' from AI for user {user_id}. Setting to null.")
                parsed_data['personality_16_personalities'] = None
        # --- END NEW ---

        # Save raw resume text to resume_submissions table
        resume_submission_id = profile_service.create_or_update_active_resume_submission(
            user_id,
            resume_text,
            'onboarding_form' # Source of the resume submission
        )

        if not resume_submission_id:
            current_app.logger.error(f"Failed to record resume submission for user_id: {user_id}")
            return jsonify({"error": "Failed to record resume submission. Please try again."}), 500
        
        current_app.logger.info(f"Successfully parsed resume for user_id: {user_id}")

        # Use the existing update_profile service to save the data.
        # This automatically handles creating the profile if it's their very first action.
        updated_profile = profile_service.update_profile(user_id, parsed_data)

        if not updated_profile:
            raise Exception("Failed to save parsed profile data.")

        return jsonify(updated_profile), 200

    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON PARSE FAILED for user_id {user_id}. Raw AI response: {response.text}. Error: {e}")
        return jsonify({"error": "Failed to parse structured data from resume."}), 500
    except Exception as e:
        # Ensure response.text is available; if not a JSONDecodeError, it might not be.
        raw_ai_response = response.text if 'response' in locals() else 'N/A (AI response object not available or error not from AI)'
        current_app.logger.error(f"An unexpected error occurred in parse_resume for user_id {user_id}: {e}. Raw AI response: {raw_ai_response}")
        return jsonify({"error": "An internal server error occurred."}), 500