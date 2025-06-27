from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2

# --- CORRECT: The one and only import needed from the library ---
from clerk_backend_api import Clerk

# --- Initialization ---
# This automatically reads the CLERK_SECRET_KEY from the environment.
clerk = Clerk()

# --- Database Connection ---
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

# --- Final token_required Decorator ---
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
            # 1. Verify the token using the correct method from the start.
            # This was the method used in your original file.
            claims = clerk.tokens.verify_token(session_token)
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # 2. Perform the critical database lookup logic.
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()

                if not user:
                    # User not found, must link or create.
                    clerk_user_info = clerk.users.get_user(user_id=clerk_user_id)
                    user_email = clerk_user_info.email_addresses[0].email_address

                    cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
                    user = cursor.fetchone()

                    if user:
                        # Pre-existing user found by email. Link them.
                        cursor.execute(
                            "UPDATE users SET clerk_user_id = %s WHERE id = %s RETURNING *;",
                            (clerk_user_id, user['id'])
                        )
                        user = cursor.fetchone()
                        conn.commit()
                    else:
                        # Brand new user. Create them.
                        cursor.execute(
                            "INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *;",
                            (clerk_user_id, user_email)
                        )
                        user = cursor.fetchone()
                        conn.commit()

                # 3. Attach the user from our database to the request.
                g.current_user = user
            conn.close()

        except Exception as e:
            # The library does not define a custom exception, so we catch the generic one.
            return jsonify({"message": "Authentication failed", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function