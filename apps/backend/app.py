# Path: apps/backend/app.py
import os
import psycopg2
from psycopg2.extras import DictCursor, Json
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import date, datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import re
from functools import wraps # NEW: Import wraps for the new decorator

from auth import token_required

# --- Initialization ---
load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True, expose_headers=["Authorization"])

# --- Constants ---
ANALYSIS_PROTOCOL_VERSION = '2.0'
JOB_POSTING_MAX_AGE_DAYS = 60
TRACKED_JOB_STALE_DAYS = 30
LEGACY_URL_MALFORMED_PATTERN = re.compile(r".+\s+\(.+\)|\(.+?\)$")

# NEW: Retrieve the API Key for integrity checks
INTEGRITY_CHECK_API_KEY = os.getenv('INTEGRITY_CHECK_API_KEY')
if not INTEGRITY_CHECK_API_KEY:
    print("Warning: INTEGRITY_CHECK_API_KEY is not set. Admin endpoints might be unprotected or inaccessible.")

# --- NEW: Simple API Key Authentication Decorator for Testing ---
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not INTEGRITY_CHECK_API_KEY:
            return jsonify({"message": "API Key not configured on server."}), 500

        api_key_header = request.headers.get('X-Api-Key') # Use a custom header like X-Api-Key
        if not api_key_header or api_key_header != INTEGRITY_CHECK_API_KEY:
            app.logger.warning("Attempted access to API key protected endpoint with missing or invalid key.")
            return jsonify({"message": "Unauthorized: Invalid or missing API Key."}), 401
        return f(*args, **kwargs)
    return decorated_function


