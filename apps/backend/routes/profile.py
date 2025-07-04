# Path: apps/backend/routes/profile.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..app import db # NEW: Import db for commit after onboarding status change
from ..models import UserProfile # NEW: Import UserProfile for direct ORM access

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
        updated_profile = profile_service.update_profile(user_id, data)
        
        # Check for onboarding completion after profile update
        # This logic ensures `has_completed_onboarding` is set to True
        # and re-analysis is triggered. It explicitly commits via db.session.commit()
        # because the profile_service.update_profile might have already committed
        # and we need to ensure this follow-up update is also persisted.
        if not updated_profile.get('has_completed_onboarding', False):
            if profile_service.has_completed_required_profile_fields(user_id):
                profile_orm = UserProfile.query.filter_by(user_id=user_id).first()
                if profile_orm:
                    profile_orm.has_completed_onboarding = True
                    db.session.commit() # Commit this specific change
                    # Ensure the returned dict reflects this change
                    updated_profile['has_completed_onboarding'] = True
                    current_app.logger.info(f"User {user_id} has completed onboarding.")
                    # Trigger re-analysis for tracked jobs (can be async)
                    from ..services.job_service import JobService # Import here to avoid circular
                    JobService(current_app.logger).trigger_reanalysis_for_user(user_id)
                else:
                    current_app.logger.warning(f"Profile for user {user_id} unexpectedly missing during onboarding status check.")


        return jsonify(updated_profile), 200
    except Exception as e:
        current_app.logger.error(f"Error updating profile for user {user_id}: {e}", exc_info=True)
        # Ensure rollback if any error occurs in this route's logic after service call
        db.session.rollback()
        return jsonify({"message": "Error updating profile."}), 500