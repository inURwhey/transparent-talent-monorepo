from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2

# --- NEW: Import the official Clerk client ---
from clerk_client import ClerkClient
from clerk_client.errors import ClerkAPIException

# --- Initialization with the official client ---
# It automatically reads the CLERK_SECRET_KEY from the environment.
clerk_client = ClerkClient()

# --- Database Connection ---
def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

# --- The Definitive token_required Decorator ---
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
            # 1. Verify the token using the official client's method
            # This returns a rich object with user details if valid.
            interstitial = clerk_client.interstitial.from_jwt(session_token)
            clerk_user_id = interstitial.user.id
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # 2. Find or create the user in our database
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()

                if not user:
                    # User not found by clerk_id. Try to link or create.
                    # The user's email is included in the token data, no extra API call needed!
                    user_email = interstitial.user.email_addresses[0].email_address

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
                        # NOTE: A new user_profile should be created here as a follow-up task.

                # 3. Attach the authenticated user from OUR database to the request context
                g.current_user = user

            conn.close()

        except ClerkAPIException as e:
            return jsonify({"message": "Clerk Authentication Error", "error": str(e)}), 401
        except Exception as e:
            # Catches database errors or other issues
            return jsonify({"message": "Authentication failed during user lookup", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function