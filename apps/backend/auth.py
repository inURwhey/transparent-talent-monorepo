# Path: apps/backend/auth.py

from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
import json
import requests
import jwt
from jwt import PyJWKClient
import logging

# Configure logging for this module
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
ISSUER_URL = os.getenv('CLERK_ISSUER_URL')

# Function to determine authorized parties based on VERCEL_ENV
def get_authorized_parties():
    vercel_env = os.getenv('VERCEL_ENV', 'development')  # Default to 'development' if not set
    logger.info(f"VERCEL_ENV: {vercel_env}")

    if vercel_env == 'production':
        # Production: Use URLs from CLERK_AUTHORIZED_PARTY
        parties = [party.strip() for party in os.getenv('CLERK_AUTHORIZED_PARTY', '').split(',') if party.strip()]
        logger.info(f"Using production authorized parties: {parties}")
        return parties
    elif vercel_env == 'preview':
        # Preview: Use the VERCEL_URL
        vercel_url = os.getenv('VERCEL_URL')
        if not vercel_url:
            logger.warning("VERCEL_URL is not set in preview environment. Authentication may fail.")
            return []  # Or handle this differently, e.g., return a default localhost URL
        # VERCEL_URL does not include the protocol (https://), so prepend it
        preview_url = f"https://{vercel_url}"
        logger.info(f"Using preview authorized party: {preview_url}")
        return [preview_url]
    else:  # development
        # Development: Use localhost
        logger.info("Using development authorized party: http://localhost:3000")
        return ["http://localhost:3000"]

# Initialize authorized parties based on the environment
AUTHORIZED_PARTIES = get_authorized_parties()


jwks_client = None
try:
    if not ISSUER_URL:
        raise ValueError("CLERK_ISSUER_URL environment variable is not set.")
    jwks_client = PyJWKClient(f"{ISSUER_URL}/.well-known/jwks.json")
    logger.info("Auth Module Init: PyJWKClient initialized successfully.")
except Exception as e:
    logger.error(f"Auth Module Init: Failed to initialize PyJWKClient: {e}")
    # Re-raise the exception or handle it to prevent 'token_required' from being defined if auth cannot work
    raise # It's best to fail fast if the auth system cannot be initialized

def get_db_connection():
    db_url = os.getenv('DATABASE_URL')
    if not db_url: raise ValueError("DATABASE_URL not set for auth module")
    return psycopg2.connect(db_url)

def get_clerk_user_info(clerk_user_id):
    clerk_secret_key = os.getenv('CLERK_SECRET_KEY')
    if not clerk_secret_key:
        logger.error("CLERK_SECRET_KEY is not set. Cannot fetch Clerk user info.")
        return None
    api_url = f"https://api.clerk.com/v1/users/{clerk_user_id}"
    headers = {'Authorization': f'Bearer {clerk_secret_key}'}
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        clerk_user = response.json()
        primary_email_id = clerk_user.get("primary_email_address_id")
        for email in clerk_user.get("email_addresses", []):
            if email.get("id") == primary_email_id:
                return email.get("email_address")
        logger.warning(f"No primary email found for Clerk user ID: {clerk_user_id}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Clerk user info for {clerk_user_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_clerk_user_info for {clerk_user_id}: {e}")
        return None

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if jwks_client is None:
            logger.error("token_required called but jwks_client is not initialized. Check CLERK_ISSUER_URL.")
            return jsonify({"message": "Server authentication setup incomplete. Please try again later."}), 500

        try:
            logger.info("--- AUTHENTICATION ATTEMPT START ---")
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                logger.warning("--> FAILURE: Auth header missing or invalid.")
                return jsonify({"message": "Authorization header is missing or invalid"}), 401

            token = auth_header.split(' ')[1]
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # --- MODIFIED: Removed 'audience' parameter from jwt.decode ---
            # Manually validate 'azp' claim as Clerk issues 'azp' not 'aud'
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=ISSUER_URL, # Validates 'iss' claim
                options={"verify_exp": True, "verify_nbf": True, "verify_iat": True}
            )

            # 1. Validate Authorized Party (azp) manually
            azp_claim = claims.get('azp')
            if not azp_claim or azp_claim not in AUTHORIZED_PARTIES:
                logger.warning(f"--> FAILURE: Invalid Authorized Party. Got: '{azp_claim}', Expected one of: {AUTHORIZED_PARTIES}")
                raise jwt.InvalidAudienceError("Invalid authorized party.") # Using InvalidAudienceError for consistency

            logger.info("--> SUCCESS: Token claims validated (iss, azp, exp, nbf, iat).")

            clerk_user_id = claims.get('sub')
            if not clerk_user_id:
                logger.warning("--> FAILURE: Token is missing 'sub' claim.")
                return jsonify({"message": "Invalid token: missing user ID (sub) claim"}), 401

            conn = None
            try:
                conn = get_db_connection()
                with conn.cursor(cursor_factory=DictCursor) as cursor:
                    cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                    user = cursor.fetchone()
                    if not user:
                        logger.info(f"--> New user detected: {clerk_user_id}. Creating DB entry.")
                        user_email = get_clerk_user_info(clerk_user_id)
                        if not user_email:
                            logger.error(f"Could not retrieve email for Clerk user {clerk_user_id}.")
                            return jsonify({"message": "Could not retrieve user email from Clerk"}), 500

                        cursor.execute("SELECT * FROM users WHERE email = %s AND clerk_user_id IS NULL", (user_email,))
                        user = cursor.fetchone()
                        if user:
                            logger.info(f"--> Updating existing user {user['id']} with Clerk ID {clerk_user_id}.")
                            cursor.execute("UPDATE users SET clerk_user_id = %s WHERE id = %s RETURNING *;", (clerk_user_id, user['id']))
                            user = cursor.fetchone()
                            conn.commit()
                        else:
                            logger.info(f"--> Inserting new user with Clerk ID {clerk_user_id} and email {user_email}.")
                            cursor.execute("INSERT INTO users (clerk_user_id, email) VALUES (%s, %s) RETURNING *;", (clerk_user_id, user_email))
                            user = cursor.fetchone()
                            conn.commit()
                    g.current_user = user
                logger.info("--- AUTHENTICATION ATTEMPT SUCCEEDED ---")
            finally:
                if conn:
                    conn.close()

        except jwt.ExpiredSignatureError:
            logger.warning("--> FAILURE: Token has expired.")
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError as e: # Catch other general JWT validation errors
            logger.warning(f"--> FAILURE: JWT Invalid Token Error: {e}")
            return jsonify({"message": f"Token is invalid: {str(e)}"}), 401
        except requests.exceptions.RequestException as e:
            logger.error(f"--> FAILURE: Network error during Clerk API call: {e}")
            return jsonify({"message": "Network error during authentication process."}), 500
        except Exception as e:
            logger.error(f"--> FAILURE: A general exception occurred during authentication: {type(e).__name__} - {e}")
            return jsonify({"message": "An unexpected error occurred during authentication."}), 500

        return f(*args, **kwargs)
    return decorated_function