from flask import request, jsonify, g
from functools import wraps
from psycopg2.extras import DictCursor
import os
import psycopg2
from clerk_backend_api import Clerk
import json

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
        # --- EXTENSIVE DEBUGGING LOGS ---
        print("\n" + "="*50)
        print("INCOMING REQUEST TO PROTECTED ENDPOINT")
        print("="*50)
        
        # Log all incoming headers
        headers = dict(request.headers)
        print(f"REQUEST HEADERS:\n{json.dumps(headers, indent=2)}")

        # Load authorized parties from environment
        authorized_parties_json = os.getenv('AUTHORIZED_PARTIES_JSON')
        authorized_parties = json.loads(authorized_parties_json) if authorized_parties_json else []
        print(f"CONFIGURED AUTHORIZED PARTIES: {authorized_parties}")
        
        try:
            # We will now see exactly why this call is failing.
            claims = clerk.authenticate_request(request, {"authorized_parties": authorized_parties})
            clerk_user_id = claims.get('sub')
            
            if not clerk_user_id:
                print("--- AUTHENTICATION FAILED: User ID ('sub') not in claims. ---")
                return jsonify({"message": "Invalid token: missing user ID"}), 401
            
            print("--- AUTHENTICATION SUCCEEDED (SHOULD NOT HAPPEN YET) ---")
            
            # Database logic (will only run if auth succeeds)
            conn = get_db_connection()
            with conn.cursor(cursor_factory=DictCursor) as cursor:
                cursor.execute("SELECT * FROM users WHERE clerk_user_id = %s", (clerk_user_id,))
                user = cursor.fetchone()
                # ... (rest of DB logic) ...
                g.current_user = user
            conn.close()

        except Exception as e:
            # --- THE MOST IMPORTANT LOG ---
            # This will print the exact, detailed error from the Clerk library.
            print("\n--- CLERK AUTHENTICATION EXCEPTION ---")
            print(f"ERROR TYPE: {type(e).__name__}")
            print(f"ERROR DETAILS: {e}")
            print("="*50 + "\n")
            return jsonify({"message": "Authentication failed", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function