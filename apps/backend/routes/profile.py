# Path: apps/backend/routes/profile.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..database import get_db

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
    db = get_db()
    
    try:
        current_profile = profile_service.get_profile(user_id)
        onboarding_was_just_completed = False

        if not current_profile.get('has_completed_onboarding'):
            merged_profile = {**current_profile, **data}
            
            # Check for required profile fields
            profile_fields_complete = all(merged_profile.get(field) for field in ONBOARDING_REQUIRED_FIELDS)
            
            # Check for an active resume
            with db.cursor() as cursor:
                cursor.execute("SELECT EXISTS (SELECT 1 FROM resume_submissions WHERE user_id = %s AND is_active = TRUE)", (user_id,))
                has_active_resume = cursor.fetchone()[0]

            if profile_fields_complete and has_active_resume:
                data['has_completed_onboarding'] = True
                onboarding_was_just_completed = True
                current_app.logger.info(f"User {user_id} has completed onboarding with this update (profile + resume).")

        updated_profile = profile_service.update_profile(user_id, data)
        
        if onboarding_was_just_completed:
            current_app.logger.info(f"Triggering job re-analysis for user {user_id} post-onboarding.")
            profile_service.trigger_reanalysis_for_user(user_id)

        if updated_profile is None:
             return jsonify({"message": "No valid profile fields to update"}), 200
        return jsonify(updated_profile), 200
    except Exception as e:
        current_app.logger.error(f"Error in update_user_profile route for user_id {user_id}: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500