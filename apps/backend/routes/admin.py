from flask import Blueprint, jsonify, current_app
from ..auth import token_required
from ..services.admin_service import AdminService

admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/admin/jobs/check-url-validity', methods=['POST'])
@token_required
def check_job_urls():
    """
    Checks the validity and age of job URLs and updates their status.
    Intended to be called by a scheduled task.
    """
    admin_service = AdminService(current_app.logger)
    try:
        result = admin_service.check_and_expire_job_postings()
        return jsonify({
            "message": "Job URL validity and age check completed.",
            **result
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error during job URL validity and age check: {e}")
        return jsonify({"message": "Internal server error during URL check.", "error": str(e)}), 500


@admin_bp.route('/admin/tracked-jobs/check-expiration', methods=['POST'])
@token_required
def check_tracked_job_expiration():
    """
    Checks tracked jobs for staleness and marks them expired.
    Intended to be called by a scheduled task.
    """
    admin_service = AdminService(current_app.logger)
    try:
        result = admin_service.check_and_expire_tracked_jobs()
        return jsonify({
            "message": "Tracked job expiration check completed.",
            **result
        }), 200
    except Exception as e:
        current_app.logger.error(f"Error during tracked job expiration check: {e}")
        return jsonify({"message": "Internal server error during tracked job expiration check.", "error": str(e)}), 500