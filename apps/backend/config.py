# Path: apps/backend/config.py
import os
import re
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Holds all configuration for the Flask application."""
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    CLERK_SECRET_KEY = os.getenv('CLERK_SECRET_KEY')
    CLERK_ISSUER_URL = os.getenv('CLERK_ISSUER_URL')

    # --- THE FIX ---
    # We now map over the split list and call .strip() on each item
    # to remove any leading or trailing whitespace.
    raw_parties = os.getenv('CLERK_AUTHORIZED_PARTY', '')
    CLERK_AUTHORIZED_PARTY = [party.strip() for party in raw_parties.split(',')]

    ANALYSIS_PROTOCOL_VERSION = '2.0'
    JOB_POSTING_MAX_AGE_DAYS = 60
    TRACKED_JOB_STALE_DAYS = 30
    LEGACY_URL_MALFORMED_PATTERN = re.compile(r".+\s+\(.+\)|\(.+?\)$")

    # --- AI Input Size Limits (in characters) ---
    # These limits are for initial ingestion, assuming a subsequent AI trimming step will reduce effective tokens.
    MAX_RESUME_TEXT_LENGTH = int(os.getenv('MAX_RESUME_TEXT_LENGTH', '100000')) # Increased significantly for initial ingest
    MAX_JOB_TEXT_LENGTH = int(os.getenv('MAX_JOB_TEXT_LENGTH', '200000')) # Increased significantly for initial ingest
    MAX_CLASSIFICATION_TEXT_LENGTH = int(os.getenv('MAX_CLASSIFICATION_TEXT_LENGTH', '2000')) # Remains small for cheap classification

    # --- Domain Whitelist/Blacklist for Job Postings ---
    # Domains from which job posts are considered high quality and bypass AI classification.
    # Add company career sites and major reputable job boards.
    WHITELISTED_JOB_DOMAINS = [
        'linkedin.com', 'indeed.com', 'glassdoor.com', 'boards.greenhouse.io',
        'jobs.lever.co', 'workday.com', 'careers.google.com', 'amazon.jobs'
    ]
    # Domains from which job posts are considered low quality/spam and are immediately rejected.
    # Updated based on research.
    BLACKLISTED_JOB_DOMAINS = [
        'geebo.com',
    ]

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