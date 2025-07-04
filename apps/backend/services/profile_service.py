# Path: apps/backend/services/profile_service.py
from flask import current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pytz

from ..app import db # NEW IMPORT for Flask-SQLAlchemy
from ..models import UserProfile, User, ResumeSubmission # Also import ResumeSubmission for potential use

# Mapping for ENUM fields from database value to display string
COMPANY_SIZE_MAPPING = {
    'SMALL_BUSINESS': 'Small Business (1-50 employees)',
    'MEDIUM_BUSINESS': 'Medium Business (51-250 employees)',
    'LARGE_ENTERPRISE': 'Large Enterprise (250+ employees)',
    'STARTUP': 'Startup (1-50 employees)',
    'NO_PREFERENCE': 'No Preference'
}

WORK_STYLE_MAPPING = {
    'STRUCTURED': 'Structured (Clear processes, predictable)',
    'AUTONOMOUS': 'Autonomous (Independent, self-directed)',
    'COLLABORATIVE': 'Collaborative (Team-oriented, frequent interaction)',
    'HYBRID': 'Hybrid (Mix of structure and autonomy)',
    'NO_PREFERENCE': 'No Preference'
}

CONFLICT_RESOLUTION_MAPPING = {
    'DIRECT': 'Direct (Face-to-face, immediate)',
    'MEDIATED': 'Mediated (Involving a third party)',
    'AVOIDANT': 'Avoidant (Prefer to de-escalate or avoid)',
    'NO_PREFERENCE': 'No Preference'
}

COMMUNICATION_PREFERENCE_MAPPING = {
    'WRITTEN': 'Written (Email, documentation)',
    'VERBAL': 'Verbal (Meetings, calls)',
    'VISUAL': 'Visual (Diagrams, presentations)',
    'NO_PREFERENCE': 'No Preference'
}

CHANGE_TOLERANCE_MAPPING = {
    'HIGH': 'High (Thrive in fast-paced, evolving environments)',
    'MEDIUM': 'Medium (Adaptable but prefer some stability)',
    'LOW': 'Low (Prefer stability and established routines)',
    'NO_PREFERENCE': 'No Preference'
}

WORK_LOCATION_MAPPING = {
    'ON_SITE': 'On-site',
    'REMOTE': 'Remote',
    'HYBRID': 'Hybrid',
    'NO_PREFERENCE': 'No Preference'
}


