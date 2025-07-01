# Path: apps/backend/routes/onboarding.py

from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
import google.generativeai as genai
import json
import re

# Prefix will be defined in app.py during registration
onboarding_bp = Blueprint('onboarding_bp', __name__)

@onboarding_bp.route('/onboarding/parse-resume', methods=['POST'])
@token_required
def parse_resume():
    # ... (rest of the function is unchanged)
    user_id = g.current_user['id']
    data = request.get_json()
    resume_text = data.get('resume_text')

    if not resume_text or len(resume_text) < 100:
        return jsonify({"error": "Resume text is too short or missing."}), 400

    profile_service = ProfileService(current_app.logger)
    
    try:
        current_app.logger.info(f"Starting resume parse for user_id: {user_id}")
        
        profile_service.create_or_update_active_resume_submission(user_id, resume_text, 'welcome-page-v1')
        
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

        current_app.logger.info(f"Successfully parsed resume for user_id: {user_id}")

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