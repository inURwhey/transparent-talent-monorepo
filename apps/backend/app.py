import os
import psycopg2
from psycopg2.extras import DictCursor
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import google.generativeai as genai
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

# --- REFACTORED API Endpoints ---
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

@app.route('/api/watchlist', methods=['GET'])
@token_required
def get_user_watchlist():
    user_id = g.current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "SELECT c.name, c.website, w.status, w.source FROM companies c JOIN user_company_watchlist w ON c.id = w.company_id WHERE w.user_id = %s"
            cursor.execute(sql, (user_id,))
            watchlist = [dict(row) for row in cursor.fetchall()]
            return jsonify(watchlist)
    except Exception as e: return jsonify({"error": str(e)}), 500
    finally: conn.close()

# --- Job Tracker API Endpoints ---
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

@app.route('/api/tracked-jobs', methods=['POST'])
@token_required
def add_tracked_job():
    user_id = g.current_user['id']
    data = request.get_json()
    job_id = data.get('job_id')
    if not job_id: return jsonify({"error": "job_id is required"}), 400
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "INSERT INTO tracked_jobs (user_id, job_id) VALUES (%s, %s) ON CONFLICT (user_id, job_id) DO NOTHING"
            cursor.execute(sql, (user_id, job_id))
            conn.commit()
            return jsonify({"message": "Job tracked successfully"}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally: conn.close()

# *** THE FIX IS HERE ***
@app.route('/api/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(tracked_job_id):
    user_id = g.current_user['id'] # Was g.current__user['id']
    data = request.get_json()
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            update_fields, update_values = [], []
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
                update_fields.append("applied_at = %s")
                update_values.append(data['applied_at'] or None)
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
        return jsonify({"error": str(e)}), 500
    finally: conn.close()

@app.route('/api/tracked-jobs/<int:tracked_job_id>', methods=['DELETE'])
@token_required
def remove_tracked_job(tracked_job_id):
    user_id = g.current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "DELETE FROM tracked_jobs WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (tracked_job_id, user_id))
            if cursor.rowcount == 0:
                return jsonify({"error": "Tracked job not found or permission denied"}), 404
            conn.commit()
            return jsonify({"message": "Job removed from tracker"}), 200
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally: conn.close()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)