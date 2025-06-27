from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk

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
            # --- THE FINAL, CORRECT METHOD CALL BASED ON THE LOGS ---
            # 1. Call the method with the two arguments the error message demanded.
            # We pass the Flask `request` object and an empty dictionary for `options`.
            claims = clerk.authenticate_request(request, {})
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            # 2. Perform the database lookup and user linking logic.
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
            return jsonify({"message": "Authentication failed", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function