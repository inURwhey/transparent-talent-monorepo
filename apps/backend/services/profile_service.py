# Path: apps/backend/services/profile_service.py
from flask import current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pytz

from ..app import db
from ..models import UserProfile, User, ResumeSubmission, CompanySize, WorkStyleType, ConflictResolution, CommunicationPref, ChangeTolerance, WorkLocation

# Mappings are now more for display layer logic, less for DB conversion
COMPANY_SIZE_MAPPING = {
    CompanySize.SMALL_BUSINESS: 'Small Business (1-50 employees)',
    CompanySize.MEDIUM_BUSINESS: 'Medium Business (51-250 employees)',
    CompanySize.LARGE_ENTERPRISE: 'Large Enterprise (250+ employees)',
    CompanySize.STARTUP: 'Startup (1-50 employees)',
    CompanySize.NO_PREFERENCE: 'No Preference'
}
# Create reverse mappings for efficient lookups
REVERSE_COMPANY_SIZE_MAPPING = {v: k for k, v in COMPANY_SIZE_MAPPING.items()}

WORK_STYLE_MAPPING = {
    WorkStyleType.STRUCTURED: 'Structured (Clear processes, predictable)',
    WorkStyleType.AUTONOMOUS: 'Autonomous (Independent, self-directed)',
    WorkStyleType.COLLABORATIVE: 'Collaborative (Team-oriented, frequent interaction)',
    WorkStyleType.HYBRID: 'Hybrid (Mix of structure and autonomy)',
    WorkStyleType.NO_PREFERENCE: 'No Preference'
}
REVERSE_WORK_STYLE_MAPPING = {v: k for k, v in WORK_STYLE_MAPPING.items()}

CONFLICT_RESOLUTION_MAPPING = {
    ConflictResolution.DIRECT: 'Direct (Face-to-face, immediate)',
    ConflictResolution.MEDIATED: 'Mediated (Involving a third party)',
    ConflictResolution.AVOIDANT: 'Avoidant (Prefer to de-escalate or avoid)',
    ConflictResolution.NO_PREFERENCE: 'No Preference'
}
REVERSE_CONFLICT_RESOLUTION_MAPPING = {v: k for k, v in CONFLICT_RESOLUTION_MAPPING.items()}

COMMUNICATION_PREFERENCE_MAPPING = {
    CommunicationPref.WRITTEN: 'Written (Email, documentation)',
    CommunicationPref.VERBAL: 'Verbal (Meetings, calls)',
    CommunicationPref.VISUAL: 'Visual (Diagrams, presentations)',
    CommunicationPref.NO_PREFERENCE: 'No Preference'
}
REVERSE_COMMUNICATION_PREFERENCE_MAPPING = {v: k for k, v in COMMUNICATION_PREFERENCE_MAPPING.items()}

CHANGE_TOLERANCE_MAPPING = {
    ChangeTolerance.HIGH: 'High (Thrive in fast-paced, evolving environments)',
    ChangeTolerance.MEDIUM: 'Medium (Adaptable but prefer some stability)',
    ChangeTolerance.LOW: 'Low (Prefer stability and established routines)',
    ChangeTolerance.NO_PREFERENCE: 'No Preference'
}
REVERSE_CHANGE_TOLERANCE_MAPPING = {v: k for k, v in CHANGE_TOLERANCE_MAPPING.items()}

