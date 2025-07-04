# Path: apps/backend/auth.py
import os
import re
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from jwt.algorithms import RSAAlgorithm
import requests

# CORRECTED IMPORT: Import the SQLAlchemy instance from the app.py within the same package
from .app import db
from .models import User # Import the User model

from .config import config

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
        token = request.headers.get('Authorization', '').split(" ")[1] if 'Authorization' in request.headers else None
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        
        jwks = get_jwks()
        if not jwks:
            return jsonify({"message": "Could not fetch JWKS for token validation."}), 500

        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
            if not rsa_key:
                raise jwt.exceptions.InvalidKeyError("Public key not found in JWKS.")
            
            public_key = RSAAlgorithm.from_jwk(rsa_key)
            claims = jwt.decode(token, public_key, algorithms=["RS256"], issuer=config.CLERK_ISSUER_URL, options={"verify_aud": False})

            authorized_party = claims.get('azp')
            # Assuming CLERK_AUTHORIZED_PARTY can be a list or a string of comma-separated URLs
            allowed_azp_regexes = [re.compile(pattern) for pattern in config.CLERK_AUTHORIZED_PARTY]
            
            is_azp_allowed = False
            for pattern in allowed_azp_regexes:
                if pattern.match(authorized_party):
                    is_azp_allowed = True
                    break

            if not is_azp_allowed:
                current_app.logger.warning(f"JWT validation failed: Invalid authorized party (azp): {authorized_party}")
                raise jwt.exceptions.InvalidAudienceError(f"Invalid authorized party: {authorized_party}")
            
            clerk_user_id = claims.get('sub')
            if not clerk_user_id:
                raise Exception("Token is missing 'sub' (subject) claim.")
            
            # --- START SQLAlchemy DB INTERACTION ---
            user = User.query.filter_by(clerk_user_id=clerk_user_id).first()
            
            if user:
                g.current_user = user
            else:
                current_app.logger.info(f"First-time user with Clerk ID {clerk_user_id}. Creating new user record.")
                email = claims.get('primary_email') or claims.get('email')
                
                new_user = User(clerk_user_id=clerk_user_id, email=email)
                db.session.add(new_user)
                db.session.commit() # Commit the new user to get their ID
                db.session.refresh(new_user) # Refresh to get the ID and other defaults
                g.current_user = new_user

        except jwt.ExpiredSignatureError:
            db.session.rollback() # Rollback any pending transactions
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.exceptions.InvalidAudienceError as e:
            db.session.rollback()
            return jsonify({"message": f"JWT validation failed: {e}"}), 401
        except Exception as e:
            db.session.rollback() # Ensure rollback on any unexpected error
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
        
        # Access clerk_user_id directly from the User object
        user_clerk_id = g.current_user.clerk_user_id if hasattr(g, 'current_user') and g.current_user else None
        
        # --- DEBUGGING LOGS ---
        current_app.logger.info(f"Admin Check: User Clerk ID is '{user_clerk_id}' (Type: {type(user_clerk_id)})")
        current_app.logger.info(f"Admin Check: Admin ID list is {admin_ids} (Types: {[type(i) for i in admin_ids]})")
        
        if not user_clerk_id or user_clerk_id not in admin_ids:
            current_app.logger.warning(f"Admin access DENIED for user '{user_clerk_id}'. Not in admin list.")
            return jsonify({"message": "Admin access required."}), 403
        
        current_app.logger.info(f"Admin access GRANTED for user '{user_clerk_id}'.")
        return f(*args, **kwargs)
    return decorated