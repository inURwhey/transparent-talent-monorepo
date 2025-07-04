# Path: apps/backend/routes/companies.py
from flask import Blueprint, jsonify, current_app
from ..auth import token_required
from ..services.company_service import CompanyService # NEW: Import CompanyService
from ..models import Company # NEW: Import Company model

companies_bp = Blueprint('companies', __name__)

@companies_bp.route('/companies/<int:company_id>/profile', methods=['GET'])
@token_required
def get_company_profile(company_id):
    """
    Retrieves a company's profile.
    """
    company_service = CompanyService(current_app.logger)
    
    try:
        company_profile = company_service.get_company(company_id)
        if company_profile:
            return jsonify(company_profile.to_dict()), 200
        return jsonify({"message": "Company profile not found."}), 404
    except Exception as e:
        current_app.logger.error(f"Error fetching company profile for company_id {company_id}: {e}", exc_info=True)
        return jsonify({"message": "Error fetching company profile."}), 500