# Path: apps/backend/auth.py
import os
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

            authorized_party = claims.get('azp')
            if not authorized_party or authorized_party not in config.CLERK_AUTHORIZED_PARTY:
                raise jwt.exceptions.InvalidAudienceError(f"Invalid authorized party: {authorized_party}")
            
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
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during token validation: {e}")
            return jsonify({"message": "An unexpected error occurred during token validation."}), 500
        
        return f(*args, **kwargs)
    return decorated