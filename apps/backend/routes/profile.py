# Path: apps/backend/routes/profile.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService

# Prefix will be defined in app.py during registration
profile_bp = Blueprint('profile_bp', __name__)

ONBOARDING_REQUIRED_FIELDS = [
    'work_style_preference',
    'conflict_resolution_style',
    'communication_preference',
    'change_tolerance'
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
    
    current_profile = profile_service.get_profile(user_id)
    if not current_profile.get('has_completed_onboarding'):
        merged_profile = {**current_profile, **data}
        is_complete = all(merged_profile.get(field) for field in ONBOARDING_REQUIRED_FIELDS)
        if is_complete:
            data['has_completed_onboarding'] = True
            current_app.logger.info(f"User {user_id} has completed onboarding.")

    try:
        updated_profile = profile_service.update_profile(user_id, data)
        if updated_profile is None:
             return jsonify({"message": "No valid profile fields to update"}), 200
        return jsonify(updated_profile), 200
    except Exception as e:
        current_app.logger.error(f"Error in update_user_profile route: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500