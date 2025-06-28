from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk
import json

# The Clerk() constructor automatically finds the CLERK_SECRET_KEY from the environment.
clerk = Clerk()

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # This is the simplest, most direct way to use the library with Flask.
            # It uses the Flask request object and relies on the dashboard for all other settings.
            # It does not require the 'options' parameter that was causing the crash.
            claims = clerk.authenticate_request(request)
            
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # --- Database logic is correct and unchanged ---
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()
                if not user:
                    clerk_user_info = clerk.users.get_user(user_id=clerk_user_id)
                    user_email = clerk_user_info.email_addresses[0].email_address
                    cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
                    user = cursor.fetchone()
                    if user:
                        cursor.execute("UPDATE users SET clerk_user_id = %s WHERE id = %s RETURNING *;", (clerk_user_id, user['id']))
                        user = cursor.fetchone()
                        conn.commit()
                    else:
                        cursor.execute("INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *;", (clerk_user_id, user_email))
                        user = cursor.fetchone()
                        conn.commit()
                g.current_user = user
            conn.close()

        except Exception as e:
            error_details = {
                "message": "A critical error occurred during authentication.",
                "error_class_name": type(e).__name__, 
                "error_details": str(e),
            }
            print(f"AUTHENTICATION EXCEPTION CAUGHT: {json.dumps(error_details)}")
            return jsonify(error_details), 401

        return f(*args, **kwargs)
    return decorated_function