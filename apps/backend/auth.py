# Path: apps/backend/auth.py
import os
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from jwt.algorithms import RSAAlgorithm
import requests
from .config import config # <-- Import our central config object

# --- REMOVED direct os.getenv calls ---
# CLERK_ISSUER = os.getenv('CLERK_ISSUER')
# AUTHORIZED_PARTIES = os.getenv('CLERK_AUTHORIZED_PARTIES', '').split(',')

def get_jwks():
    # Use the validated config variable
    jwks_url = f"{config.CLERK_ISSUER}/.well-known/jwks.json"
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
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                return jsonify({"message": "Malformed Authorization header."}), 401
        if not token:
            return jsonify({"message": "Token is missing!"}), 401
        jwks = get_jwks()
        if not jwks:
            return jsonify({"message": "Could not fetch JWKS for token validation."}), 500
        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {"kty": key["kty"], "kid": key["kid"], "use": key["use"], "n": key["n"], "e": key["e"]}
            if not rsa_key:
                 raise jwt.exceptions.InvalidKeyError("Public key not found in JWKS.")
            public_key = RSAAlgorithm.from_jwk(rsa_key)
            
            # Use the validated config variable
            claims = jwt.decode(token, public_key, algorithms=["RS256"], issuer=config.CLERK_ISSUER, options={"verify_aud": False})

            authorized_party = claims.get('azp')
            # Use the validated config variable
            if not authorized_party or authorized_party not in config.CLERK_AUTHORIZED_PARTIES:
                current_app.logger.warning(f"--> FAILURE: Invalid Authorized Party. Got: '{authorized_party}', Expected one of: {config.CLERK_AUTHORIZED_PARTIES}")
                raise jwt.exceptions.InvalidAudienceError("Invalid authorized party.")
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during token validation: {e}")
            return jsonify({"message": "An unexpected error occurred during token validation."}), 500
        
        g.current_user = claims
        return f(*args, **kwargs)
    return decorated