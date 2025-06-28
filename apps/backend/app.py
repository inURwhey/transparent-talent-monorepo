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
    """
    Executes Protocol User-Driven Job Analysis v1.1.
    """
    if not GEMINI_API_KEY:
        raise ValueError("AI analysis cannot be run without GEMINI_API_KEY.")

    model = genai.GenerativeModel('gemini-1.5-pro-latest')

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
        The JSON object must have the following keys:
        - "positionRelevanceScore": A number from 0-50.
        - "environmentFitScore": A number from 0-50.
        - "hiringManagerView": A string, one of "Strong", "Possible", "Stretch", "Unlikely".
        - "matrixRating": A string, one of "A", "B", "C", "D", "F".
        - "summary": A 2-4 sentence summary of the opportunity.
        - "qualificationGaps": An array of 2-3 strings listing key qualification gaps.
        - "recommendedTestimonials": An array of 1-3 strings recommending impactful testimonials from the user's resume.
        - "jobTitle": The official job title from the description.
        - "companyName": The official company name from the description.
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

            cursor.execute("SELECT summary FROM user_profiles WHERE user_id = %s", (user_id,))
            user_profile_row = cursor.fetchone()
            if not user_profile_row or not user_profile_row['summary']:
                return jsonify({"error": "User profile summary not found or is empty. Cannot perform analysis."}), 404
            user_profile_text = user_profile_row['summary']

            analysis_result = run_job_analysis(job_text, user_profile_text)
            company_name = analysis_result.get('companyName', 'Unknown Company')
            job_title = analysis_result.get('jobTitle', 'Unknown Title')

            cursor.execute("SELECT id FROM companies WHERE LOWER(name) = LOWER(%s)", (company_name,))
            company_row = cursor.fetchone()
            company_id = company_row['id'] if company_row else cursor.execute("INSERT INTO companies (name) VALUES (%s) RETURNING id", (company_name,)).fetchone()['id']

            cursor.execute("""
                INSERT INTO jobs (company_id, company_name, job_title, job_url, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (job_url) DO UPDATE SET
                    company_id = EXCLUDED.company_id,
                    company_name = EXCLUDED.company_name,
                    job_title = EXCLUDED.job_title
                RETURNING id;
            """, (company_id, company_name, job_title, job_url, 'User Submission'))
            job_id = cursor.fetchone()['id']

            cursor.execute("""
                INSERT INTO job_analyses (job_id, position_relevance_score, environment_fit_score, hiring_manager_view, matrix_rating, summary, qualification_gaps, recommended_testimonials)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (job_id) DO NOTHING;
            """, (
                job_id,
                analysis_result.get('positionRelevanceScore'),
                analysis_result.get('environmentFitScore'),
                analysis_result.get('hiringManagerView'),
                analysis_result.get('matrixRating'),
                analysis_result.get('summary'),
                Json(analysis_result.get('qualificationGaps', [])),
                Json(analysis_result.get('recommendedTestimonials', []))
            ))

            cursor.execute("INSERT INTO tracked_jobs (user_id, job_id, status) VALUES (%s, %s, %s) RETURNING id;", (user_id, job_id, 'Saved'))
            tracked_job_id = cursor.fetchone()['id']
            
            conn.commit()

            cursor.execute("""
                SELECT 
                    j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                    t.id as tracked_job_id, t.status, t.notes as user_notes, t.applied_at,
                    ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                    ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
                FROM jobs j
                JOIN tracked_jobs t ON j.id = t.job_id
                LEFT JOIN job_analyses ja ON j.id = ja.job_id
                WHERE t.id = %s;
            """, (tracked_job_id,))
            new_job_row = cursor.fetchone()
            
            # Structure the response consistently
            response_data = {
                "job_id": new_job_row["job_id"], "company_name": new_job_row["company_name"],
                "job_title": new_job_row["job_title"], "job_url": new_job_row["job_url"],
                "source": new_job_row["source"], "found_at": new_job_row["found_at"],
                "tracked_job_id": new_job_row["tracked_job_id"], "status": new_job_row["status"],
                "user_notes": new_job_row["user_notes"], "applied_at": new_job_row["applied_at"],
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
    except Exception as e:
        if conn: conn.rollback()
        print(f"An unexpected error occurred: {e}") 
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
            sql = "SELECT id, user_id, full_name, headline, summary FROM user_profiles WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            profile = cursor.fetchone()
            if not profile: return jsonify({"error": "Profile not found"}), 404
            return jsonify(dict(profile))
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally: conn.close()

@app.route('/api/jobs', methods=['GET'])
@token_required
def get_user_jobs():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            excluded_companies = ['various', 'various companies', 'confidential']
            sql = "SELECT * FROM jobs WHERE LOWER(company_name) NOT IN %s ORDER BY found_at DESC LIMIT 50"
            cursor.execute(sql, (tuple(excluded_companies),))
            jobs = [dict(row) for row in cursor.fetchall()]
            return jsonify(jobs)
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally: conn.close()

@app.route('/api/tracked-jobs', methods=['GET'])
@token_required
def get_tracked_jobs():
    user_id = g.current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = """
                SELECT 
                    j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.notes, j.found_at,
                    t.id as tracked_job_id, t.status, t.notes as user_notes, t.applied_at,
                    ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                    ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
                FROM jobs j
                JOIN tracked_jobs t ON j.id = t.job_id
                LEFT JOIN job_analyses ja ON j.id = ja.job_id
                WHERE t.user_id = %s ORDER BY t.created_at DESC;
            """
            cursor.execute(sql, (user_id,))
            
            tracked_jobs = []
            for row in cursor.fetchall():
                job = {
                    "job_id": row["job_id"], "company_name": row["company_name"],
                    "job_title": row["job_title"], "job_url": row["job_url"],
                    "source": row["source"], "found_at": row["found_at"],
                    "tracked_job_id": row["tracked_job_id"], "status": row["status"],
                    "user_notes": row["user_notes"], "applied_at": row["applied_at"],
                    "ai_analysis": None
                }
                # If analysis exists, populate it
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

            return jsonify(tracked_jobs)
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally: conn.close()

# Other endpoints...
@app.route('/api/tracked-jobs', methods=['POST'])
@token_required
def add_tracked_job():
    # ... (code for this function is unchanged)
    pass 

@app.route('/api/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(tracked_job_id):
    # ... (code for this function is unchanged)
    pass

@app.route('/api/tracked-jobs/<int:tracked_job_id>', methods=['DELETE'])
@token_required
def remove_tracked_job(tracked_job_id):
    # ... (code for this function is unchanged)
    pass


# --- NEW DIAGNOSTIC ENDPOINT ---
@app.route('/api/debug-env', methods=['GET'])
def debug_env():
    clerk_key = os.getenv('CLERK_SECRET_KEY')
    db_url = os.getenv('DATABASE_URL')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    response = {
        "clerk_key_is_set": bool(clerk_key),
        "clerk_key_preview": f"{clerk_key[:5]}...{clerk_key[-4:]}" if clerk_key else "Not Set",
        "db_url_is_set": bool(db_url),
        "gemini_key_is_set": bool(gemini_key)
    }
    return jsonify(response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)