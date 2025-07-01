# Path: apps/backend/app.py
import os
from flask import Flask, jsonify
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config.from_object('your_config_module.Config') # Ensure this path is correct
    
    # This configuration is the most robust for handling preflight requests
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    from . import database
    database.init_app(app)

    # Import all blueprints
    from .routes.profile import profile_bp
    from .routes.jobs import jobs_bp
    from .routes.admin import admin_bp
    from .routes.onboarding import onboarding_bp
    from .routes.recommendations import reco_bp
    
    # Register blueprints without adding a prefix here
    app.register_blueprint(profile_bp)
    app.register_blueprint(jobs_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(onboarding_bp)
    app.register_blueprint(reco_bp)

    @app.route('/')
    def index(): return "Backend server is running."

    return app