class ProfileService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.allowed_fields = [
            'phone_number', 'linkedin_url', 'github_url', 'portfolio_url', 'location',
            'latitude', 'longitude', 'current_role', 'desired_job_titles',
            'desired_salary_min', 'desired_salary_max', 'target_industries',
            'career_goals', 'preferred_company_size', 'work_style_preference',
            'conflict_resolution_style', 'communication_preference', 'change_tolerance',
            'preferred_work_style', 'is_remote_preferred',
            'skills', 'education', 'work_experience', 'personality_16_personalities',
            'other_personal_attributes', 'has_completed_onboarding'
        ]
        self.enum_fields = {
            'preferred_company_size': COMPANY_SIZE_MAPPING,
            'work_style_preference': WORK_STYLE_MAPPING,
            'conflict_resolution_style': CONFLICT_RESOLUTION_MAPPING,
            'communication_preference': COMMUNICATION_PREFERENCE_MAPPING,
            'change_tolerance': CHANGE_TOLERANCE_MAPPING,
            'preferred_work_style': WORK_LOCATION_MAPPING
        }

    def _map_db_to_display(self, field_name, db_value):
        """Maps database ENUM value to a user-friendly display string."""
        if field_name in self.enum_fields and db_value is not None:
            # db_value will be an Enum object, need to get its value first
            return self.enum_fields[field_name].get(db_value.value, db_value.value)
        return db_value

    def _map_display_to_db(self, field_name, display_value):
        """Maps user-friendly display string to a database ENUM value."""
        if field_name in self.enum_fields and display_value is not None:
            # Find the key (DB value) for the given display_value
            for db_key, display_str in self.enum_fields[field_name].items():
                if display_str == display_value:
                    return db_key
            # If "No Preference" is selected, ensure it maps to the correct ENUM value
            if display_value == "No Preference":
                return "NO_PREFERENCE"
            # If value is an empty string or null from frontend, convert to None for DB
            if display_value == '' or display_value == 'null':
                return None
            return display_value # Return as is if no mapping found (e.g., direct enum value passed)
        return None if display_value == '' or display_value == 'null' else display_value

    def get_profile(self, user_id: int):
        """Fetches a user's profile, creating a default if none exists."""
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            self.logger.info(f"No profile found for user {user_id}. Creating default.")
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            try:
                db.session.commit()
                db.session.refresh(profile) # Refresh to get ID and default values
            except IntegrityError as e:
                db.session.rollback()
                self.logger.error(f"Integrity error when creating default profile for user {user_id}: {e}")
                # Attempt to retrieve if it was created by a concurrent request
                profile = UserProfile.query.filter_by(user_id=user_id).first()
                if not profile: raise e # If still no profile, re-raise error
            except Exception as e:
                db.session.rollback()
                self.logger.error(f"Error creating default profile for user {user_id}: {e}")
                raise e

        profile_dict = profile.to_dict()
        # Map ENUM values for display
        for field, mapping in self.enum_fields.items():
            db_value = getattr(profile, field)
            profile_dict[field] = self._map_db_to_display(field, db_value)

        return profile_dict

    def update_profile(self, user_id: int, data: dict):
        """Updates a user's profile with provided data."""
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            # This case should ideally be handled by get_profile creating a default.
            # But as a fallback, create if not found.
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        for key, value in data.items():
            if key in self.allowed_fields:
                if key in self.enum_fields:
                    # Convert display string to DB ENUM value
                    db_value = self._map_display_to_db(key, value)
                    setattr(profile, key, db_value)
                elif key in ['latitude', 'longitude'] and value is not None:
                    try:
                        setattr(profile, key, float(value))
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid numeric value for {key}: {value}. Setting to None.")
                        setattr(profile, key, None)
                elif key == 'is_remote_preferred' and value is None:
                    # Handle frontend sending null/undefined for checkbox if not checked
                    setattr(profile, key, False)
                elif key in ['desired_salary_min', 'desired_salary_max'] and value is not None:
                    try:
                        # Strip commas and convert to int
                        clean_value = int(str(value).replace(',', ''))
                        setattr(profile, key, clean_value)
                    except (ValueError, TypeError):
                        self.logger.warning(f"Invalid integer value for {key}: {value}. Setting to None.")
                        setattr(profile, key, None)
                else:
                    # For other fields, if value is empty string, set to None for DB
                    setattr(profile, key, value if value != '' else None)
        
        profile.updated_at = datetime.now(pytz.utc) # Manually update timestamp

        try:
            db.session.commit()
            db.session.refresh(profile)
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating profile for user {user_id}: {e}")
            raise e

        profile_dict = profile.to_dict()
        # Remap for display after successful update
        for field, mapping in self.enum_fields.items():
            db_value = getattr(profile, field)
            profile_dict[field] = self._map_db_to_display(field, db_value)

        return profile_dict


    def get_profile_for_analysis(self, user_id: int):
        """
        Retrieves a user's profile optimized for AI analysis.
        Returns a flat dictionary with raw DB values, not display strings.
        """
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            self.logger.warning(f"No profile found for user {user_id} during AI analysis request.")
            return None # Or a default empty profile dict

        # Directly return the raw DB values as a dictionary
        profile_data = profile.to_dict()
        
        # Ensure enums are their raw string values, not Enum objects
        for field in self.enum_fields.keys():
            if profile_data.get(field) and hasattr(profile_data[field], 'value'):
                profile_data[field] = profile_data[field].value

        return profile_data

    def get_active_resume_text(self, user_id: int):
        """Retrieves the raw text of the user's active resume."""
        resume = ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).first()
        return resume.raw_text if resume else None

    def has_completed_required_profile_fields(self, user_id: int):
        """
        Checks if a user has completed the minimal required profile fields
        to enable full AI analysis.
        """
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            return False

        # Define required fields based on your business logic
        # For example, desired_job_titles and current_role
        required_fields = [
            profile.desired_job_titles,
            profile.current_role
        ]

        # Check for presence of required text fields
        if not all(field and field.strip() for field in required_fields):
            return False
        
        # Check if an active resume has been submitted
        active_resume = ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).first()
        if not active_resume:
            return False

        return True