# Path: apps/backend/routes/profile.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from psycopg2 import errors # Import the errors module

profile_bp = Blueprint('profile_bp', __name__)

ONBOARDING_REQUIRED_FIELDS = [
    'work_style_preference',
    'conflict_resolution_style',
    'communication_preference',
    'change_tolerance',
    'short_term_career_goal',
    'desired_title'
]

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_user_profile():
    user_id = g.current_user['id']
    profile_service = ProfileService(current_app.logger)
    try:
        profile = profile_service.get_profile(user_id)
        return jsonify(profile), 200
    except Exception as e:
        current_app.logger.error(f"Error in get_user_profile route: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

@profile_bp.route('/profile', methods=['PUT'])
@token_required
def update_user_profile():
    user_id = g.current_user['id']
    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400

    profile_service = ProfileService(current_app.logger)

    try:
        updated_profile = profile_service.update_profile(user_id, data)

        # After every profile update, check if onboarding is now complete.
        profile_service.check_and_trigger_onboarding_completion(user_id, ONBOARDING_REQUIRED_FIELDS)

        if updated_profile is None:
             # This indicates no valid fields were provided for update, based on current ProfileService logic
             return jsonify({"message": "No valid profile fields to update"}), 200

        # Return the latest state of the profile after the update and potential re-analysis trigger.
        # The updated_profile already contains the mapped values for the frontend
        return jsonify(updated_profile), 200 # Directly return updated_profile as it's already formatted
    except errors.InvalidTextRepresentation as e:
        # Catch PostgreSQL specific error for invalid ENUM input
        current_app.logger.error(f"Invalid ENUM value provided for user {user_id}: {e}")
        return jsonify({"error": f"Invalid data for one or more fields. Detail: {e.pgerror}"}), 400
    except Exception as e:
        current_app.logger.error(f"Error in update_user_profile route for user_id {user_id}: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

# Placeholder for onboarding route for now, will be fleshed out in next steps
@profile_bp.route('/onboarding/parse-resume', methods=['POST'])
@token_required
def parse_resume():
    # Example usage of resume parsing logic
    # from ..services.onboarding_service import OnboardingService # Assuming this exists
    # onboarding_service = OnboardingService(current_app.logger)
    # raw_resume_text = request.json.get('resume_text', '')
    # user_id = g.current_user['id']
    # if not raw_resume_text:
    #     return jsonify({"error": "Resume text is required"}), 400
    # try:
    #     onboarding_service.parse_resume_and_update_profile(user_id, raw_resume_text)
    #     return jsonify({"message": "Resume parsed and profile updated successfully."}), 200
    # except Exception as e:
    #     current_app.logger.error(f"Error parsing resume: {e}")
    #     return jsonify({"error": "Failed to parse resume."}), 500
    return jsonify({"message": "Resume parsing endpoint placeholder."}), 200