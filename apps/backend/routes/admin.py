# Path: apps/backend/routes/admin.py
from flask import Blueprint, jsonify, current_app
from ..auth import token_required, admin_required
from ..services.admin_service import AdminService
from ..services.company_service import CompanyService

# Prefix will be defined in app.py during registration
admin_bp = Blueprint('admin_bp', __name__)

@admin_bp.route('/admin/jobs/check-url-validity', methods=['POST'])
@token_required
def check_job_urls():
    # This existing function is unchanged.
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
    # This existing function is unchanged.
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

# --- NEW ROUTE ---
@admin_bp.route('/admin/research-company/<int:company_id>', methods=['POST'])
@token_required
@admin_required
def research_company(company_id):
    """
    Triggers AI research for a specific company and stores the profile.
    Requires admin privileges.
    """
    try:
        company_service = CompanyService()
        result = company_service.research_and_update_company_profile(company_id)
        
        return jsonify({
            "success": result["success"],
            "message": result["message"]
        }), result["status_code"]

    except ValueError as e:
        # Catches the case where GEMINI_API_KEY is not set
        current_app.logger.error(f"Configuration error in admin endpoint: {e}")
        return jsonify({"success": False, "message": str(e)}), 503 # Service Unavailable
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred in research_company endpoint: {e}")
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500