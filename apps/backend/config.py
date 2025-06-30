# Path: apps/backend/config.py
import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Holds all configuration for the Flask application."""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Using the exact variable names from Render
    CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
    CLERK_ISSUER_URL = os.getenv('CLERK_ISSUER_URL')
    # Note: The variable is singular 'PARTY', not 'PARTIES'. We will handle this.
    CLERK_AUTHORIZED_PARTY = os.getenv('CLERK_AUTHORIZED_PARTY', '').split(',')

    ANALYSIS_PROTOCOL_VERSION = '2.0'
    JOB_POSTING_MAX_AGE_DAYS = 60
    TRACKED_JOB_STALE_DAYS = 30
    LEGACY_URL_MALFORMED_PATTERN = re.compile(r".+\s+\(.+\)|\(.+?\)$")
    
    @staticmethod
    def validate():
        if not Config.DATABASE_URL:
            raise ValueError("FATAL: DATABASE_URL environment variable is not set.")
        if not Config.CLERK_SECRET_KEY:
            raise ValueError("FATAL: CLERK_SECRET_KEY environment variable is not set.")
        if not Config.CLERK_ISSUER_URL:
            raise ValueError("FATAL: CLERK_ISSUER_URL environment variable is not set.")

config = Config()
config.validate()