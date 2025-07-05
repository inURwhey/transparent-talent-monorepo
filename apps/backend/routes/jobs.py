# Path: apps/backend/routes/jobs.py
from flask import Blueprint, request, jsonify, g, current_app
from ..auth import token_required
from ..services.profile_service import ProfileService
from ..services.job_service import JobService
from ..services.tracked_job_service import TrackedJobService
from ..app import db
from sqlalchemy.exc import IntegrityError
from ..models import JobAnalysis

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
    tracked_job_service = TrackedJobService(current_app.logger)

    try:
        canonical_job, job_opportunity = job_service.create_or_get_canonical_job(job_url, user_id=user_id, commit=True)
        
        if not canonical_job or not job_opportunity:
            return jsonify({"message": "Failed to process job URL. Could not extract core details."}), 500

        tracked_job = tracked_job_service.track_job(user_id, job_opportunity.id)
        
        if not tracked_job:
            return jsonify({"message": "Failed to track job opportunity (internal error). Please try again."}), 500
        
        jobs_data = tracked_job_service.get_tracked_jobs(user_id, job_id_filter=tracked_job.id)
        if jobs_data and jobs_data.get("jobs"):
             return jsonify(jobs_data["jobs"][0]), 201
        
        return jsonify({"message": "Job tracked successfully, but failed to retrieve full details."}), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Job already tracked or other database conflict."}), 409
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
    limit = int(request.args.get('limit', 1000))

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
    # CORRECTED: The entire JSON body is the payload.
    payload = request.json

    if not payload:
        return jsonify({"message": "Payload is required."}), 400

    tracked_job_service = TrackedJobService(current_app.logger)

    try:
        updated_job = tracked_job_service.update_tracked_job(user_id, tracked_job_id, payload)
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