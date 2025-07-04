# Path: apps/backend/routes/jobs.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..services.job_service import JobService
from ..services.tracked_job_service import TrackedJobService
from ..app import db # NEW: Import db for rollback in routes
from sqlalchemy.exc import IntegrityError # NEW: Import IntegrityError for specific handling

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/jobs/submit', methods=['POST'])
@token_required
def submit_job():
    user_id = g.current_user.id
    data = request.json
    job_url = data.get('job_url')

    if not job_url:
        return jsonify({"message": "Job URL is required."}), 400

    job_service = JobService(current_app.logger)
    profile_service = ProfileService(current_app.logger)
    tracked_job_service = TrackedJobService(current_app.logger)

    try:
        # 1. Create or get the canonical Job and JobOpportunity
        # The create_or_get_canonical_job now handles lightweight scrape and initial AI analysis
        # for new canonical jobs.
        canonical_job, job_opportunity = job_service.create_or_get_canonical_job(job_url, user_id=user_id, commit=True) # Pass user_id
        
        if not canonical_job or not job_opportunity:
            db.session.rollback() # Ensure rollback if job or opportunity creation failed
            return jsonify({"message": "Failed to process job URL. Could not extract core details."}), 500

        # Check for user's profile completion status. This happens in job_service for new canonical jobs.
        # But if it's an existing canonical job, we might need to trigger analysis here.
        
        # 2. Track the job opportunity for the user
        tracked_job = tracked_job_service.track_job(user_id, job_opportunity.id)
        # track_job will return existing_tracked_job if already tracked
        if not tracked_job:
            # This branch should typically not be hit if track_job returns the existing object
            return jsonify({"message": "Failed to track job opportunity (internal error). Please try again."}), 500

        # 3. If it's a newly tracked job and profile is complete, ensure analysis happened or trigger it
        # If the canonical job was new, initial analysis was triggered by create_or_get_canonical_job
        # If the canonical job existed, we need to ensure analysis for *this user* has happened.
        # Check if an analysis exists for this user and canonical job
        from ..models import JobAnalysis # Import model here to avoid circular if needed
        existing_analysis = JobAnalysis.query.filter_by(user_id=user_id, job_id=canonical_job.id).first()

        if not existing_analysis and profile_service.has_completed_required_profile_fields(user_id):
            current_app.logger.info(f"No existing analysis for user {user_id} and canonical job {canonical_job.id}. Triggering now.")
            user_profile_data = profile_service.get_profile_for_analysis(user_id)
            job_description_to_analyze = canonical_job.notes # Assume notes has the description for analysis
            if not job_description_to_analyze and canonical_job.opportunities:
                # If notes doesn't have it, try scraping one of the opportunity URLs
                scraped_data = job_service._lightweight_scrape(canonical_job.opportunities[0].url)
                job_description_to_analyze = scraped_data.get('description') if scraped_data else None

            if job_description_to_analyze:
                ai_analysis_data = job_service.analyze_job_posting(job_description_to_analyze, user_profile_data, canonical_job.company.to_dict() if canonical_job.company else {})
                if ai_analysis_data:
                    job_service.create_or_update_job_analysis(user_id, canonical_job.id, ai_analysis_data)
                    current_app.logger.info(f"AI analysis completed for user {user_id}, canonical job {canonical_job.id}")
                else:
                    current_app.logger.warning(f"AI analysis failed for job {job_url}. Will not save analysis.")
            else:
                current_app.logger.warning(f"Could not get job description for AI analysis of {job_url}")

        # 4. Prepare response data by re-fetching the tracked_job with all relationships loaded
        response_tracked_job = tracked_job_service.get_tracked_job_by_opportunity_id(user_id, job_opportunity.id)
        if response_tracked_job:
            # Manually load related data for response, similar to get_tracked_jobs service method
            response_data = response_tracked_job.to_dict()
            response_data['job_opportunity'] = response_tracked_job.job_opportunity.to_dict()
            response_data['job'] = response_tracked_job.job_opportunity.job.to_dict()
            response_data['company'] = response_tracked_job.job_opportunity.job.company.to_dict() if response_tracked_job.job_opportunity.job.company else None
            
            # Get the specific analysis for this user and the canonical job
            user_analysis = JobAnalysis.query.filter_by(user_id=user_id, job_id=response_tracked_job.job_opportunity.job.id).first()
            if user_analysis:
                response_data['job_analysis'] = user_analysis.to_dict()
                response_data['ai_grade'] = user_analysis.matrix_rating
            else:
                response_data['job_analysis'] = None
                response_data['ai_grade'] = None

            return jsonify(response_data), 201
        else:
            # Fallback if somehow tracking succeeded but retrieval failed
            return jsonify({"message": "Job tracked, but failed to retrieve full details for response."}), 201

    except IntegrityError as e:
        db.session.rollback()
        # Check for duplicate entry error specifically (e.g., if track_job hit unique constraint)
        if "tracked_jobs_user_id_job_opportunity_id_key" in str(e):
             current_app.logger.info(f"User {user_id} attempted to track duplicate job opportunity for URL: {job_url}.")
             # Attempt to fetch and return the existing tracked job to the client
             # Need to re-create canonical_job and job_opportunity without committing
             canonical_job_temp, job_opportunity_temp = job_service.create_or_get_canonical_job(job_url, user_id=user_id, commit=False)
             if job_opportunity_temp:
                 existing_tracked = tracked_job_service.get_tracked_job_by_opportunity_id(user_id, job_opportunity_temp.id)
                 if existing_tracked:
                     # Load relations for existing tracked job
                     response_data = existing_tracked.to_dict()
                     response_data['job_opportunity'] = existing_tracked.job_opportunity.to_dict()
                     response_data['job'] = existing_tracked.job_opportunity.job.to_dict()
                     response_data['company'] = existing_tracked.job_opportunity.job.company.to_dict() if existing_tracked.job_opportunity.job.company else None
                     user_analysis = JobAnalysis.query.filter_by(user_id=user_id, job_id=existing_tracked.job_opportunity.job.id).first()
                     if user_analysis:
                         response_data['job_analysis'] = user_analysis.to_dict()
                         response_data['ai_grade'] = user_analysis.matrix_rating
                     else:
                         response_data['job_analysis'] = None
                         response_data['ai_grade'] = None
                     return jsonify({"message": "Job already tracked.", "tracked_job": response_data}), 200
             return jsonify({"message": "Job already tracked or other database conflict."}), 409 # Conflict

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error submitting job for user {user_id}: {e}", exc_info=True)
        return jsonify({"message": "An unexpected error occurred while submitting the job."}), 500


