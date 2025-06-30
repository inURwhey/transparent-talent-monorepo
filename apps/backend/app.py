# Path: apps/backend/app.py
import os
from flask import Flask, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    from . import config
    app.config.from_object(config.Config)
    
    # Reverted to simple, broad CORS for production
    CORS(app, supports_credentials=True)

    from . import database
    database.init_app(app)

    from .routes import profile, jobs, admin, onboarding
    app.register_blueprint(profile.profile_bp, url_prefix='/api')
    app.register_blueprint(jobs.jobs_bp, url_prefix='/api')
    app.register_blueprint(admin.admin_bp, url_prefix='/api')
    app.register_blueprint(onboarding.onboarding_bp, url_prefix='/api')

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