# --- AI Configuration ---
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("Warning: GEMINI_API_KEY is not set. Job analysis will fail.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url: raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(db_url)

# --- Helper function to check URL validity ---
def check_job_url_validity(full_url_string: str) -> bool:
    """
    Extracts a clean URL from a string and performs an HTTP HEAD request to check if it's reachable (2xx or 3xx status).
    Handles cases where the string might contain extra text.
    """
    url_match = re.search(r"https?://[^\s)\]]+", full_url_string)
    if not url_match:
        app.logger.warning(f"No valid URL pattern found for HTTP request in string: {full_url_string}")
        return False

    clean_url = url_match.group(0)

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.head(clean_url, timeout=5, headers=headers, allow_redirects=True)
        return 200 <= response.status_code < 400
    except requests.exceptions.RequestException as e:
        app.logger.warning(f"Error checking URL '{clean_url}' extracted from '{full_url_string}': {e}")
        return False
    except Exception as e:
        app.logger.error(f"Unexpected error in check_job_url_validity for '{clean_url}' extracted from '{full_url_string}': {e}")
        return False


# --- API Endpoints ---

@app.route('/api/jobs/submit', methods=['POST'])
@token_required
def submit_job():
    user_id = g.current_user['id']
    data = request.get_json()
    job_url = data.get('job_url')
    if not job_url:
        return jsonify({"error": "job_url is required"}), 400
    
    conn = None
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        response = requests.get(job_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        job_text = soup.get_text(separator=' ', strip=True)
        
        conn = get_db_connection()
        conn.autocommit = False
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT t.id FROM tracked_jobs t JOIN jobs j ON t.job_id = j.id WHERE t.user_id = %s AND j.job_url = %s", (user_id, job_url))
            if cursor.fetchone():
                return jsonify({"error": "You are already tracking this job."}), 409

            profile_columns = [
                "short_term_career_goal", "ideal_role_description", "core_strengths",
                "skills_to_avoid", "preferred_industries", "industries_to_avoid",
                "desired_title", "non_negotiable_requirements", "deal_breakers",
                "preferred_work_style", "is_remote_preferred"
            ]
            sql = f"SELECT {', '.join(profile_columns)} FROM user_profiles WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            user_profile_row = cursor.fetchone()

            if not user_profile_row:
                return jsonify({"error": "User profile not found. Cannot perform analysis."}), 404

            user_profile_parts = []
            profile_labels = {
                "short_term_career_goal": "Short-Term Career Goal", "ideal_role_description": "Ideal Role",
                "core_strengths": "Core Strengths", "skills_to_avoid": "Skills To Avoid",
                "preferred_industries": "Preferred Industries", "industries_to_avoid": "Industries To Avoid",
                "desired_title": "Desired Title", "non_negotiable_requirements": "Non-Negotiables",
                "deal_breakers": "Deal Breakers",
                "preferred_work_style": "Preferred Work Style",
                "is_remote_preferred": "Remote Preference"
            }
            for col in profile_columns:
                value = user_profile_row[col]
                if col == 'is_remote_preferred':
                    if value is True:
                        user_profile_parts.append(f"- {profile_labels[col]}: Yes, remote is preferred.")
                    elif value is False:
                        user_profile_parts.append(f"- {profile_labels[col]}: No, remote is not preferred.")
                elif value and str(value).strip():
                    user_profile_parts.append(f"- {profile_labels[col]}: {value}")

            if not user_profile_parts:
                return jsonify({"error": "User profile is too sparse. Please fill out your profile to enable analysis."}), 400
            
            user_profile_text = "\n".join(user_profile_parts)

            analysis_result = run_job_analysis(job_text, user_profile_text)
            
            company_name = analysis_result.get('company_name', 'Unknown Company')
            job_title = analysis_result.get('job_title', 'Unknown Title')
            
            cursor.execute("SELECT id FROM companies WHERE LOWER(name) = LOWER(%s)", (company_name,))
            company_row = cursor.fetchone()
            if company_row:
                company_id = company_row['id']
            else:
                cursor.execute("INSERT INTO companies (name) VALUES (%s) RETURNING id", (company_name,))
                company_id = cursor.fetchone()['id']
            
            cursor.execute("""
                INSERT INTO jobs (company_id, company_name, job_title, job_url, source, status, last_checked_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_url) DO UPDATE SET
                company_id = EXCLUDED.company_id,
                company_name = EXCLUDED.company_name,
                job_title = EXCLUDED.job_title,
                status = 'Active',
                last_checked_at = %s
                RETURNING id;
            """, (company_id, company_name, job_title, job_url, 'User Submission', 'Active', datetime.now(timezone.utc), datetime.now(timezone.utc)))
            job_id = cursor.fetchone()['id']
            
            cursor.execute("""
                INSERT INTO job_analyses (job_id, user_id, analysis_protocol_version, position_relevance_score, environment_fit_score, hiring_manager_view, matrix_rating, summary, qualification_gaps, recommended_testimonials)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_id, user_id) DO UPDATE SET
                    analysis_protocol_version = EXCLUDED.analysis_protocol_version,
                    position_relevance_score = EXCLUDED.position_relevance_score,
                    environment_fit_score = EXCLUDED.environment_fit_score,
                    hiring_manager_view = EXCLUDED.hiring_manager_view,
                    matrix_rating = EXCLUDED.matrix_rating,
                    summary = EXCLUDED.summary,
                    qualification_gaps = EXCLUDED.qualification_gaps,
                    recommended_testimonials = EXCLUDED.recommended_testimonials,
                    updated_at = CURRENT_TIMESTAMP;
            """, (
                job_id, user_id, ANALYSIS_PROTOCOL_VERSION,
                analysis_result.get('position_relevance_score'), analysis_result.get('environment_fit_score'),
                analysis_result.get('hiring_manager_view'), analysis_result.get('matrix_rating'),
                analysis_result.get('summary'), Json(analysis_result.get('qualification_gaps', [])),
                Json(analysis_result.get('recommended_testimonials', []))
            ))
            
            cursor.execute("INSERT INTO tracked_jobs (user_id, job_id, status, status_reason) VALUES (%s, %s, %s, %s) RETURNING id;", (user_id, job_id, 'Saved', None))
            tracked_job_id = cursor.fetchone()['id']
            
            conn.commit()
            
            cursor.execute("""
                SELECT j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                       j.status as job_posting_status, j.last_checked_at,
                       t.id as tracked_job_id, t.status, t.notes as user_notes, t.applied_at, t.created_at, t.is_excited, t.status_reason,
                       ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                       ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
                FROM jobs j 
                JOIN tracked_jobs t ON j.id = t.job_id 
                LEFT JOIN job_analyses ja ON j.id = ja.job_id AND t.user_id = ja.user_id
                WHERE t.id = %s;
            """, (tracked_job_id,))
            new_job_row = cursor.fetchone()
            
            response_data = {
                "job_id": new_job_row["job_id"], "company_name": new_job_row["company_name"],
                "job_title": new_job_row["job_title"], "job_url": new_job_row["job_url"],
                "source": new_job_row["source"], "found_at": new_job_row["found_at"],
                "job_posting_status": new_job_row["job_posting_status"],
                "last_checked_at": new_job_row["last_checked_at"],
                "tracked_job_id": new_job_row["tracked_job_id"], "status": new_job_row["status"],
                "user_notes": new_job_row["user_notes"], "applied_at": new_job_row["applied_at"],
                "created_at": new_job_row["created_at"],
                "is_excited": new_job_row["is_excited"],
                "status_reason": new_job_row["status_reason"],
                "ai_analysis": {
                    "position_relevance_score": new_job_row["position_relevance_score"],
                    "environment_fit_score": new_job_row["environment_fit_score"],
                    "hiring_manager_view": new_job_row["hiring_manager_view"],
                    "matrix_rating": new_job_row["matrix_rating"],
                    "summary": new_job_row["ai_summary"],
                    "qualification_gaps": new_job_row["qualification_gaps"],
                    "recommended_testimonials": new_job_row["recommended_testimonials"]
                }
            }
            return jsonify(response_data), 201

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch job URL: {str(e)}"}), 500
    except json.JSONDecodeError as e:
        if conn: conn.rollback()
        return jsonify({"error": f"Failed to parse AI response: {str(e)}"}), 500
    except psycopg2.Error as e:
        if conn: conn.rollback()
        app.logger.error(f"DATABASE ERROR in submit_job: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        if conn: conn.rollback()
        app.logger.error(f"An unexpected error occurred in submit_job: {e}") 
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        if conn: conn.close()

@app.route('/api/profile', methods=['GET'])
@token_required
def get_user_profile():
    user_id = g.current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "SELECT * FROM user_profiles WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            profile = cursor.fetchone()
            
            if not profile:
                app.logger.info(f"No profile found for user_id {user_id}. Creating default profile.")
                insert_sql = """
                    INSERT INTO user_profiles (user_id) VALUES (%s)
                    RETURNING *;
                """
                cursor.execute(insert_sql, (user_id,))
                profile = cursor.fetchone()
                conn.commit()
            
            profile_dict = {}
            if profile:
                for col in cursor.description:
                    col_name = col.name
                    value = profile[col_name]
                    if col_name in ['full_name', 'current_location', 'linkedin_profile_url', 'resume_url',
                                    'short_term_career_goal', 'long_term_career_goals', 'desired_annual_compensation',
                                    'desired_title', 'ideal_role_description', 'preferred_company_size',
                                    'ideal_work_culture', 'disliked_work_culture', 'core_strengths',
                                    'skills_to_avoid', 'preferred_industries', 'industries_to_avoid',
                                    'personality_adjectives',
                                    'personality_16_personalities', 'personality_disc', 'personality_gallup_strengths',
                                    'preferred_work_style'] and value is None:
                        profile_dict[col_name] = ""
                    elif col_name == 'is_remote_preferred':
                        profile_dict[col_name] = value if value is not None else False
                    else:
                        profile_dict[col_name] = value
            
            return jsonify(profile_dict)
    except Exception as e:
        app.logger.error(f"ERROR in get_user_profile: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/profile', methods=['PUT'])
@token_required
def update_user_profile():
    user_id = g.current_user['id']
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided for profile update"}), 400

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT id FROM user_profiles WHERE user_id = %s", (user_id,))
            existing_profile = cursor.fetchone()
            if not existing_profile:
                cursor.execute("INSERT INTO user_profiles (user_id) VALUES (%s) RETURNING id;", (user_id,))
                conn.commit()
            
            fields_to_update = []
            params = []
            
            allowed_profile_fields = [
                "full_name", "current_location", "linkedin_profile_url", "resume_url",
                "short_term_career_goal", "long_term_career_goals", "desired_annual_compensation",
                "desired_title", "ideal_role_description", "preferred_company_size",
                "ideal_work_culture", "disliked_work_culture", "core_strengths",
                "skills_to_avoid", "non_negotiable_requirements", "deal_breakers",
                "preferred_industries", "industries_to_avoid", "personality_adjectives",
                "personality_16_personalities", "personality_disc", "personality_gallup_strengths",
                "preferred_work_style", "is_remote_preferred"
            ]

            for field, value in data.items():
                if field in allowed_profile_fields:
                    fields_to_update.append(f"{field} = %s")
                    if field == 'is_remote_preferred':
                        if isinstance(value, str):
                            params.append(value.lower() == 'true')
                        else:
                            params.append(bool(value))
                    else:
                        params.append(value)
            
            if not fields_to_update:
                return jsonify({"message": "No valid profile fields to update"}), 200

            sql = f"UPDATE user_profiles SET {', '.join(fields_to_update)} WHERE user_id = %s RETURNING *;"
            params.append(user_id)
            
            cursor.execute(sql, tuple(params))
            updated_profile = cursor.fetchone()
            conn.commit()

            if updated_profile:
                profile_dict = {}
                for col in cursor.description:
                    profile_dict[col.name] = updated_profile[col.name]
                return jsonify(profile_dict), 200
            else:
                return jsonify({"error": "Failed to update profile or profile not found."}), 500

    except psycopg2.Error as e:
        conn.rollback()
        app.logger.error(f"DATABASE ERROR in update_user_profile: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"An unexpected error occurred in update_user_profile: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500
    finally:
        conn.close()

@app.route('/api/jobs', methods=['GET'])
@token_required
def get_user_jobs():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            excluded_companies = ['various', 'various companies', 'confidential']
            sql = "SELECT id, company_name, job_title, job_url, source, status, last_checked_at FROM jobs WHERE LOWER(company_name) NOT IN %s AND status = 'Active' ORDER BY found_at DESC LIMIT 50"
            cursor.execute(sql, (tuple(excluded_companies),))
            jobs = [dict(row) for row in cursor.fetchall()]
            return jsonify(jobs)
    except Exception as e:
        app.logger.error(f"ERROR in get_user_jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/tracked-jobs', methods=['GET'])
@token_required
def get_tracked_jobs():
    user_id = g.current_user['id']

    # Pagination parameters
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        if page < 1: page = 1
        if limit < 1: limit = 1
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    offset = (page - 1) * limit

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT COUNT(*) FROM tracked_jobs WHERE user_id = %s;", (user_id,))
            total_count = cursor.fetchone()[0]

            sql = """
                SELECT 
                    j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                    j.status as job_posting_status, j.last_checked_at,
                    t.id as tracked_job_id, t.status, t.notes as user_notes, t.applied_at, t.created_at, t.is_excited, t.status_reason,
                    ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                    ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
                FROM jobs j
                JOIN tracked_jobs t ON j.id = t.job_id
                LEFT JOIN job_analyses ja ON j.id = ja.job_id AND t.user_id = ja.user_id
                WHERE t.user_id = %s
                ORDER BY t.created_at DESC, t.id DESC
                LIMIT %s OFFSET %s;
            """
            cursor.execute(sql, (user_id, limit, offset))
            tracked_jobs = []
            for row in cursor.fetchall():
                job = {
                    "job_id": row["job_id"], "company_name": row["company_name"],
                    "job_title": row["job_title"], "job_url": row["job_url"],
                    "source": row["source"], "found_at": row["found_at"],
                    "job_posting_status": row["job_posting_status"],
                    "last_checked_at": row["last_checked_at"],
                    "tracked_job_id": row["tracked_job_id"], "status": row["status"],
                    "user_notes": row["user_notes"], "applied_at": row["applied_at"],
                    "created_at": row["created_at"],
                    "is_excited": row["is_excited"],
                    "status_reason": row["status_reason"],
                    "ai_analysis": None
                }
                if row["position_relevance_score"] is not None:
                    job["ai_analysis"] = {
                        "position_relevance_score": row["position_relevance_score"],
                        "environment_fit_score": row["environment_fit_score"],
                        "hiring_manager_view": row["hiring_manager_view"],
                        "matrix_rating": row["matrix_rating"],
                        "summary": row["ai_summary"],
                        "qualification_gaps": row["qualification_gaps"],
                        "recommended_testimonials": row["recommended_testimonials"]
                    }
                tracked_jobs.append(job)
            return jsonify({
                "tracked_jobs": tracked_jobs,
                "total_count": total_count,
                "page": page,
                "limit": limit
            })
    except Exception as e:
        app.logger.error(f"ERROR in get_tracked_jobs: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/tracked-jobs', methods=['POST'])
@token_required
def add_tracked_job():
    user_id = g.current_user['id']
    data = request.get_json()
    job_id = data.get('job_id')
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO tracked_jobs (user_id, job_id, status, status_reason) VALUES (%s, %s, %s, %s) RETURNING id;",
                (user_id, job_id, 'Saved', None)
            )
            tracked_job_id = cursor.fetchone()[0]
            conn.commit()
        return jsonify({"message": "Job tracked successfully", "tracked_job_id": tracked_job_id}), 201
    except Exception as e:
        app.logger.error(f"ERROR in add_tracked_job: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(tracked_job_id):
    user_id = g.current_user['id']
    data = request.get_json()
    if not data or not any(key in data for key in ['status', 'notes', 'applied_at', 'is_excited', 'status_reason']):
        return jsonify({"error": "No update data provided"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT id FROM tracked_jobs WHERE id = %s AND user_id = %s", (tracked_job_id, user_id))
            if not cursor.fetchone():
                return jsonify({"error": "Tracked job not found or permission denied"}), 404
            fields, params = [], []
            if 'status' in data:
                fields.append("status = %s")
                params.append(data['status'])
            if 'notes' in data:
                fields.append("notes = %s")
                params.append(data['notes'])
            if 'applied_at' in data:
                fields.append("applied_at = %s")
                params.append(data['applied_at'])
            if 'is_excited' in data:
                fields.append("is_excited = %s")
                params.append(bool(data['is_excited']))
            if 'status_reason' in data:
                fields.append("status_reason = %s")
                params.append(data['status_reason'])

            if not fields:
                return jsonify({"error": "No valid fields to update"}), 400
            sql = f"UPDATE tracked_jobs SET {', '.join(fields)} WHERE id = %s RETURNING *"
            params.append(tracked_job_id)
            cursor.execute(sql, tuple(params))
            updated_job = dict(cursor.fetchone())
            conn.commit()
            return jsonify(updated_job)
    except Exception as e:
        app.logger.error(f"ERROR in update_tracked_job: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/tracked-jobs/<int:tracked_job_id>', methods=['DELETE'])
@token_required
def remove_tracked_job(tracked_job_id):
    user_id = g.current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM tracked_jobs WHERE id = %s AND user_id = %s RETURNING id", (tracked_job_id, user_id))
            deleted_id = cursor.fetchone()
            conn.commit()
            if deleted_id:
                return jsonify({"message": "Tracked job removed successfully"}), 200
            else:
                return jsonify({"error": "Tracked job not found or permission denied"}), 404
    except Exception as e:
        app.logger.error(f"ERROR in remove_tracked_job: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# --- Endpoint to trigger job URL validity and age check ---
@app.route('/api/admin/jobs/check-url-validity', methods=['POST'])
# @token_required # TEMPORARILY COMMENTED OUT FOR API KEY TESTING
@api_key_required # NEW: Use API key for testing
def check_job_urls():
    """
    Checks the validity and age of job URLs and updates their status in the 'jobs' table.
    This endpoint is intended to be called by a scheduled task (e.g., Render Cron Job).
    """
    checked_count = 0
    updated_count = 0
    errors = []

    try:
        conn = get_db_connection()
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=DictCursor)

        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        sixty_days_ago = datetime.now(timezone.utc) - timedelta(days=JOB_POSTING_MAX_AGE_DAYS)
        
        # Select jobs that need checking based on last_checked_at, age, or if they match legacy patterns.
        cur.execute("""
            SELECT id, job_url, status, found_at
            FROM jobs
            WHERE last_checked_at IS NULL
               OR last_checked_at < %s
               OR (status = 'Active' AND found_at < %s)
               OR (job_url IS NOT NULL AND job_url != '' AND job_url ~ %s)
            LIMIT 1000;
        """, (twenty_four_hours_ago, sixty_days_ago, LEGACY_URL_MALFORMED_PATTERN.pattern))
        
        jobs_to_check = cur.fetchall()

        app.logger.info(f"Found {len(jobs_to_check)} jobs to check URLs and age for.")

        for job in jobs_to_check:
            checked_count += 1
            current_time_utc = datetime.now(timezone.utc)
            new_status = job['status']
            
            if not job['job_url'] or not job['job_url'].strip():
                if job['status'] != 'Expired - Missing URL':
                    new_status = 'Expired - Missing URL'
                    app.logger.warning(f"Job ID {job['id']} has no job_url. Marking as '{new_status}'.")
                else:
                    app.logger.info(f"Job ID {job['id']} already 'Expired - Missing URL'. Just updating check time.")
                
            elif LEGACY_URL_MALFORMED_PATTERN.search(job['job_url']):
                if job['status'] != 'Expired - Legacy Format':
                    new_status = 'Expired - Legacy Format'
                    app.logger.warning(f"Job ID {job['id']} URL '{job['job_url']}' matches legacy malformed pattern. Marking as '{new_status}'.")
                else:
                    app.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' still 'Expired - Legacy Format'. Just updating check time.")
            
            else:
                is_valid_url = check_job_url_validity(job['job_url'])

                if not is_valid_url:
                    if job['status'] != 'Expired - Unreachable':
                        new_status = 'Expired - Unreachable'
                        app.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' is unreachable. Marking as '{new_status}'.")
                    else:
                        app.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' still unreachable. Just updating check time.")
                else:
                    if job['found_at'] and job['found_at'] < sixty_days_ago:
                        if job['status'] != 'Expired - Time Based':
                            new_status = 'Expired - Time Based'
                            app.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' is too old (found_at). Marking as '{new_status}'.")
                        else:
                            app.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' still 'Expired - Time Based'. Just updating check time.")
                    else:
                        if job['status'] != 'Active':
                            new_status = 'Active'
                            app.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' is active. Marking as '{new_status}'.")
                        else:
                            app.logger.info(f"Job ID {job['id']} URL '{job['job_url']}' is still 'Active'. Just updating check time.")

            if new_status != job['status'] or job['last_checked_at'] is None or job['last_checked_at'] < twenty_four_hours_ago:
                cur.execute("""
                    UPDATE jobs
                    SET status = %s, last_checked_at = %s
                    WHERE id = %s;
                """, (new_status, current_time_utc, job['id']))
                updated_count += 1
        
        conn.commit()
        app.logger.info(f"Finished checking job URLs and age. Checked: {checked_count}, Updated status: {updated_count}")
        return jsonify({
            "message": "Job URL validity and age check completed.",
            "jobs_checked": checked_count,
            "jobs_status_updated": updated_count,
            "errors": errors
        }), 200

    except Exception as e:
        if conn: conn.rollback()
        app.logger.error(f"Error during job URL validity and age check: {e}")
        return jsonify({"message": "Internal server error during URL check.", "error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()

# --- NEW: Endpoint to trigger tracked job application expiration ---
@app.route('/api/admin/tracked-jobs/check-expiration', methods=['POST'])
# @token_required # TEMPORARILY COMMENTED OUT FOR API KEY TESTING
@api_key_required # NEW: Use API key for testing
def check_tracked_job_expiration():
    """
    Checks tracked jobs for staleness based on last action (updated_at) and marks them expired.
    This endpoint is intended to be called by a scheduled task.
    """
    checked_count = 0
    expired_count = 0
    errors = []

    try:
        conn = get_db_connection()
        conn.autocommit = False
        cur = conn.cursor(cursor_factory=DictCursor)

        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=TRACKED_JOB_STALE_DAYS)

        cur.execute("""
            SELECT id, user_id, status, status_reason, applied_at, created_at, updated_at
            FROM tracked_jobs
            WHERE status NOT IN ('Expired', 'Rejected', 'Offer', 'Accepted', 'Withdrawn')
              AND updated_at < %s
            LIMIT 1000;
        """, (thirty_days_ago,))
        
        jobs_to_check = cur.fetchall()

        app.logger.info(f"Found {len(jobs_to_check)} tracked jobs to check for expiration.")

        for job in jobs_to_check:
            checked_count += 1
            
            if job['status'] != 'Expired':
                new_status = 'Expired'
                new_reason = 'Stale - No action in 30 days'
                app.logger.info(f"Tracked Job ID {job['id']} (User {job['user_id']}) is stale. Marking as '{new_status}' with reason '{new_reason}'.")
                cur.execute("""
                    UPDATE tracked_jobs
                    SET status = %s, status_reason = %s
                    WHERE id = %s;
                """, (new_status, new_reason, job['id']))
                expired_count += 1
            else:
                app.logger.info(f"Tracked Job ID {job['id']} already expired. Skipping.")
        
        conn.commit()
        app.logger.info(f"Finished checking tracked job expiration. Checked: {checked_count}, Marked Expired: {expired_count}")
        return jsonify({
            "message": "Tracked job expiration check completed.",
            "tracked_jobs_checked": checked_count,
            "tracked_jobs_marked_expired": expired_count,
            "errors": errors
        }), 200

    except Exception as e:
        if conn: conn.rollback()
        app.logger.error(f"Error during tracked job expiration check: {e}")
        return jsonify({"message": "Internal server error during tracked job expiration check.", "error": str(e)}), 500
    finally:
        if conn:
            cur.close()
            conn.close()


@app.route('/api/debug-env', methods=['GET'])
def debug_env():
    clerk_key = os.getenv('CLERK_SECRET_KEY')
    db_url = os.getenv('DATABASE_URL')
    gemini_key = os.getenv('GEMINI_API_KEY')
    response = {
        "clerk_key_is_set": bool(clerk_key),
        "db_url_is_set": bool(db_url),
        "gemini_key_is_set": bool(gemini_key)
    }
    return jsonify(response)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)