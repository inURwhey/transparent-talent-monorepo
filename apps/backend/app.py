# Path: apps/backend/app.py
import os
import re
from flask import Flask, jsonify

def create_app():
    app = Flask(__name__)

    from . import config
    app.config.from_object(config.Config)
    
    # Re-instantiate Flask-CORS with a robust configuration
    from flask_cors import CORS
    
    # Define allowed origins, including a regex for Vercel preview deployments
    allowed_origins = [
        "https://www.transparenttalent.ai",
        "https://transparenttalent.ai",
        re.compile(r"^https://transparent-talent-git-.*-greg-p-projects\.vercel\.app$")
    ]

    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
        supports_credentials=True,
        allow_headers=["Authorization", "Content-Type"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    from . import database
    database.init_app(app)

    # Import all blueprints
    from .routes.profile import profile_bp
    from .routes.jobs import jobs_bp
    from .routes.admin import admin_bp
    from .routes.onboarding import onboarding_bp
    from .routes.recommendations import reco_bp
    from .routes.companies import companies_bp # <-- ADDED IMPORT

    # Register all blueprints with a consistent /api prefix
    app.register_blueprint(profile_bp, url_prefix='/api')
    app.register_blueprint(jobs_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(onboarding_bp, url_prefix='/api')
    app.register_blueprint(reco_bp, url_prefix='/api')
    app.register_blueprint(companies_bp, url_prefix='/api') # <-- ADDED REGISTRATION

    # The manual CORS middleware has been removed in favor of Flask-CORS.

    @app.route('/')
    def index(): return "Backend server is running."

    @app.route('/api/debug-env')
    def debug_env():
        return jsonify({
            "clerk_key_is_set": bool(config.Config.CLERK_SECRET_KEY),
            "db_url_is_set": bool(config.Config.DATABASE_URL),
            "gemini_key_is_set": bool(config.Config.GEMINI_API_KEY)
        })

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)