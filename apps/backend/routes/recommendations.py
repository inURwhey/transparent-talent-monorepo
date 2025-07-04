# Path: apps/backend/routes/recommendations.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.job_matching_service import JobMatchingService
from ..app import db # Added for potential future session rollback if service does not handle it fully

reco_bp = Blueprint('recommendations', __name__)

@reco_bp.route('/jobs/recommendations', methods=['GET'])
@token_required
def get_job_recommendations():
    user_id = g.current_user.id
    limit = int(request.args.get('limit', 10))

    job_matching_service = JobMatchingService(current_app.logger)

    try:
        recommendations = job_matching_service.get_job_recommendations(user_id, limit)
        # Service handles commit/rollback
        return jsonify(recommendations), 200
    except Exception as e:
        current_app.logger.error(f"Error getting job recommendations for user {user_id}: {e}", exc_info=True)
        db.session.rollback() # Ensure rollback on route level if exception happens
        return jsonify({"message": "Error fetching recommendations."}), 500