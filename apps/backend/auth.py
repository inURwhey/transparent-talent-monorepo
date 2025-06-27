from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk

clerk = Clerk()

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print("\n--- AUTH decorator starting ---")
        session_token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header.split(' ')[1]

        if not session_token:
            print("ERROR: Auth token is missing.")
            return jsonify({"message": "Authentication token is missing"}), 401

        try:
            print("1. Verifying token...")
            claims = clerk.tokens.verify_token(session_token)
            clerk_user_id = claims.get('sub')
            print(f"2. Token verified. Clerk User ID: {clerk_user_id}")
            
            if not clerk_user_id:
                print("ERROR: Clerk User ID missing from token.")
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            print("3. Connecting to database...")
            conn = get_db_connection()
            print("4. Database connected.")
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                print(f"5. Looking up user by clerk_user_id: {clerk_user_id}")
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()

                if not user:
                    print("6a. User not found by clerk_id. Attempting to link...")
                    clerk_user_info = clerk.users.get_user(user_id=clerk_user_id)
                    user_email = clerk_user_info.email_addresses[0].email_address
                    print(f"6b. Found email {user_email} from Clerk. Searching in DB...")
                    
                    cursor.execute("SELECT * FROM users WHERE email = %s", (user_email,))
                    user = cursor.fetchone()

                    if user:
                        print("6c. User found by email. Linking account now.")
                        cursor.execute("UPDATE users SET clerk_user_id = %s WHERE id = %s RETURNING *;", (clerk_user_id, user['id']))
                        user = cursor.fetchone()
                        conn.commit()
                    else:
                        print("6d. No user found. Creating new user record.")
                        cursor.execute("INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *;", (clerk_user_id, user_email))
                        user = cursor.fetchone()
                        conn.commit()
                else:
                    print("6. User found in database.")

                if not user:
                     print("CRITICAL ERROR: User object is NULL after all checks.")
                     return jsonify({"message": "Could not find or create a user"}), 500

                print(f"7. Attaching user to request context: {dict(user)}")
                g.current_user = user
            
            conn.close()
            print("8. DB connection closed. Decorator finished successfully.")

        except Exception as e:
            print(f"\n--- AUTH DECORATOR FAILED ---")
            print(f"Exception Type: {type(e).__name__}")
            print(f"Exception Details: {e}")
            return jsonify({"message": "Authentication failed", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function