from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk
# We remove the faulty import of ClerkError
import json

# Initialization
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
            # The dynamic URL logic from before remains correct.
            origin = request.headers.get('Origin')
            authorized_parties_json = os.getenv('AUTHORIZED_PARTIES_JSON')
            authorized_parties = json.loads(authorized_parties_json) if authorized_parties_json else []

            preview_pattern = "-greg-freeds-projects.vercel.app"

            if origin and preview_pattern in origin:
                claims = clerk.authenticate_request()
            else:
                claims = clerk.authenticate_request(authorized_parties=authorized_parties)
            
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # Database logic is unchanged.
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # User lookup/creation logic is unchanged
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

        # --- NEW ROBUST EXCEPTION HANDLING ---
        # This generic 'except' will not crash. It will instead help us diagnose.
        except Exception as e:
            # We will construct a detailed error message for our logs.
            error_details = {
                "message": "A critical error occurred during authentication.",
                # This line is the key: it tells us the real name of the exception class.
                "error_class_name": type(e).__name__, 
                "error_details": str(e),
            }
            # Print the detailed JSON to the Render logs.
            print(f"AUTHENTICATION EXCEPTION CAUGHT: {json.dumps(error_details)}")
            
            # Return a 401 so the frontend knows authentication failed.
            return jsonify(error_details), 401

        return f(*args, **kwargs)
    return decorated_function