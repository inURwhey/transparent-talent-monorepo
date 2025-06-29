import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Holds all configuration for the Flask application."""
    
    # --- Core ---
    DATABASE_URL = os.getenv('DATABASE_URL')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')

    # --- Application Constants ---
    ANALYSIS_PROTOCOL_VERSION = '2.0'
    JOB_POSTING_MAX_AGE_DAYS = 60
    TRACKED_JOB_STALE_DAYS = 30
    LEGACY_URL_MALFORMED_PATTERN = re.compile(r".+\s+\(.+\)|\(.+?\)$")
    
    # --- Validation ---
    @staticmethod
    def validate():
        if not Config.DATABASE_URL:
            raise ValueError("FATAL: DATABASE_URL environment variable is not set.")
        if not Config.GEMINI_API_KEY:
            print("Warning: GEMINI_API_KEY is not set. Job analysis functionality will be disabled.")
        if not Config.CLERK_SECRET_KEY:
            # This is a critical failure for authentication
            raise ValueError("FATAL: CLERK_SECRET_KEY environment variable is not set.")

# Create a single instance of the config to be imported by other modules
config = Config()
config.validate()