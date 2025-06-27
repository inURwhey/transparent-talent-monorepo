from flask import request, jsonify
from functools import wraps
from clerk_backend_api import Clerk
import os

# The new library reads the secret key from the environment automatically.
# The constructor is now called with no arguments.
clerk = Clerk()

def token_required(f):
    """
    A decorator to protect a Flask endpoint. It verifies the JWT
    from the 'Authorization' header.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            session_token = auth_header.split(' ')[1]

        if not session_token:
            return jsonify({"message": "Authentication token is missing"}), 401

        try:
            # The verify_token method now exists on the 'tokens' interface.
            claims = clerk.tokens.verify_token(session_token)
        except Exception as e:
            return jsonify({"message": "Authentication token is invalid", "error": str(e)}), 401

        return f(*args, **kwargs)
    return decorated_function