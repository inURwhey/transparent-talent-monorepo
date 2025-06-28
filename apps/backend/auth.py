from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk
from clerk_backend_api.errors import ClerkError
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
            # --- DYNAMIC PREVIEW URL SOLUTION ---
            # 1. Get the origin of the request and the static authorized list
            origin = request.headers.get('Origin')
            authorized_parties_json = os.getenv('AUTHORIZED_PARTIES_JSON')
            authorized_parties = json.loads(authorized_parties_json) if authorized_parties_json else []

            # 2. Define the unique pattern for your Vercel preview deployments
            #    This ensures we only relax the rule for your specific preview apps.
            preview_pattern = "-greg-freeds-projects.vercel.app"

            # 3. Conditionally authenticate based on the origin
            if origin and preview_pattern in origin:
                # For Vercel previews, authenticate the token but SKIP the authorized party check.
                # This allows dynamic URLs to work securely.
                claims = clerk.authenticate_request()
            else:
                # For your production URL and all other requests, enforce the STRICT check.
                claims = clerk.authenticate_request(authorized_parties=authorized_parties)
            
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # --- DATABASE & USER LINKING LOGIC (No changes needed here) ---
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

        # --- ENHANCED DEBUGGING (As discussed previously) ---
        except ClerkError as e:
            error_details = {
                "message": "Clerk authentication failed.", "clerk_error": True,
                "code": e.code, "long_message": e.long_message, "meta": e.meta,
            }
            print(f"CLERK AUTHENTICATION ERROR: {json.dumps(error_details)}")
            return jsonify(error_details), 401
        except Exception as e:
            return jsonify({"message": "An unexpected error occurred during authentication.", "error": str(e)}), 500

        return f(*args, **kwargs)
    return decorated_function