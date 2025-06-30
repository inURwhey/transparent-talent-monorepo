import os
from flask import Flask, jsonify
from flask_cors import CORS

# --- Application Factory ---
def create_app():
    """
    Creates and configures an instance of the Flask application.
    """
    app = Flask(__name__)

    # --- Configuration ---
    from . import config
    app.config.from_object(config.Config)
    
    # --- Extensions ---
    CORS(app, supports_credentials=True, expose_headers=["Authorization"])

    # --- Database Initialization ---
    from . import database
    database.init_app(app)

    # --- Register Blueprints (API Routes) ---
    # Import the new onboarding blueprint alongside the others
    from .routes import profile, jobs, admin, onboarding
    
    # Register the new blueprint
    app.register_blueprint(profile.profile_bp, url_prefix='/api')
    app.register_blueprint(jobs.jobs_bp, url_prefix='/api')
    app.register_blueprint(admin.admin_bp, url_prefix='/api')
    app.register_blueprint(onboarding.onboarding_bp, url_prefix='/api')


    # --- Basic Routes for Health/Debug ---
    @app.route('/')
    def index():
        return "Backend server is running."

    @app.route('/api/debug-env')
    def debug_env():
        # A simple endpoint to check if environment variables are loaded
        return jsonify({
            "clerk_key_is_set": bool(config.Config.CLERK_SECRET_KEY),
            "db_url_is_set": bool(config.Config.DATABASE_URL),
            "gemini_key_is_set": bool(config.Config.GEMINI_API_KEY)
        })

    return app

# --- Main Execution ---
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)