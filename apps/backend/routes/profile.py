# Path: apps/backend/routes/profile.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..app import db
from ..models import UserProfile

profile_bp = Blueprint('profile', __name__)

@profile_bp.before_app_request
def before_request():
    if request.path.startswith('/api/profile'):
        current_app.logger.debug(f"Profile Blueprint: Request to {request.path}")

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    profile_service = ProfileService(current_app.logger)
    user_id = g.current_user.id
    
    try:
        profile_data = profile_service.get_profile(user_id)
        return jsonify(profile_data), 200
    except Exception as e:
        current_app.logger.error(f"Error getting profile for user {user_id}: {e}")
        return jsonify({"message": "Error fetching profile."}), 500

@profile_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    profile_service = ProfileService(current_app.logger)
    user_id = g.current_user.id
    data = request.json

    if not data:
        return jsonify({"message": "No data provided"}), 400

    try:
        # First, update the profile with the new data.
        updated_profile = profile_service.update_profile(user_id, data)
        
        # CORRECTED LOGIC: After any update, check if the profile is complete.
        # If it is, this is the trigger to re-analyze jobs. This now works for
        # both the initial profile completion and all subsequent updates.
        if profile_service.has_completed_required_profile_fields(user_id):
            
            # Action 1: Trigger re-analysis for the user.
            current_app.logger.info(f"Profile updated for onboarded user {user_id}. Triggering re-analysis.")
            from ..services.job_service import JobService # Import here to avoid circular dependencies
            JobService(current_app.logger).trigger_reanalysis_for_user(user_id)

            # Action 2: Ensure the `has_completed_onboarding` flag is set to True.
            # This is an idempotent check; it's safe to run even if the flag is already True.
            if not updated_profile.get('has_completed_onboarding', False):
                profile_orm = UserProfile.query.filter_by(user_id=user_id).first()
                if profile_orm:
                    profile_orm.has_completed_onboarding = True
                    db.session.commit()
                    updated_profile['has_completed_onboarding'] = True
                    current_app.logger.info(f"User {user_id}'s 'has_completed_onboarding' flag set to True.")

        return jsonify(updated_profile), 200
    except Exception as e:
        current_app.logger.error(f"Error updating profile for user {user_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({"message": "Error updating profile."}), 500