from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
import json
import requests
import jwt
from jwt import PyJWKClient

# This is now the only Clerk-related URL we need.
ISSUER_URL = os.getenv('CLERK_ISSUER_URL')
jwks_client = PyJWKClient(f"{ISSUER_URL}/.well-known/jwks.json")

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

def get_clerk_user_info(clerk_user_id):
    """
    Fetches user details from the Clerk API using the secret key.
    This is necessary to get the user's email for our database logic.
    """
    clerk_secret_key = os.getenv('CLERK_SECRET_KEY')
    api_url = f"https://api.clerk.com/v1/users/{clerk_user_id}"
    headers = {'Authorization': f'Bearer {clerk_secret_key}'}
    
    response = requests.get(api_url, headers=headers)
    response.raise_for_status() # Will raise an exception for 4xx/5xx errors
    
    clerk_user = response.json()
    primary_email_id = clerk_user.get("primary_email_address_id")
    for email in clerk_user.get("email_addresses", []):
        if email.get("id") == primary_email_id:
            return email.get("email_address")
    return None # Fallback

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"message": "Authorization header is missing or invalid"}), 401
            
            token = auth_header.split(' ')[1]

            # Get the signing key from the JWKS endpoint
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and verify the token using the public key
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=ISSUER_URL,
                audience="https://transparenttalent.onrender.com" # You may need to adjust this
            )
            
            clerk_user_id = claims.get('sub')
            if not clerk_user_id:
                return jsonify({"message": "Invalid token: missing user ID (sub) claim"}), 401
            
            # --- Database logic for user lookup/creation ---
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()
                if not user:
                    user_email = get_clerk_user_info(clerk_user_id)
                    if not user_email:
                        return jsonify({"message": "Could not retrieve user email from Clerk"}), 500

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

        except jwt.exceptions.PyJWTError as e:
            return jsonify({"message": f"Token is invalid: {str(e)}"}), 401
        except Exception as e:
            error_details = {
                "message": "Authentication failed during execution.",
                "error_class_name": type(e).__name__, 
                "error_details": str(e),
            }
            print(f"AUTHENTICATION EXCEPTION CAUGHT: {json.dumps(error_details)}")
            return jsonify(error_details), 500

        return f(*args, **kwargs)
    return decorated_function