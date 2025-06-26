import os
import psycopg2
from psycopg2.extras import DictCursor
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import date

# Import the new security decorator
from auth import token_required

# --- Initialization ---
load_dotenv()
app = Flask(__name__)
CORS(app)

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key: raise ValueError("GEMINI_API_KEY not found...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    print("Flask app initialized and Gemini model loaded.")
except Exception as e:
    print(f"FATAL ERROR: Could not initialize Gemini model: {e}")
    model = None

# --- Database Connection Function ---
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set in .env file")
    return psycopg2.connect(db_url)

# --- Helper function to get user ID ---
def get_user_id(cursor, user_email):
    cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
    user_record = cursor.fetchone()
    return user_record[0] if user_record else None

# --- Existing API Endpoints ---
@app.route('/users/<user_email>/profile', methods=['GET'])
@token_required
def get_user_profile(user_email):
    print(f"\nReceived request to get profile for user: {user_email}")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "SELECT p.* FROM user_profiles p JOIN users u ON p.user_id = u.id WHERE u.email = %s"
            cursor.execute(sql, (user_email,))
            profile = cursor.fetchone()
            if not profile: return jsonify({"error": "Profile not found"}), 404
            return jsonify(dict(profile))
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/users/<user_email>/jobs', methods=['GET'])
@token_required
def get_user_jobs(user_email):
    print(f"\nReceived request to get saved jobs...")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # MODIFIED: Filter out junk company names
            excluded_companies = ['various', 'various companies', 'confidential']
            sql = "SELECT * FROM jobs WHERE LOWER(company_name) NOT IN %s ORDER BY found_at DESC LIMIT 50"
            cursor.execute(sql, (tuple(excluded_companies),))
            jobs = [dict(row) for row in cursor.fetchall()]
            return jsonify(jobs)
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/users/<user_email>/watchlist', methods=['GET'])
@token_required
def get_user_watchlist(user_email):
    print(f"\nReceived request to get watchlist for user: {user_email}")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            user_id = get_user_id(cursor, user_email)
            if not user_id: return jsonify({"error": "User not found"}), 404
            sql = "SELECT c.name, c.website, w.status, w.source FROM companies c JOIN user_company_watchlist w ON c.id = w.company_id WHERE w.user_id = %s"
            cursor.execute(sql, (user_id,))
            watchlist = [dict(row) for row in cursor.fetchall()]
            return jsonify(watchlist)
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/users/<user_email>/suggest-companies', methods=['POST'])
@token_required
def suggest_companies_for_user(user_email):
    print(f"\nReceived request to suggest companies for user: {user_email}")
    if model is None: return jsonify({"error": "Model is not available"}), 503
    return jsonify({"message": "This endpoint is a placeholder for now."}), 200

# --- Job Tracker API Endpoints ---

@app.route('/users/<user_email>/tracked-jobs', methods=['GET'])
@token_required
def get_tracked_jobs(user_email):
    print(f"\nReceived request to GET tracked jobs for {user_email}")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            user_id = get_user_id(cursor, user_email)
            if not user_id: return jsonify({"error": "User not found"}), 404
            sql = """
                SELECT j.*, t.status, t.notes, t.applied_at, t.id as tracked_job_id
                FROM jobs j JOIN tracked_jobs t ON j.id = t.job_id
                WHERE t.user_id = %s ORDER BY t.created_at DESC;
            """
            cursor.execute(sql, (user_id,))
            tracked_jobs = [dict(row) for row in cursor.fetchall()]
            return jsonify(tracked_jobs)
    except Exception as e:
        print(f"ERROR in get_tracked_jobs: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/users/<user_email>/tracked-jobs', methods=['POST'])
@token_required
def add_tracked_job(user_email):
    print(f"\nReceived request to POST new tracked job for {user_email}")
    data = request.get_json()
    job_id = data.get('job_id')
    if not job_id: return jsonify({"error": "job_id is required"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            user_id = get_user_id(cursor, user_email)
            if not user_id: return jsonify({"error": "User not found"}), 404
            sql = "INSERT INTO tracked_jobs (user_id, job_id) VALUES (%s, %s) ON CONFLICT (user_id, job_id) DO NOTHING"
            cursor.execute(sql, (user_id, job_id))
            conn.commit()
            return jsonify({"message": "Job tracked successfully"}), 201
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR in add_tracked_job: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/users/<user_email>/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(user_email, tracked_job_id):
    print(f"\nReceived request to PUT update for tracked job id {tracked_job_id}")
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            user_id = get_user_id(cursor, user_email)
            if not user_id: return jsonify({"error": "User not found"}), 404

            update_fields = []
            update_values = []
            
            if data.get('status') == 'Applied' and 'applied_at' not in data and not data.get('applied_at'):
                update_fields.append("applied_at = %s")
                update_values.append(date.today())
            
            if 'status' in data:
                update_fields.append("status = %s")
                update_values.append(data['status'])
            if 'notes' in data:
                update_fields.append("notes = %s")
                update_values.append(data['notes'])
            if 'applied_at' in data:
                applied_date = data['applied_at'] if data['applied_at'] else None
                update_fields.append("applied_at = %s")
                update_values.append(applied_date)

            if not update_fields:
                return jsonify({"error": "No update fields provided"}), 400

            update_values.extend([tracked_job_id, user_id])
            sql = f"UPDATE tracked_jobs SET {', '.join(update_fields)} WHERE id = %s AND user_id = %s"
            
            cursor.execute(sql, tuple(update_values))
            if cursor.rowcount == 0:
                return jsonify({"error": "Tracked job not found or permission denied"}), 404
            
            conn.commit()
            return jsonify({"message": "Tracked job updated successfully"}), 200
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR in update_tracked_job: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/users/<user_email>/tracked-jobs/<int:tracked_job_id>', methods=['DELETE'])
@token_required
def remove_tracked_job(user_email, tracked_job_id):
    """Removes a job from a user's tracker entirely."""
    print(f"\nReceived request to DELETE tracked job id {tracked_job_id}")
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            user_id = get_user_id(cursor, user_email)
            if not user_id: return jsonify({"error": "User not found"}), 404
            sql = "DELETE FROM tracked_jobs WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (tracked_job_id, user_id))
            if cursor.rowcount == 0:
                return jsonify({"error": "Tracked job not found or permission denied"}), 404
            conn.commit()
            return jsonify({"message": "Job removed from tracker"}), 200
    except Exception as e:
        if conn: conn.rollback()
        print(f"ERROR in remove_tracked_job: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)