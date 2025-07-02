# Path: apps/backend/routes/jobs.py

from flask import Blueprint, request, jsonify, g, current_app
from psycopg2.extras import Json
import json
from ..auth import token_required
from ..services.job_service import JobService
from ..services.profile_service import ProfileService
from ..services.tracked_job_service import TrackedJobService
from ..database import get_db
from ..config import config
import psycopg2
import requests

jobs_bp = Blueprint('jobs_bp', __name__)

@jobs_bp.route('/jobs/submit', methods=['POST'])
@token_required
def submit_job():
    user_id = g.current_user['id']
    data = request.get_json()
    job_url = data.get('job_url')
    if not job_url:
        return jsonify({"error": "job_url is required"}), 400

    job_service = JobService(current_app.logger)
    profile_service = ProfileService(current_app.logger)
    db = get_db()
    
    try:
        with db.cursor() as cursor:
            # Check if this job URL already exists in our jobs table
            cursor.execute("SELECT id FROM jobs WHERE job_url = %s", (job_url,))
            job_row = cursor.fetchone()

            if job_row:
                job_id = job_row['id']
                cursor.execute("SELECT id FROM tracked_jobs WHERE user_id = %s AND job_id = %s", (user_id, job_id))
                if cursor.fetchone():
                    return jsonify({"error": "You are already tracking this job."}), 409
                else:
                    current_app.logger.info(f"User {user_id} is re-tracking existing job_id {job_id}.")
                    cursor.execute("INSERT INTO tracked_jobs (user_id, job_id) VALUES (%s, %s) RETURNING id;", (user_id, job_id))
                    tracked_job_id = cursor.fetchone()['id']
                    db.commit()
                    service = TrackedJobService(current_app.logger)
                    new_job_data = service._get_formatted_job_by_id(cursor, tracked_job_id, user_id)
                    return jsonify(new_job_data), 201
            
            # --- START: AUTOMATED COMPANY RESEARCH & DATA ENRICHMENT ---
            
            # Step 1: Get initial company name from lightweight scrape.
            # This is necessary to find or create the company record.
            basic_details = job_service.get_basic_job_details(job_url)
            company_name_guess = basic_details.get('company_name', 'Unknown Company')

            # Step 2: Find or create the company to get a stable company_id.
            cursor.execute("SELECT id FROM companies WHERE LOWER(name) = LOWER(%s)", (company_name_guess,))
            company_row = cursor.fetchone()
            if company_row:
                company_id = company_row['id']
            else:
                cursor.execute("INSERT INTO companies (name) VALUES (%s) RETURNING id", (company_name_guess,))
                company_id = cursor.fetchone()['id']
                # Commit immediately so the company record is available for the next step.
                db.commit()
            
            # Step 3: Check for user's onboarding status to decide on analysis type.
            user_profile = profile_service.get_profile(user_id)
            perform_ai_analysis = user_profile.get('has_completed_onboarding', False)
        
            analysis_result = None
            if perform_ai_analysis:
                current_app.logger.info(f"User {user_id} is onboarded. Enriching data and performing full analysis.")
                
                # Step 3a: Proactively research company if needed. This is best-effort.
                company_profile = job_service.research_and_get_company_profile(company_id)
                company_profile_text = json.dumps(company_profile, indent=2) if company_profile else "No company profile available."
                
                # Step 3b: Run the full job analysis with the enriched company context.
                user_profile_text = profile_service.get_profile_for_analysis(user_id)
                job_data = job_service.get_job_details_and_analysis(job_url, user_profile_text, company_profile_text)
                analysis_result = job_data['analysis']
            else:
                current_app.logger.info(f"User {user_id} is not onboarded. Using basic job details.")
                # For non-onboarded users, we still use the basic scrape details.
                analysis_result = basic_details

            # --- END: AUTOMATED COMPANY RESEARCH & DATA ENRICHMENT ---

            # Use the most accurate name/title from the full analysis if available, otherwise fall back to the scrape.
            company_name = analysis_result.get('company_name', company_name_guess)
            job_title = analysis_result.get('job_title', 'Unknown Title')
            
            salary_min = analysis_result.get('salary_min') if perform_ai_analysis else None
            salary_max = analysis_result.get('salary_max') if perform_ai_analysis else None
            required_experience_years = analysis_result.get('required_experience_years') if perform_ai_analysis else None
            job_modality = analysis_result.get('job_modality') if perform_ai_analysis else None
            deduced_job_level = analysis_result.get('deduced_job_level') if perform_ai_analysis else None

            # Update the company_id in case the AI analysis corrected the company name
            cursor.execute("SELECT id FROM companies WHERE LOWER(name) = LOWER(%s)", (company_name,))
            company_row = cursor.fetchone()
            if company_row:
                company_id = company_row['id']
            else:
                cursor.execute("INSERT INTO companies (name) VALUES (%s) RETURNING id", (company_name,))
                company_id = cursor.fetchone()['id']

            cursor.execute("""
                INSERT INTO jobs (company_id, company_name, job_title, job_url, source, status, last_checked_at,
                                  salary_min, salary_max, required_experience_years, job_modality, deduced_job_level)
                VALUES (%s, %s, %s, %s, %s, 'Active', NOW(), %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) DO UPDATE SET 
                    job_title = EXCLUDED.job_title, status = 'Active', last_checked_at = NOW(),
                    salary_min = EXCLUDED.salary_min, salary_max = EXCLUDED.salary_max,
                    required_experience_years = EXCLUDED.required_experience_years,
                    job_modality = EXCLUDED.job_modality, deduced_job_level = EXCLUDED.deduced_job_level
                RETURNING id;
            """, (company_id, company_name, job_title, job_url, 'User Submission', salary_min, salary_max, required_experience_years, job_modality, deduced_job_level))
            job_id = cursor.fetchone()['id']

            if perform_ai_analysis:
                cursor.execute("""
                    INSERT INTO job_analyses (job_id, user_id, analysis_protocol_version, position_relevance_score, environment_fit_score, hiring_manager_view, matrix_rating, summary, qualification_gaps, recommended_testimonials)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id, user_id) DO UPDATE SET
                        analysis_protocol_version = EXCLUDED.analysis_protocol_version, position_relevance_score = EXCLUDED.position_relevance_score,
                        environment_fit_score = EXCLUDED.environment_fit_score, hiring_manager_view = EXCLUDED.hiring_manager_view,
                        matrix_rating = EXCLUDED.matrix_rating, summary = EXCLUDED.summary, qualification_gaps = EXCLUDED.qualification_gaps,
                        recommended_testimonials = EXCLUDED.recommended_testimonials, updated_at = NOW();
                """, (job_id, user_id, config.ANALYSIS_PROTOCOL_VERSION, analysis_result.get('position_relevance_score'), analysis_result.get('environment_fit_score'), analysis_result.get('hiring_manager_view'), analysis_result.get('matrix_rating'), analysis_result.get('summary'), Json(analysis_result.get('qualification_gaps', [])), Json(analysis_result.get('recommended_testimonials', []))))

            cursor.execute("INSERT INTO tracked_jobs (user_id, job_id) VALUES (%s, %s) RETURNING id;", (user_id, job_id))
            tracked_job_id = cursor.fetchone()['id']
            db.commit()

            service = TrackedJobService(current_app.logger)
            new_job_data = service._get_formatted_job_by_id(cursor, tracked_job_id, user_id)
            return jsonify(new_job_data), 201

    except ValueError as e: return jsonify({"error": str(e)}), 400
    except (requests.exceptions.RequestException, ConnectionError) as e: return jsonify({"error": f"Service Error: {str(e)}"}), 503
    except psycopg2.IntegrityError as e:
        db.rollback()
        current_app.logger.error(f"DATABASE INTEGRITY ERROR in submit_job route: {e}")
        return jsonify({"error": "This job may already exist or could not be saved due to a data conflict."}), 409
    except psycopg2.Error as e:
        db.rollback()
        current_app.logger.error(f"DATABASE ERROR in submit_job route: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"An unexpected error occurred in submit_job route: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

# --- OTHER ENDPOINTS ARE UNCHANGED ---

@jobs_bp.route('/tracked-jobs', methods=['GET'])
@token_required
def get_tracked_jobs():
    user_id = g.current_user['id']
    try: page = int(request.args.get('page', 1)); limit = int(request.args.get('limit', 10))
    except (ValueError, TypeError): return jsonify({"error": "Invalid pagination parameters"}), 400
    offset = (page - 1) * limit
    db = get_db(); service = TrackedJobService(current_app.logger)
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM tracked_jobs WHERE user_id = %s;", (user_id,))
        total_count = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM tracked_jobs WHERE user_id = %s ORDER BY created_at DESC, id DESC LIMIT %s OFFSET %s;", (user_id, limit, offset))
        job_ids = [row['id'] for row in cursor.fetchall()]
        tracked_jobs = [service._get_formatted_job_by_id(cursor, job_id, user_id) for job_id in job_ids]
        return jsonify({"tracked_jobs": [j for j in tracked_jobs if j], "total_count": total_count, "page": page, "limit": limit})

@jobs_bp.route('/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(tracked_job_id):
    user_id = g.current_user['id']; data = request.get_json()
    if not data: return jsonify({"error": "No update data provided"}), 400
    service = TrackedJobService(current_app.logger)
    try:
        updated_job = service.update_job(user_id, tracked_job_id, data)
        if updated_job: return jsonify(updated_job), 200
        else: return jsonify({"error": "Tracked job not found or permission denied"}), 404
    except ValueError as e: return jsonify({"error": str(e)}), 400
    except Exception as e: current_app.logger.error(f"Error in update_tracked_job route: {e}"); return jsonify({"error": "An internal server error occurred."}), 500

@jobs_bp.route('/tracked-jobs/<int:tracked_job_id>', methods=['DELETE'])
@token_required
def remove_tracked_job(tracked_job_id):
    user_id = g.current_user['id']; db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM tracked_jobs WHERE id = %s AND user_id = %s RETURNING id", (tracked_job_id, user_id))
        if cursor.fetchone(): db.commit(); return jsonify({"message": "Tracked job removed successfully"}), 200
        else: return jsonify({"error": "Tracked job not found or permission denied"}), 404