# Path: apps/backend/app.py
import os
from flask import Flask, jsonify, request

def create_app():
    app = Flask(__name__)

    from . import config
    app.config.from_object(config.Config)
    
    # We are now handling CORS manually via middleware below.
    # from flask_cors import CORS
    # CORS(app, resources={r"/api/*": {"origins": "*"}})

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

    @app.after_request
    def after_request(response):
        """
        Manually attach CORS headers to every response.
        This is a robust way to handle CORS for production APIs.
        """
        # The frontend URL from Vercel
        origin = request.headers.get('Origin')
        allowed_origins = [
            'https://www.transparenttalent.ai', 
            'https://transparenttalent.ai'
        ]
        
        # This is a simplified check. A more robust regex could be used for previews.
        if origin and any(origin.startswith(url) for url in allowed_origins):
             response.headers.add('Access-Control-Allow-Origin', origin)
        
        # For development, a wildcard is often used, but explicit is better for prod.
        # response.headers.add('Access-Control-Allow-Origin', '*')

        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

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