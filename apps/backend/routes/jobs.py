# Path: apps/backend/routes/jobs.py

from flask import Blueprint, request, jsonify, g, current_app
from psycopg2.extras import Json
from ..auth import token_required
from ..services.job_service import JobService
from ..services.profile_service import ProfileService
from ..services.tracked_job_service import TrackedJobService
from ..database import get_db
from ..config import config
import psycopg2
import requests

jobs_bp = Blueprint('jobs_bp', __name__, url_prefix='/api')

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
        # First, check if the user is already tracking this job
        with db.cursor() as cursor:
            cursor.execute("SELECT t.id FROM tracked_jobs t JOIN jobs j ON t.job_id = j.id WHERE t.user_id = %s AND j.job_url = %s", (user_id, job_url))
            if cursor.fetchone():
                return jsonify({"error": "You are already tracking this job."}), 409

        # Fetch the user's profile to check their onboarding status
        user_profile = profile_service.get_profile(user_id)
        perform_ai_analysis = user_profile.get('has_completed_onboarding', False)
        
        analysis_result = None
        if perform_ai_analysis:
            current_app.logger.info(f"User {user_id} has completed onboarding. Performing full AI analysis.")
            user_profile_text = profile_service.get_profile_for_analysis(user_id)
            job_data = job_service.get_job_details_and_analysis(job_url, user_profile_text)
            analysis_result = job_data['analysis']
        else:
            current_app.logger.info(f"User {user_id} has not completed onboarding. Skipping AI analysis.")
            # We still need basic info if we're skipping AI. We can get this from a simple scrape.
            # This part can be enhanced later. For now, we'll use placeholders.
            analysis_result = {
                'company_name': 'Unknown Company (Profile Incomplete)',
                'job_title': 'Unknown Title (Profile Incomplete)'
            }


        with db.cursor() as cursor:
            company_name = analysis_result.get('company_name', 'Unknown Company')
            job_title = analysis_result.get('job_title', 'Unknown Title')
            salary_min = analysis_result.get('salary_min') if perform_ai_analysis else None
            salary_max = analysis_result.get('salary_max') if perform_ai_analysis else None
            required_experience_years = analysis_result.get('required_experience_years') if perform_ai_analysis else None
            job_modality = analysis_result.get('job_modality') if perform_ai_analysis else None
            deduced_job_level = analysis_result.get('deduced_job_level') if perform_ai_analysis else None

            cursor.execute("SELECT id FROM companies WHERE LOWER(name) = LOWER(%s)", (company_name,))
            company_row = cursor.fetchone()
            company_id = company_row['id'] if company_row else cursor.execute("INSERT INTO companies (name) VALUES (%s) RETURNING id", (company_name,)) and cursor.fetchone()['id']
            
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
            """, (
                company_id, company_name, job_title, job_url, 'User Submission',
                salary_min, salary_max, required_experience_years, job_modality, deduced_job_level
            ))
            job_id = cursor.fetchone()['id']

            # Only create an analysis record if we performed the analysis
            if perform_ai_analysis:
                cursor.execute("""
                    INSERT INTO job_analyses (job_id, user_id, analysis_protocol_version, position_relevance_score, environment_fit_score, hiring_manager_view, matrix_rating, summary, qualification_gaps, recommended_testimonials)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id, user_id) DO UPDATE SET
                        analysis_protocol_version = EXCLUDED.analysis_protocol_version, position_relevance_score = EXCLUDED.position_relevance_score,
                        environment_fit_score = EXCLUDED.environment_fit_score, hiring_manager_view = EXCLUDED.hiring_manager_view,
                        matrix_rating = EXCLUDED.matrix_rating, summary = EXCLUDED.summary, qualification_gaps = EXCLUDED.qualification_gaps,
                        recommended_testimonials = EXCLUDED.recommended_testimonials, updated_at = NOW();
                """, (
                    job_id, user_id, config.ANALYSIS_PROTOCOL_VERSION,
                    analysis_result.get('position_relevance_score'), analysis_result.get('environment_fit_score'),
                    analysis_result.get('hiring_manager_view'), analysis_result.get('matrix_rating'),
                    analysis_result.get('summary'), Json(analysis_result.get('qualification_gaps', [])),
                    Json(analysis_result.get('recommended_testimonials', []))
                ))

            cursor.execute("INSERT INTO tracked_jobs (user_id, job_id) VALUES (%s, %s) RETURNING id;", (user_id, job_id))
            tracked_job_id = cursor.fetchone()['id']
            db.commit()

        with db.cursor() as cursor:
            service = TrackedJobService(current_app.logger)
            new_job_data = service._get_formatted_job_by_id(cursor, tracked_job_id, user_id)
            return jsonify(new_job_data), 201

    except ValueError as e: return jsonify({"error": str(e)}), 400
    except (requests.exceptions.RequestException, ConnectionError) as e: return jsonify({"error": f"Service Error: {str(e)}"}), 503
    except psycopg2.Error as e:
        db.rollback()
        current_app.logger.error(f"DATABASE ERROR in submit_job route: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"An unexpected error occurred in submit_job route: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500