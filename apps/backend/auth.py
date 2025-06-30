import os
from functools import wraps
from flask import request, jsonify, g, current_app
import jwt
from jwt.algorithms import RSAAlgorithm
import requests
import re # Import the regular expression module

# --- Constants ---
# Load allowed parties from environment variables
# Production URLs are static and predictable.
CLERK_ISSUER = os.getenv('CLERK_ISSUER')
# Split the comma-separated string of authorized parties into a list
PROD_AUTHORIZED_PARTIES = os.getenv('CLERK_AUTHORIZED_PARTIES', '').split(',')

# Vercel preview URLs have a dynamic, hyphenated structure.
# This regex will match URLs like: 'https://transparent-talent-frontend-1a2b3c4d-greg-freeds-projects.vercel.app'
VERCEL_PREVIEW_URL_PATTERN = re.compile(
    r"^https:\/\/transparent-talent-frontend-[a-z0-9]+-greg-freeds-projects\.vercel\.app$"
)

# Fetch the JWKS from Clerk
def get_jwks():
    jwks_url = f"{CLERK_ISSUER}/.well-known/jwks.json"
    try:
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to fetch JWKS: {e}")
        return None

# --- Main Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        current_app.logger.info("--- AUTHENTICATION ATTEMPT START ---")
        token = None
        if 'Authorization' in request.headers:
            try:
                token = request.headers['Authorization'].split(" ")[1]
            except IndexError:
                current_app.logger.warning("Malformed Authorization header. Bearer token not found.")
                return jsonify({"message": "Malformed Authorization header."}), 401

        if not token:
            current_app.logger.warning("Authorization token is missing.")
            return jsonify({"message": "Token is missing!"}), 401
        
        jwks = get_jwks()
        if not jwks:
            return jsonify({"message": "Could not fetch JWKS for token validation."}), 500

        try:
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            if not rsa_key:
                 raise jwt.exceptions.InvalidKeyError("Public key not found in JWKS.")

            public_key = RSAAlgorithm.from_jwk(rsa_key)
            
            # Decode without verifying 'aud' claim, as Clerk uses 'azp'
            claims = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                issuer=CLERK_ISSUER,
                options={"verify_aud": False} 
            )

            # --- CUSTOM 'azp' (Authorized Party) VALIDATION ---
            authorized_party = claims.get('azp')
            if not authorized_party:
                current_app.logger.error("Token is missing the 'azp' claim.")
                raise jwt.exceptions.MissingRequiredClaimError("azp")
            
            # Check if the 'azp' matches our production URLs OR the Vercel preview pattern
            is_authorized = False
            if authorized_party in PROD_AUTHORIZED_PARTIES:
                is_authorized = True
            elif VERCEL_PREVIEW_URL_PATTERN.match(authorized_party):
                is_authorized = True
            
            if not is_authorized:
                current_app.logger.error(f"Unauthorized 'azp' claim: {authorized_party}. Not in allowed list or matching preview pattern.")
                raise jwt.exceptions.InvalidAudienceError("Invalid authorized party.")
            
            current_app.logger.info("--> SUCCESS: Token claims validated (iss, azp, exp, nbf, iat).")

        except jwt.ExpiredSignatureError:
            current_app.logger.error("Token has expired.")
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.exceptions.InvalidKeyError as e:
            current_app.logger.error(f"JWT Invalid Key Error: {e}")
            return jsonify({"message": "Invalid token key."}), 401
        except jwt.exceptions.DecodeError as e:
            current_app.logger.error(f"JWT Decode Error: {e}")
            return jsonify({"message": "Token decoding failed."}), 401
        except Exception as e:
            current_app.logger.error(f"An unexpected error occurred during token validation: {e}")
            return jsonify({"message": "An unexpected error occurred during token validation."}), 500
        
        g.current_user = claims
        current_app.logger.info("--- AUTHENTICATION ATTEMPT SUCCEEDED ---")
        return f(*args, **kwargs)

    return decorated