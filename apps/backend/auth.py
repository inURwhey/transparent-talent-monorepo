from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk
import json

# Initialize the clerk client. It will read the secret key from the environment.
clerk = Clerk()

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"message": "Authorization header is missing or invalid"}), 401
        
        token = auth_header.split(' ')[1]

        try:
            # Reverting to the simpler, more direct token verification method
            # that was present in your earlier commits. This avoids the problematic
            # authenticate_request method entirely.
            claims = clerk.tokens.verify_token(token)
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID (sub) claim"}), 401
            
            # This is the correct database logic you wrote, combined with the
            # simpler verification method.
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()
                # This block handles user creation on first login
                if not user:
                    # We must use the clerk object to get the user's email from their ID
                    clerk_user_info = Clerk().users.get_user(user_id=clerk_user_id)
                    user_email = clerk_user_info.email_addresses[0].email_address
                    
                    # Check if a user with that email already exists from a pre-Clerk system
                    cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
                    user = cursor.fetchone()
                    
                    if user:
                        # If they exist, link their account to their Clerk ID
                        cursor.execute("UPDATE users SET clerk_user_id = %s WHERE id = %s RETURNING *;", (clerk_user_id, user['id']))
                        user = cursor.fetchone()
                        conn.commit()
                    else:
                        # If they are a brand new user, create a new record
                        cursor.execute("INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *;", (clerk_user_id, user_email))
                        user = cursor.fetchone()
                        conn.commit()
                
                # Attach the full user record to the request context
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