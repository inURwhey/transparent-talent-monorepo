# Path: apps/backend/routes/recommendations.py
from flask import Blueprint, jsonify, g, current_app
from ..auth import token_required
from ..services.job_matching_service import JobMatchingService

reco_bp = Blueprint('reco_bp', __name__, url_prefix='/api')

@reco_bp.route('/jobs/recommendations', methods=['GET'])
@token_required
def get_job_recommendations():
    # ... (rest of the function is unchanged)
    user_id = g.current_user['id']
    
    try:
        service = JobMatchingService(current_app.logger)
        recommendations = service.get_recommendations(user_id)
        
        return jsonify(recommendations), 200

    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred in get_job_recommendations for user_id {user_id}: {e}")
        return jsonify({"error": "An internal server error occurred while fetching recommendations."}), 500