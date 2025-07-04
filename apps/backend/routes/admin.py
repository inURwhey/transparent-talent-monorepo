# Path: apps/backend/routes/admin.py
from flask import Blueprint, jsonify, current_app, request
from ..auth import token_required, admin_required
from ..app import db
from ..models import User, Company, Job, JobOpportunity, TrackedJob, JobAnalysis
from ..services.job_service import JobService
from ..services.company_service import CompanyService
import requests
from ..config import config

admin_bp = Blueprint('admin', __name__)

# NEW: Temporary debugging route to list available Gemini models
@admin_bp.route('/admin/list-models', methods=['GET'])
@admin_required
def list_models():
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return jsonify({"error": "Gemini API key is not configured."}), 500

    # Using the v1beta endpoint as that's what the code currently uses.
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Error calling ListModels: {e}")
        if e.response is not None:
            return jsonify({
                "error": "Failed to list models",
                "status_code": e.response.status_code,
                "response": e.response.text
            }), 500
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/admin/db-reset', methods=['POST'])
@token_required
@admin_required
def db_reset():
    data = request.json
    tables_to_reset = data.get('tables', [])

    if not tables_to_reset:
        return jsonify({"message": "No tables specified for reset."}), 400

    reset_messages = []
    
    table_model_map = {
        'users': User, 'companies': Company, 'jobs': Job,
        'job_opportunities': JobOpportunity, 'tracked_jobs': TrackedJob, 'job_analyses': JobAnalysis,
    }

    try:
        for table_name in tables_to_reset:
            model = table_model_map.get(table_name)
            if model:
                num_deleted = db.session.query(model).delete()
                db.session.execute(db.text(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1;"))
                reset_messages.append(f"Table '{table_name}' reset. Deleted {num_deleted} rows.")
            else:
                reset_messages.append(f"Table '{table_name}' not found.")
        
        db.session.commit()
        return jsonify({"message": "Database reset operation completed.", "details": reset_messages}), 200

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error during database reset: {e}", exc_info=True)
        return jsonify({"message": "Failed to reset database.", "error": str(e)}), 500

@admin_bp.route('/admin/reprocess-malformed-job-data', methods=['POST'])
@token_required
@admin_required
def reprocess_malformed_job_data():
    job_service = JobService(current_app.logger)
    reprocessed_count = 0
    failed_count = 0

    jobs_to_reprocess = Job.query.filter(
        db.or_(
            Job.job_title.ilike('%job not found at url%'),
            Job.job_description_hash == None,
            Job.salary_min == None
        )
    ).limit(100).all()

    for job in jobs_to_reprocess:
        opportunity = db.session.query(JobOpportunity).filter_by(job_id=job.id).first()
        if not opportunity:
            failed_count += 1
            continue

        try:
            re_processed_canonical_job, _ = job_service.create_or_get_canonical_job(
                url=opportunity.url, user_id=None, commit=True
            )
            if re_processed_canonical_job:
                reprocessed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            db.session.rollback()
            current_app.logger.error(f"Error re-processing job ID: {job.id}: {e}", exc_info=True)

    return jsonify({
        "message": "Job data re-processing initiated.",
        "reprocessed_count": reprocessed_count,
        "failed_count": failed_count,
    }), 200

@admin_bp.route('/admin/reprocess-incomplete-company-profiles', methods=['POST'])
@token_required
@admin_required
def reprocess_incomplete_company_profiles():
    company_service = CompanyService(current_app.logger)
    reprocessed_count = 0
    failed_count = 0

    companies_to_reprocess = Company.query.filter(
        db.or_(
            Company.industry == None,
            Company.description == None,
            Company.mission == None
        )
    ).limit(50).all()

    for company in companies_to_reprocess:
        try:
            updated_company = company_service.research_and_update_company_profile(company.id)
            if updated_company:
                reprocessed_count += 1
            else:
                failed_count += 1
        except Exception as e:
            failed_count += 1
            db.session.rollback()
            current_app.logger.error(f"Error re-processing company ID: {company.id}: {e}", exc_info=True)

    return jsonify({
        "message": "Company profile re-processing initiated.",
        "reprocessed_count": reprocessed_count,
        "failed_count": failed_count,
    }), 200