WORK_LOCATION_MAPPING = {
    WorkLocation.ON_SITE: 'On-site',
    WorkLocation.REMOTE: 'Remote',
    WorkLocation.HYBRID: 'Hybrid',
    WorkLocation.NO_PREFERENCE: 'No Preference'
}
REVERSE_WORK_LOCATION_MAPPING = {v: k for k, v in WORK_LOCATION_MAPPING.items()}


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
        self.enum_field_mappings = {
            'preferred_company_size': (COMPANY_SIZE_MAPPING, REVERSE_COMPANY_SIZE_MAPPING),
            'work_style_preference': (WORK_STYLE_MAPPING, REVERSE_WORK_STYLE_MAPPING),
            'conflict_resolution_style': (CONFLICT_RESOLUTION_MAPPING, REVERSE_CONFLICT_RESOLUTION_MAPPING),
            'communication_preference': (COMMUNICATION_PREFERENCE_MAPPING, REVERSE_COMMUNICATION_PREFERENCE_MAPPING),
            'change_tolerance': (CHANGE_TOLERANCE_MAPPING, REVERSE_CHANGE_TOLERANCE_MAPPING),
            'preferred_work_style': (WORK_LOCATION_MAPPING, REVERSE_WORK_LOCATION_MAPPING)
        }

    def _get_or_create_profile(self, user_id):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile:
            self.logger.info(f"No profile for user {user_id}, creating default.")
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                self.logger.warning(f"Race condition creating profile for user {user_id}, fetching existing.")
                profile = UserProfile.query.filter_by(user_id=user_id).first()
        return profile

    def get_profile(self, user_id: int):
        profile = self._get_or_create_profile(user_id)
        profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
        
        # Manually convert ENUM objects to display strings for the frontend
        for field, (fwd_map, _) in self.enum_field_mappings.items():
            enum_obj = profile_dict.get(field)
            if enum_obj:
                profile_dict[field] = fwd_map.get(enum_obj, None)
        
        # Ensure lat/long are floats
        if profile_dict.get('latitude') is not None: profile_dict['latitude'] = float(profile_dict['latitude'])
        if profile_dict.get('longitude') is not None: profile_dict['longitude'] = float(profile_dict['longitude'])

        return profile_dict

    def update_profile(self, user_id: int, data: dict):
        profile = self._get_or_create_profile(user_id)

        for key, value in data.items():
            if key in self.allowed_fields:
                if key in self.enum_field_mappings:
                    _, rev_map = self.enum_field_mappings[key]
                    # Convert incoming display string back to an Enum object
                    enum_obj = rev_map.get(value) if value else None
                    setattr(profile, key, enum_obj)
                elif key in ['latitude', 'longitude'] and value is not None:
                    try:
                        setattr(profile, key, float(value))
                    except (ValueError, TypeError):
                        setattr(profile, key, None)
                elif key == 'is_remote_preferred':
                    setattr(profile, key, bool(value))
                elif key in ['desired_salary_min', 'desired_salary_max'] and value is not None:
                    try:
                        clean_value = int(str(value).replace(',', '')) if value else None
                        setattr(profile, key, clean_value)
                    except (ValueError, TypeError):
                        setattr(profile, key, None)
                else:
                    setattr(profile, key, value if value not in [None, ''] else None)
        
        profile.updated_at = datetime.now(pytz.utc)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating profile for user {user_id}: {e}", exc_info=True)
            raise

        return self.get_profile(user_id)

    def enrich_profile(self, user_id: int, ai_data: dict):
        """Merges AI-parsed data into a profile, only filling empty fields."""
        profile = self._get_or_create_profile(user_id)
        
        update_data = {}
        for key, value in ai_data.items():
            if key in self.allowed_fields and getattr(profile, key) is None:
                update_data[key] = value

        if update_data:
            self.logger.info(f"Enriching profile for user {user_id} with AI data: {list(update_data.keys())}")
            # Use the existing update_profile logic to handle type conversions
            return self.update_profile(user_id, update_data)
        
        return self.get_profile(user_id)

    def get_profile_for_analysis(self, user_id: int):
        profile = self._get_or_create_profile(user_id)
        profile_dict = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}

        # Manually convert ENUM objects to their string values for JSON serialization
        for field in self.enum_field_mappings.keys():
            enum_obj = profile_dict.get(field)
            if enum_obj:
                profile_dict[field] = enum_obj.value
        
        # Ensure lat/long are floats
        if profile_dict.get('latitude') is not None: profile_dict['latitude'] = float(profile_dict['latitude'])
        if profile_dict.get('longitude') is not None: profile_dict['longitude'] = float(profile_dict['longitude'])
        
        # Remove fields that are not useful for AI analysis
        profile_dict.pop('id', None)
        profile_dict.pop('user_id', None)
        profile_dict.pop('created_at', None)
        profile_dict.pop('updated_at', None)

        return profile_dict

    def has_completed_required_profile_fields(self, user_id: int):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile: return False

        # For onboarding to be complete, they need a job title and a resume
        has_title = profile.desired_job_titles and profile.desired_job_titles.strip()
        has_resume = ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).first() is not None
        
        return has_title and has_resume