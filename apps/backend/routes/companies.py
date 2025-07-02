# Path: apps/backend/routes/companies.py
from flask import Blueprint, jsonify
from ..auth import token_required
from ..database import get_db
import json

companies_bp = Blueprint('companies_bp', __name__)

@companies_bp.route('/companies/<int:company_id>/profile', methods=['GET'])
@token_required
def get_company_profile(company_id):
    """
    Fetches the AI-generated profile for a specific company.
    """
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("SELECT * FROM company_profiles WHERE company_id = %s", (company_id,))
        profile = cursor.fetchone()

        if profile:
            # The 'profile' object is a dict-like object. We can convert it to a real dict
            # and then serialize it with a default handler for datetime objects.
            profile_dict = dict(profile)
            return json.dumps(profile_dict, default=str), 200, {'Content-Type': 'application/json'}
        else:
            return jsonify({"error": "Company profile not found"}), 404