# Path: apps/backend/routes/admin.py
from flask import Blueprint, jsonify, current_app, request
from ..auth import token_required, admin_required
from ..app import db # Import db for direct access in admin tools
from ..models import User, Company, Job, JobOpportunity, TrackedJob, JobAnalysis # Import models
from ..services.job_service import JobService
from ..services.company_service import CompanyService # NEW: Import CompanyService
from datetime import datetime, timedelta
import pytz
import re # for URL patterns

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/db-reset', methods=['POST'])
@token_required
@admin_required
def db_reset():
    """
    Resets selected tables in the database. DANGER ZONE.
    """
    data = request.json
    tables_to_reset = data.get('tables', [])

    if not tables_to_reset:
        return jsonify({"message": "No tables specified for reset."}), 400

    reset_messages = []
    
    # Map table names to SQLAlchemy models
    table_model_map = {
        'users': User,
        'companies': Company,
        'jobs': Job,
        'job_opportunities': JobOpportunity,
        'tracked_jobs': TrackedJob,
        'job_analyses': JobAnalysis,
        # Add other tables as needed
    }

    try:
        for table_name in tables_to_reset:
            model = table_model_map.get(table_name)
            if model:
                # Delete all records from the table
                num_deleted = db.session.query(model).delete()
                # Reset sequence for primary key (PostgreSQL specific)
                # Ensure correct sequence name, e.g., tablename_id_seq
                db.session.execute(db.text(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH 1;"))
                reset_messages.append(f"Table '{table_name}' reset. Deleted {num_deleted} rows. Sequence restarted.")
                current_app.logger.info(f"Admin reset: {table_name} - {num_deleted} rows deleted, sequence restarted.")
            else:
                reset_messages.append(f"Table '{table_name}' not found or not configured for reset.")
                current_app.logger.warning(f"Admin reset: Attempted to reset unconfigured table '{table_name}'.")
        
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
    """
    Admin endpoint to re-process historical job data that was saved with placeholder titles
    or needs re-analysis into the new canonical job structure.
    """
    # Assuming "malformed" means job_title contains "Job not found at URL" or similar.
    # This also targets jobs that might not have a proper job_description_hash or other new fields.
    current_app.logger.info("Admin: Starting re-processing of malformed job data.")
    
    job_service = JobService(current_app.logger)
    profile_service = ProfileService(current_app.logger)

    reprocessed_count = 0
    failed_count = 0

    # Find JobOpportunities that might have malformed canonical Jobs, or Jobs that need re-analysis
    # For initial cleanup, target old jobs that might not have been processed through the new flow
    # This should target the canonical Job, not the opportunity
    jobs_to_reprocess = Job.query.filter(
        db.or_(
            Job.job_title.ilike('%job not found at url%'), # Specific placeholder title
            Job.job_description_hash == None, # Jobs that haven't had a hash generated
            Job.salary_min == None # Jobs that might be missing structured data
        )
    ).limit(100).all() # Process in batches

    for job in jobs_to_reprocess:
        # For each canonical job, pick one associated opportunity to re-scrape
        # We need at least one opportunity linked to this canonical job to get its URL for re-scraping
        opportunity = db.session.query(JobOpportunity).filter_by(job_id=job.id).first()

        if not opportunity:
            current_app.logger.warning(f"Canonical Job {job.id} has no associated opportunities. Skipping re-processing.")
            failed_count += 1
            continue

        try:
            # Re-run the canonical job creation process which includes scrape and AI analysis
            # This will update the existing canonical job with new details and analysis
            # We pass the existing opportunity's URL to create_or_get_canonical_job
            re_processed_canonical_job, re_processed_opportunity = job_service.create_or_get_canonical_job(
                url=opportunity.url, user_id=None, # user_id is not directly relevant for canonical job creation here
                commit=True # Commit each processing for robustness
            )

            if re_processed_canonical_job and re_processed_opportunity:
                # If the job was re-processed, ensure all users tracking it get a re-analysis
                # This should ideally be handled by trigger_reanalysis_for_user where user_profile_data is present
                tracked_users_for_job = db.session.query(TrackedJob.user_id).filter_by(job_opportunity_id=re_processed_opportunity.id).distinct().all()
                for user_id_tuple in tracked_users_for_job:
                    user_id = user_id_tuple[0]
                    # Trigger re-analysis for each user who tracked this opportunity
                    job_service.trigger_reanalysis_for_user(user_id)
                
                reprocessed_count += 1
                current_app.logger.info(f"Successfully re-processed canonical job ID: {job.id} from URL: {opportunity.url}")
            else:
                failed_count += 1
                current_app.logger.error(f"Failed to re-process canonical job ID: {job.id} from URL: {opportunity.url}. create_or_get_canonical_job returned None.")
        except Exception as e:
            failed_count += 1
            db.session.rollback() # Rollback current transaction if error occurs
            current_app.logger.error(f"Error re-processing canonical job ID: {job.id} from URL: {opportunity.url}: {e}", exc_info=True)

    return jsonify({
        "message": "Job data re-processing initiated.",
        "reprocessed_count": reprocessed_count,
        "failed_count": failed_count,
        "note": "Check server logs for details. This is an asynchronous process."
    }), 200

@admin_bp.route('/admin/reprocess-incomplete-company-profiles', methods=['POST'])
@token_required
@admin_required
def reprocess_incomplete_company_profiles():
    """
    Admin endpoint to clean up and enrich historical company data.
    """
    current_app.logger.info("Admin: Starting re-processing of incomplete company profiles.")
    
    company_service = CompanyService(current_app.logger)

    reprocessed_count = 0
    failed_count = 0

    # Find companies with missing key data (e.g., industry, description)
    companies_to_reprocess = Company.query.filter(
        db.or_(
            Company.industry == None,
            Company.description == None,
            Company.mission == None,
            Company.business_model == None,
            Company.company_size_min == None,
            Company.headquarters == None,
            Company.founded_year == None,
            Company.website_url == None
        )
    ).limit(50).all() # Process in batches

    for company in companies_to_reprocess:
        try:
            # Re-run company research (which will update existing record)
            updated_company = company_service.research_and_update_company_profile(company.id)
            if updated_company:
                reprocessed_count += 1
                current_app.logger.info(f"Successfully re-processed company ID: {company.id} ({company.name})")
            else:
                failed_count += 1
                current_app.logger.error(f"Failed to re-process company ID: {company.id} ({company.name}). research_and_update_company_profile returned None.")
        except Exception as e:
            failed_count += 1
            db.session.rollback() # Rollback current transaction if error occurs
            current_app.logger.error(f"Error re-processing company ID: {company.id} ({company.name}): {e}", exc_info=True)

    return jsonify({
        "message": "Company profile re-processing initiated.",
        "reprocessed_count": reprocessed_count,
        "failed_count": failed_count,
        "note": "Check server logs for details. This is an asynchronous process."
    }), 200