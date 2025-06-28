import os
import psycopg2
from psycopg2.extras import DictCursor, Json
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import date
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json

from auth import token_required

# --- Initialization ---
load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True, expose_headers=["Authorization"])

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

# --- AI Helper Function ---
def run_job_analysis(job_description_text, user_profile_text):
    if not GEMINI_API_KEY:
        raise ValueError("AI analysis cannot be run without GEMINI_API_KEY.")
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    # *** FIX: Prompt now requests snake_case keys to match the database schema. ***
    prompt = f"""
        Analyze the following job description in the context of the provided user profile.
        Your output MUST be a single, minified JSON object with no extra text or markdown.

        USER PROFILE:
        ---
        {user_profile_text}
        ---

        JOB DESCRIPTION:
        ---
        {job_description_text}
        ---

        Based on "Protocol User-Driven Job Analysis v1.1", provide a comprehensive analysis.
        The JSON object must have the following snake_case keys:
        - "position_relevance_score": A number from 0-50.
        - "environment_fit_score": A number from 0-50.
        - "hiring_manager_view": A string, one of "Strong", "Possible", "Stretch", "Unlikely".
        - "matrix_rating": A string, one of "A", "B", "C", "D", "F".
        - "summary": A 2-4 sentence summary of the opportunity.
        - "qualification_gaps": An array of 2-3 strings listing key qualification gaps.
        - "recommended_testimonials": An array of 1-3 strings recommending impactful testimonials from the user's resume.
        - "job_title": The official job title from the description.
        - "company_name": The official company name from the description.
    """
    response = model.generate_content(prompt)
    cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
    return json.loads(cleaned_response_text)


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
                "desired_title", "non_negotiable_requirements", "deal_breakers"
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
                "deal_breakers": "Deal Breakers"
            }
            for col in profile_columns:
                value = user_profile_row[col]
                if value and str(value).strip():
                    user_profile_parts.append(f"- {profile_labels[col]}: {value}")

            if not user_profile_parts:
                return jsonify({"error": "User profile is too sparse. Please fill out your profile to enable analysis."}), 400
            
            user_profile_text = "\n".join(user_profile_parts)

            analysis_result = run_job_analysis(job_text, user_profile_text)
            
            # *** FIX: Use snake_case keys to access the AI analysis result. ***
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
                INSERT INTO jobs (company_id, company_name, job_title, job_url, source)
                VALUES (%s, %s, %s, %s, %s) ON CONFLICT (job_url) DO UPDATE SET
                company_id = EXCLUDED.company_id, company_name = EXCLUDED.company_name, job_title = EXCLUDED.job_title
                RETURNING id;
            """, (company_id, company_name, job_title, job_url, 'User Submission'))
            job_id = cursor.fetchone()['id']
            
            cursor.execute("""
                INSERT INTO job_analyses (job_id, position_relevance_score, environment_fit_score, hiring_manager_view, matrix_rating, summary, qualification_gaps, recommended_testimonials)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (job_id) DO NOTHING;
            """, (
                job_id, analysis_result.get('position_relevance_score'), analysis_result.get('environment_fit_score'),
                analysis_result.get('hiring_manager_view'), analysis_result.get('matrix_rating'),
                analysis_result.get('summary'), Json(analysis_result.get('qualification_gaps', [])),
                Json(analysis_result.get('recommended_testimonials', []))
            ))
            
            cursor.execute("INSERT INTO tracked_jobs (user_id, job_id, status) VALUES (%s, %s, %s) RETURNING id;", (user_id, job_id, 'Saved'))
            tracked_job_id = cursor.fetchone()['id']
            
            conn.commit()
            
            cursor.execute("""
                SELECT j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                       t.id as tracked_job_id, t.status, t.notes as user_notes, t.applied_at, t.created_at,
                       ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                       ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
                FROM jobs j JOIN tracked_jobs t ON j.id = t.job_id LEFT JOIN job_analyses ja ON j.id = ja.job_id
                WHERE t.id = %s;
            """, (tracked_job_id,))
            new_job_row = cursor.fetchone()
            
            response_data = {
                "job_id": new_job_row["job_id"], "company_name": new_job_row["company_name"],
                "job_title": new_job_row["job_title"], "job_url": new_job_row["job_url"],
                "source": new_job_row["source"], "found_at": new_job_row["found_at"],
                "tracked_job_id": new_job_row["tracked_job_id"], "status": new_job_row["status"],
                "user_notes": new_job_row["user_notes"], "applied_at": new_job_row["applied_at"],
                "created_at": new_job_row["created_at"],
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
        print(f"DATABASE ERROR in submit_job: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        if conn: conn.rollback()
        print(f"An unexpected error occurred in submit_job: {e}") 
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
            # Attempt to fetch the user profile
            sql = "SELECT * FROM user_profiles WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            profile = cursor.fetchone()
            
            # If no profile exists, create a new default one
            if not profile:
                print(f"No profile found for user_id {user_id}. Creating default profile.")
                insert_sql = """
                    INSERT INTO user_profiles (user_id) VALUES (%s)
                    RETURNING *;
                """
                cursor.execute(insert_sql, (user_id,))
                profile = cursor.fetchone() # Fetch the newly created profile
                conn.commit() # Commit the insert operation
            
            return jsonify(dict(profile))
    except Exception as e:
        print(f"ERROR in get_user_profile: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/jobs', methods=['GET'])
@token_required
def get_user_jobs():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            excluded_companies = ['various', 'various companies', 'confidential']
            sql = "SELECT id, company_name, job_title, job_url, source FROM jobs WHERE LOWER(company_name) NOT IN %s ORDER BY found_at DESC LIMIT 50"
            cursor.execute(sql, (tuple(excluded_companies),))
            jobs = [dict(row) for row in cursor.fetchall()]
            return jsonify(jobs)
    except Exception as e:
        print(f"ERROR in get_user_jobs: {str(e)}")
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
        limit = int(request.args.get('limit', 10)) # Default limit to 10 items per page
        if page < 1: page = 1
        if limit < 1: limit = 1
    except ValueError:
        return jsonify({"error": "Invalid pagination parameters"}), 400

    offset = (page - 1) * limit

    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # First, get the total count of jobs for the user
            cursor.execute("SELECT COUNT(*) FROM tracked_jobs WHERE user_id = %s;", (user_id,))
            total_count = cursor.fetchone()[0]

            sql = """
                SELECT 
                    j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                    t.id as tracked_job_id, t.status, t.notes as user_notes, t.applied_at, t.created_at,
                    ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                    ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
                FROM jobs j
                JOIN tracked_jobs t ON j.id = t.job_id
                LEFT JOIN job_analyses ja ON j.id = ja.job_id
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
                    "tracked_job_id": row["tracked_job_id"], "status": row["status"],
                    "user_notes": row["user_notes"], "applied_at": row["applied_at"],
                    "created_at": row["created_at"],
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
                "page": page, # Current page (1-indexed)
                "limit": limit # Items per page
            })
    except Exception as e:
        print(f"ERROR in get_tracked_jobs: {str(e)}")
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
                "INSERT INTO tracked_jobs (user_id, job_id, status) VALUES (%s, %s, %s) RETURNING id;",
                (user_id, job_id, 'Saved')
            )
            tracked_job_id = cursor.fetchone()[0]
            conn.commit()
        return jsonify({"message": "Job tracked successfully", "tracked_job_id": tracked_job_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(tracked_job_id):
    user_id = g.current_user['id']
    data = request.get_json()
    if not data or not any(key in data for key in ['status', 'notes', 'applied_at']):
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
            if not fields:
                return jsonify({"error": "No valid fields to update"}), 400
            sql = f"UPDATE tracked_jobs SET {', '.join(fields)} WHERE id = %s RETURNING *"
            params.append(tracked_job_id)
            cursor.execute(sql, tuple(params))
            updated_job = dict(cursor.fetchone())
            conn.commit()
            return jsonify(updated_job)
    except Exception as e:
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
        return jsonify({"error": str(e)}), 500
    finally:
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