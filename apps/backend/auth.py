from flask import request, jsonify, g
from functools import wraps
import os

# --- CORRECT LIBRARY AND IMPORT ---
from clerk_backend_api import Clerk

# Initialization
clerk = Clerk()

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # This decorator will now only perform debug logging.
        # It will intentionally fail at the end so we can see the logs.
        try:
            print("\n\n\n--- CLERK OBJECT DEBUGGING ---")
            print(f"Type of clerk object: {type(clerk)}")
            print(f"Attributes of clerk object: {dir(clerk)}")
            
            # Let's check for likely verification methods by name
            if hasattr(clerk, 'tokens'):
                print("DEBUG: clerk.tokens EXISTS.")
                print(f"Attributes of clerk.tokens: {dir(clerk.tokens)}")
            else:
                print("DEBUG: clerk.tokens DOES NOT EXIST.")

            if hasattr(clerk, 'sessions'):
                print("DEBUG: clerk.sessions EXISTS.")
                print(f"Attributes of clerk.sessions: {dir(clerk.sessions)}")
            else:
                print("DEBUG: clerk.sessions DOES NOT EXIST.")

            print("--- DEBUGGING COMPLETE ---")

        except Exception as e:
            print(f"--- DEBUGGING FAILED: {e} ---")

        # Intentionally return an error so we can capture the logs above.
        return jsonify({"message": "Debugging step complete. Please check Render logs."}), 500

    return decorated_function