# Path: apps/backend/routes/profile.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService

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
             return jsonify({"message": "No valid profile fields to update"}), 200
        
        # Return the latest state of the profile after the update and potential re-analysis trigger.
        final_profile_state = profile_service.get_profile(user_id)
        return jsonify(final_profile_state), 200
    except Exception as e:
        current_app.logger.error(f"Error in update_user_profile route for user_id {user_id}: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500