# Path: apps/backend/services/profile_service.py
from flask import current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pytz

from ..app import db
from ..models import (
    UserProfile, User, ResumeSubmission, 
    CompanySizeEnum, WorkStyleTypeEnum, ConflictResolutionEnum, 
    CommunicationPrefEnum, ChangeToleranceEnum, WorkLocationEnum
)

# Mappings are now correctly keyed by the Enum objects from models.py
COMPANY_SIZE_MAPPING = {
    CompanySizeEnum.SMALL_BUSINESS: 'Small Business (1-50 employees)',
    CompanySizeEnum.MEDIUM_BUSINESS: 'Medium Business (51-250 employees)',
    CompanySizeEnum.LARGE_ENTERPRISE: 'Large Enterprise (250+ employees)',
    CompanySizeEnum.STARTUP: 'Startup (1-50 employees)',
    CompanySizeEnum.NO_PREFERENCE: 'No Preference'
}
REVERSE_COMPANY_SIZE_MAPPING = {v: k for k, v in COMPANY_SIZE_MAPPING.items()}

WORK_STYLE_MAPPING = {
    WorkStyleTypeEnum.STRUCTURED: 'Structured (Clear processes, predictable)',
    WorkStyleTypeEnum.AUTONOMOUS: 'Autonomous (Independent, self-directed)',
    WorkStyleTypeEnum.COLLABORATIVE: 'Collaborative (Team-oriented, frequent interaction)',
    WorkStyleTypeEnum.HYBRID: 'Hybrid (Mix of structure and autonomy)',
    WorkStyleTypeEnum.NO_PREFERENCE: 'No Preference'
}
REVERSE_WORK_STYLE_MAPPING = {v: k for k, v in WORK_STYLE_MAPPING.items()}

CONFLICT_RESOLUTION_MAPPING = {
    ConflictResolutionEnum.DIRECT: 'Direct (Face-to-face, immediate)',
    ConflictResolutionEnum.MEDIATED: 'Mediated (Involving a third party)',
    ConflictResolutionEnum.AVOIDANT: 'Avoidant (Prefer to de-escalate or avoid)',
    ConflictResolutionEnum.NO_PREFERENCE: 'No Preference'
}
REVERSE_CONFLICT_RESOLUTION_MAPPING = {v: k for k, v in CONFLICT_RESOLUTION_MAPPING.items()}

COMMUNICATION_PREFERENCE_MAPPING = {
    CommunicationPrefEnum.WRITTEN: 'Written (Email, documentation)',
    CommunicationPrefEnum.VERBAL: 'Verbal (Meetings, calls)',
    CommunicationPrefEnum.VISUAL: 'Visual (Diagrams, presentations)',
    CommunicationPrefEnum.NO_PREFERENCE: 'No Preference'
}
REVERSE_COMMUNICATION_PREFERENCE_MAPPING = {v: k for k, v in COMMUNICATION_PREFERENCE_MAPPING.items()}

CHANGE_TOLERANCE_MAPPING = {
    ChangeToleranceEnum.HIGH: 'High (Thrive in fast-paced, evolving environments)',
    ChangeToleranceEnum.MEDIUM: 'Medium (Adaptable but prefer some stability)',
    ChangeToleranceEnum.LOW: 'Low (Prefer stability and established routines)',
    ChangeToleranceEnum.NO_PREFERENCE: 'No Preference'
}
REVERSE_CHANGE_TOLERANCE_MAPPING = {v: k for k, v in CHANGE_TOLERANCE_MAPPING.items()}

WORK_LOCATION_MAPPING = {
    WorkLocationEnum.ON_SITE: 'On-site',
    WorkLocationEnum.REMOTE: 'Remote',
    WorkLocationEnum.HYBRID: 'Hybrid',
    WorkLocationEnum.NO_PREFERENCE: 'No Preference'
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
            'disc_assessment', 'clifton_strengths', # ADD THESE TWO
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
        # Use the model's to_dict() but then override Enums with display strings
        profile_dict = profile.to_dict()
        
        # Manually convert ENUM values (which are strings from to_dict) to display strings
        for field, (fwd_map, rev_map) in self.enum_field_mappings.items():
            db_value_str = profile_dict.get(field)
            if db_value_str:
                # Find the Enum object corresponding to the string value
                enum_obj = next((k for k, v in fwd_map.items() if k.value == db_value_str), None)
                if enum_obj:
                    profile_dict[field] = fwd_map.get(enum_obj)

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
            # Check if the field is allowed and if the current value in the model is None
            if key in self.allowed_fields and getattr(profile, key) is None:
                update_data[key] = value

        if update_data:
            self.logger.info(f"Enriching profile for user {user_id} with AI data: {list(update_data.keys())}")
            # Use the existing update_profile logic to handle type conversions
            self.update_profile(user_id, update_data)
        
        return self.get_profile(user_id)


    def get_profile_for_analysis(self, user_id: int):
        profile = self._get_or_create_profile(user_id)
        # The model's to_dict() method is perfect for this as it already returns enum values
        profile_dict = profile.to_dict()
        
        # Remove fields that are not useful for AI analysis or are internal
        profile_dict.pop('id', None)
        profile_dict.pop('user_id', None)
        
        return profile_dict

    def has_completed_required_profile_fields(self, user_id: int):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile: return False

        # For onboarding to be complete, they need a job title and a resume
        has_title = profile.desired_job_titles and profile.desired_job_titles.strip()
        has_resume = ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).first() is not None
        
        return has_title and has_resume