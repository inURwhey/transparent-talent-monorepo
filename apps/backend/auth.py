from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk
import json

# Initialize the clerk client using the Issuer URL from the environment.
# This allows the SDK to find the public keys at the JWKS endpoint and verify the token.
clerk = Clerk(
    issuer=os.getenv('CLERK_ISSUER_URL'),
    secret_key=os.getenv('CLERK_SECRET_KEY')
)

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # The authenticate_request method is the correct one to use.
            # Now that the clerk object is fully configured with the issuer,
            # it has all the information it needs to validate the request.
            request_state = clerk.authenticate_request(request)
            
            if not request_state.is_signed_in:
                 return jsonify({"message": "Not signed in"}), 401

            claims = request_state.to_claims()
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID (sub) claim"}), 401
            
            # --- Database logic for user lookup/creation is correct ---
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
                "message": "Authentication failed.",
                "error_class_name": type(e).__name__, 
                "error_details": str(e),
            }
            print(f"AUTHENTICATION EXCEPTION CAUGHT: {json.dumps(error_details)}")
            return jsonify(error_details), 401

        return f(*args, **kwargs)
    return decorated_function