@jobs_bp.route('/tracked-jobs', methods=['GET'])
@token_required
def get_tracked_jobs():
    user_id = g.current_user.id
    status_filter = request.args.get('status_filter')
    search_query = request.args.get('search_query')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))

    tracked_job_service = TrackedJobService(current_app.logger)

    try:
        jobs_data = tracked_job_service.get_tracked_jobs(user_id, status_filter, search_query, page, limit)
        return jsonify(jobs_data), 200
    except Exception as e:
        current_app.logger.error(f"Error getting tracked jobs for user {user_id}: {e}", exc_info=True)
        return jsonify({"message": "Error fetching tracked jobs."}), 500

@jobs_bp.route('/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(tracked_job_id):
    user_id = g.current_user.id
    data = request.json
    field = data.get('field')
    value = data.get('value')

    if not field:
        return jsonify({"message": "Field to update is required."}), 400

    tracked_job_service = TrackedJobService(current_app.logger)

    try:
        updated_job = tracked_job_service.update_tracked_job_field(user_id, tracked_job_id, field, value)
        if updated_job:
            return jsonify(updated_job), 200
        return jsonify({"message": "Tracked job not found or update failed."}), 404
    except Exception as e:
        current_app.logger.error(f"Error updating tracked job {tracked_job_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"message": "Error updating tracked job."}), 500

@jobs_bp.route('/tracked-jobs/<int:tracked_job_id>', methods=['DELETE'])
@token_required
def remove_tracked_job(tracked_job_id):
    user_id = g.current_user.id
    tracked_job_service = TrackedJobService(current_app.logger)

    try:
        if tracked_job_service.remove_tracked_job(user_id, tracked_job_id):
            return jsonify({"message": "Tracked job deleted successfully."}), 200
        return jsonify({"message": "Tracked job not found or delete failed."}), 404
    except Exception as e:
        current_app.logger.error(f"Error deleting tracked job {tracked_job_id} for user {user_id}: {e}", exc_info=True)
        return jsonify({"message": "Error deleting tracked job."}), 500