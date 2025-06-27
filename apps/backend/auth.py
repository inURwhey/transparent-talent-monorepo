from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2

# --- CORRECT: Import the official Clerk client ---
# As per the official documentation
from clerk_backend_api import Clerk 
from clerk_backend_api.errors import ClerkAPIException
from clerk_backend_api.jwks_helpers import verify_jwt

# --- Initialization with the official client ---
# It automatically reads the CLERK_SECRET_KEY from the environment.
clerk = Clerk()

# --- Database Connection ---
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

# --- The Verifiably Correct token_required Decorator ---
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header.split(' ')[1]

        if not session_token:
            return jsonify({"message": "Authentication token is missing"}), 401

        try:
            # 1. Verify the token using the official library's method
            # This returns a claims dictionary upon successful verification.
            claims = verify_jwt(session_token)
            clerk_user_id = claims.get('sub') # 'sub' is the standard claim for subject/user ID
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # 2. Find or create the user in our database
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()

                if not user:
                    # To get user email, we must use the Clerk API as the token doesn't contain it by default.
                    clerk_user_info = clerk.users.get_user(user_id=clerk_user_id)
                    user_email = clerk_user_info.email_addresses[0].email_address

                    cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
                    user = cursor.fetchone()

                    if user:
                        # Pre-existing user found by email. Link the account.
                        cursor.execute(
                            "UPDATE users SET clerk_user_id = %s WHERE id = %s RETURNING *;",
                            (clerk_user_id, user['id'])
                        )
                        user = cursor.fetchone()
                        conn.commit()
                    else:
                        # This is a brand new user. Create a new record.
                        cursor.execute(
                            "INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *;",
                            (clerk_user_id, user_email)
                        )
                        user = cursor.fetchone()
                        conn.commit()

                # 3. Attach the authenticated user from OUR database to the request context
                g.current_user = user

            conn.close()

        except ClerkAPIException as e:
            return jsonify({"message": "Clerk Authentication Error", "error": str(e)}), 401
        except Exception as e:
            return jsonify({"message": "Authentication failed during user lookup", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function