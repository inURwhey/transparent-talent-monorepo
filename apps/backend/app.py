# Path: apps/backend/app.py
import os
from flask import Flask, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    # This is the correct import path for your config module
    from . import config
    app.config.from_object(config.Config)
    
    # This is the robust CORS configuration we need
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize database
    from . import database
    database.init_app(app)

    # Import all blueprints
    from .routes.profile import profile_bp
    from .routes.jobs import jobs_bp
    from .routes.admin import admin_bp
    from .routes.onboarding import onboarding_bp
    from .routes.recommendations import reco_bp
    
    # Register all blueprints with a consistent /api prefix
    app.register_blueprint(profile_bp, url_prefix='/api')
    app.register_blueprint(jobs_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(onboarding_bp, url_prefix='/api')
    app.register_blueprint(reco_bp, url_prefix='/api')

    @app.route('/')
    def index():
        return "Backend server is running."

    @app.route('/api/debug-env')
    def debug_env():
        return jsonify({
            "clerk_key_is_set": bool(config.Config.CLERK_SECRET_KEY),
            "db_url_is_set": bool(config.Config.DATABASE_URL),
            "gemini_key_is_set": bool(config.Config.GEMINI_API_KEY)
        })

    return app

# This part is for local development and should not be removed
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)