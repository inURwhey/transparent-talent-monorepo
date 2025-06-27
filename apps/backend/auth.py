from flask import request, jsonify, g
from functools import wraps
from clerk_backend_api import Clerk
from psycopg2.extras import DictCursor
import os
import psycopg2

# --- Initialization ---
clerk = Clerk()

# --- Database Connection (needed for user lookup) ---
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

# --- The Enhanced Decorator ---
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
            # 1. Verify the token with Clerk
            claims = clerk.tokens.verify_token(session_token)
            clerk_user_id = claims.get('sub') # 'sub' is the standard claim for subject/user ID
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # 2. Find or create the user in our database
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                # Find user by Clerk ID
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()

                # If user not found by clerk_id, this is a first-time login or a pre-existing user.
                if not user:
                    # Get user info from Clerk to find them by email
                    clerk_user_info = clerk.users.get_user(user_id=clerk_user_id)
                    user_email = clerk_user_info.email_addresses[0].email_address

                    # Try to find user by email to link the account
                    cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
                    user = cursor.fetchone()

                    if user:
                        # User exists, link account by adding clerk_user_id
                        cursor.execute(
                            "UPDATE users SET clerk_user_id = %s WHERE id = %s RETURNING *;",
                            (clerk_user_id, user['id'])
                        )
                        user = cursor.fetchone()
                        conn.commit()
                    else:
                        # This is a brand new user. Create a record.
                        cursor.execute(
                            "INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *;",
                            (clerk_user_id, user_email)
                        )
                        user = cursor.fetchone()
                        conn.commit()
                        # NOTE: You'll also need to create an associated user_profile record here
                        # For now, this is sufficient to get the dashboard working.
                
                # 3. Attach the authenticated user to the request context
                g.current_user = user

            conn.close()

        except Exception as e:
            return jsonify({"message": "Authentication token is invalid or user lookup failed", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function