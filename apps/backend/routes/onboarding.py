# Path: apps/backend/routes/onboarding.py

from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..services.job_service import JobService # Import JobService for classification
from ..config import config
import google.generativeai as genai
import json
import re

onboarding_bp = Blueprint('onboarding_bp', __name__)

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
    job_service = JobService(current_app.logger) # Instantiate JobService for classification
    
    try:
        current_app.logger.info(f"Starting resume parse for user_id: {user_id}")

        # --- NEW: AI Classification Check ---
        is_resume = job_service.is_resume_content(resume_text)
        if not is_resume:
            return jsonify({"error": "The provided text does not appear to be a resume. Please submit valid resume content."}), 400
        # --- END NEW ---
        
        # Use the ProfileService's allowed_fields to construct the desired JSON schema for the prompt
        # This keeps our prompt dynamically in sync with our service layer.
        json_schema = {field: "string (or null)" for field in profile_service.allowed_fields if field not in ['is_remote_preferred', 'latitude', 'longitude', 'has_completed_onboarding']}
        json_schema_str = json.dumps(json_schema, indent=2)

        prompt = f"""
            You are a meticulous HR data-entry specialist. Your task is to parse the following resume text and extract the information into a structured JSON object.
            
            - Infer and summarize where necessary. For example, 'short_term_career_goal' should be a concise summary of the candidate's likely next step based on their most recent role.
            - If a field is not present in the resume, the value should be `null`.
            - The `current_location` should be just the City, State (e.g., "San Francisco, CA").
            - Do not invent information.
            
            Produce a JSON object with the exact keys defined in this schema. Do not include any introductory text, markdown formatting, or any keys not in the schema.

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
        current_app.logger.error(f"An unexpected error occurred in parse_resume for user_id {user_id}: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500