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
    # ... (code for this function is unchanged)
    pass

# --- API Endpoints ---

@app.route('/api/jobs/submit', methods=['POST'])
@token_required
def submit_job():
    # ... (code for this function is unchanged)
    pass

@app.route('/api/profile', methods=['GET'])
@token_required
def get_user_profile():
    user_id = g.current_user['id']
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # *** THE FIX IS HERE ***
            # The query now selects the specific fields required by the frontend component.
            sql = "SELECT full_name, short_term_career_goal FROM user_profiles WHERE user_id = %s"
            cursor.execute(sql, (user_id,))
            profile = cursor.fetchone()
            if not profile: return jsonify({"error": "Profile not found"}), 404
            return jsonify(dict(profile))
    except Exception as e:
        # Added more specific logging for this error
        print(f"ERROR in get_user_profile: {str(e)}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/jobs', methods=['GET'])
@token_required
def get_user_jobs():
    # ... (code for this function is unchanged)
    pass

@app.route('/api/tracked-jobs', methods=['GET'])
@token_required
def get_tracked_jobs():
    # ... (code for this function is unchanged)
    pass

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
    # ... (code for this function is unchanged)
    pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)