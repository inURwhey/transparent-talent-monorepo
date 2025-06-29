from flask import Blueprint, request, jsonify, g
from ..auth import token_required
from ..services.profile_service import ProfileService

# Create a Blueprint for profile routes
profile_bp = Blueprint('profile_bp', __name__)

# Note: We get the logger from the current app context
from flask import current_app

@profile_bp.route('/profile', methods=['GET'])
@token_required
def get_user_profile():
    """Handles GET requests to /api/profile."""
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
    """Handles PUT requests to /api/profile."""
    user_id = g.current_user['id']
    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400
    
    profile_service = ProfileService(current_app.logger)
    try:
        updated_profile = profile_service.update_profile(user_id, data)
        if updated_profile is None:
             return jsonify({"message": "No valid profile fields to update"}), 200
        return jsonify(updated_profile), 200
    except Exception as e:
        current_app.logger.error(f"Error in update_user_profile route: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500