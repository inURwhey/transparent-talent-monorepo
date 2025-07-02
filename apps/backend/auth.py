# Path: apps/backend/auth.py
import os
import re
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from jwt.algorithms import RSAAlgorithm
import requests
from .config import config
from .database import get_db

def get_jwks():
    jwks_url = f"{config.CLERK_ISSUER_URL}/.well-known/jwks.json"
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to fetch JWKS: {e}")
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers['Authorization'].split(" ")[1] if 'Authorization' in request.headers else None
        if not token: return jsonify({"message": "Token is missing!"}), 401
        
        jwks = get_jwks()
        if not jwks: return jsonify({"message": "Could not fetch JWKS for token validation."}), 500

        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
            if not rsa_key: raise jwt.exceptions.InvalidKeyError("Public key not found in JWKS.")
            
            public_key = RSAAlgorithm.from_jwk(rsa_key)
            claims = jwt.decode(token, public_key, algorithms=["RS256"], issuer=config.CLERK_ISSUER_URL, options={"verify_aud": False})

            # --- REVERTED AZP CHECK ---
            # Reverting to the simpler, ground-truth logic provided by the user.
            authorized_party = claims.get('azp')
            if not authorized_party or authorized_party not in config.CLERK_AUTHORIZED_PARTY:
                current_app.logger.warning(f"JWT validation failed: Invalid authorized party (azp): {authorized_party}")
                raise jwt.exceptions.InvalidAudienceError(f"Invalid authorized party: {authorized_party}")
            # --- END OF REVERTED LOGIC ---
            
            clerk_user_id = claims.get('sub')
            if not clerk_user_id: raise Exception("Token is missing 'sub' (subject) claim.")
            
            db = get_db()
            with db.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()
                
                if user:
                    g.current_user = user
                else:
                    current_app.logger.info(f"First-time user with Clerk ID {clerk_user_id}. Creating new user record.")
                    email = claims.get('primary_email') or claims.get('email')
                    
                    cursor.execute(
                        "INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *",
                        (clerk_user_id, email)
                    )
                    new_user = cursor.fetchone()
                    g.current_user = new_user
                    db.commit()

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.exceptions.InvalidAudienceError as e:
            return jsonify({"message": f"JWT validation failed: {e}"}), 401
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during token validation: {e}")
            return jsonify({"message": "An unexpected error occurred during token validation."}), 500
        
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """
    A decorator to ensure the user is an admin.
    Must be used *after* @token_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(config, 'CLERK_ADMIN_USER_IDS') or not config.CLERK_ADMIN_USER_IDS:
            current_app.logger.error("CLERK_ADMIN_USER_IDS is not set in the configuration.")
            return jsonify({"message": "Server configuration error: Admin list not set."}), 500

        admin_ids = [id.strip() for id in config.CLERK_ADMIN_USER_IDS.split(',')]
        
        user_clerk_id = g.current_user.get('clerk_user_id') if hasattr(g, 'current_user') and g.current_user else None
        
        if not user_clerk_id or user_clerk_id not in admin_ids:
            return jsonify({"message": "Admin access required."}), 403
            
        return f(*args, **kwargs)
    return decorated