import os
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, request, jsonify, g
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import date

from auth import token_required

# --- Initialization ---
load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True, expose_headers=["Authorization"])

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url: raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(db_url)

# --- Existing API Endpoints (Unchanged) ---
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
                SELECT j.*, t.status, t.notes, t.applied_at, t.id as tracked_job_id
                FROM jobs j JOIN tracked_jobs t ON j.id = t.job_id
                WHERE t.user_id = %s ORDER BY t.created_at DESC;
            """
            cursor.execute(sql, (user_id,))
            tracked_jobs = [dict(row) for row in cursor.fetchall()]
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
    
    response = {
        "clerk_key_is_set": bool(clerk_key),
        "clerk_key_preview": f"{clerk_key[:5]}...{clerk_key[-4:]}" if clerk_key else "Not Set",
        "db_url_is_set": bool(db_url),
    }
    return jsonify(response)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)