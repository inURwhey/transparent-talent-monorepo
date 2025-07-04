# Path: apps/backend/auth.py
import os
import re
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from jwt.algorithms import RSAAlgorithm
import requests

from .app import db
from .models import User
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
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"message": "Authorization header is missing or malformed."}), 401
        
        token = auth_header.split(" ")[1]
        
        jwks = get_jwks()
        if not jwks:
            return jsonify({"message": "Could not fetch JWKS for token validation."}), 500

        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = next((key for key in jwks["keys"] if key["kid"] == unverified_header["kid"]), None)
            if not rsa_key:
                raise jwt.exceptions.InvalidKeyError("Public key not found in JWKS.")
            
            public_key = RSAAlgorithm.from_jwk(rsa_key)
            
            # This will also validate 'exp' and 'iss' claims
            claims = jwt.decode(token, public_key, algorithms=["RS256"], issuer=config.CLERK_ISSUER_URL, options={"verify_aud": False})

            authorized_party = claims.get('azp')
            is_azp_allowed = False
            for pattern_str in config.CLERK_AUTHORIZED_PARTY:
                if re.match(pattern_str, authorized_party):
                    is_azp_allowed = True
                    break

            if not is_azp_allowed:
                raise jwt.exceptions.InvalidAudienceError(f"Invalid authorized party: {authorized_party}")
            
            clerk_user_id = claims.get('sub')
            if not clerk_user_id:
                raise Exception("Token is missing 'sub' (subject) claim.")
            
            user = User.query.filter_by(clerk_user_id=clerk_user_id).first()
            
            if not user:
                current_app.logger.info(f"First-time user with Clerk ID {clerk_user_id}. Creating new user record.")
                email = claims.get('primary_email') or claims.get('email')
                user = User(clerk_user_id=clerk_user_id, email=email)
                db.session.add(user)
                db.session.commit()
            
            g.current_user = user

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.PyJWTError as e: # Catch specific JWT errors
            return jsonify({"message": f"JWT validation failed: {e}"}), 401
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"An unexpected error occurred during token validation: {e}", exc_info=True)
            return jsonify({"message": "An unexpected error occurred during token validation."}), 500
        
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # This decorator must be used after @token_required, so g.current_user is guaranteed to exist.
        if not hasattr(g, 'current_user'):
             return jsonify({"message": "Authentication context not found."}), 500

        admin_ids_str = config.CLERK_ADMIN_USER_IDS
        if not admin_ids_str:
            current_app.logger.error("CLERK_ADMIN_USER_IDS is not set in the configuration.")
            return jsonify({"message": "Server configuration error: Admin list not set."}), 500

        admin_ids = {admin_id.strip() for admin_id in admin_ids_str.split(',')}
        
        # CORRECTED: Safely get clerk_user_id from the SQLAlchemy object
        user_clerk_id = str(g.current_user.clerk_user_id)

        if user_clerk_id not in admin_ids:
            current_app.logger.warning(f"Admin access DENIED for user '{user_clerk_id}'. Not in admin list {admin_ids}.")
            return jsonify({"message": "Admin access required."}), 403
        
        current_app.logger.info(f"Admin access GRANTED for user '{user_clerk_id}'.")
        return f(*args, **kwargs)
    return decorated
