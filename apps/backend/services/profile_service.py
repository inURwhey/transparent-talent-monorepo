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
            'disc_assessment', 'clifton_strengths',
            'other_personal_attributes', 'has_completed_onboarding'
        ]
        self.enum_fields = [
            'preferred_company_size', 'work_style_preference', 'conflict_resolution_style',
            'communication_preference', 'change_tolerance', 'preferred_work_style'
        ]

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
        # The model's to_dict() method correctly returns the raw ENUM value (e.g., 'STRUCTURED').
        # This is the robust source of truth for the frontend.
        return profile.to_dict()

    def update_profile(self, user_id: int, data: dict):
        profile = self._get_or_create_profile(user_id)

        for key, value in data.items():
            if key in self.allowed_fields:
                if key in self.enum_fields:
                    # The value from the frontend will be the raw ENUM string (e.g., 'STRUCTURED') or null.
                    # The SQLAlchemy Enum type handles the conversion automatically.
                    setattr(profile, key, value)
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
        profile = self._get_or_create_profile(user_id)
        update_data = {}
        for key, value in ai_data.items():
            if key in self.allowed_fields and getattr(profile, key) is None:
                update_data[key] = value

        if update_data:
            self.logger.info(f"Enriching profile for user {user_id} with AI data: {list(update_data.keys())}")
            self.update_profile(user_id, update_data)
        
        return self.get_profile(user_id)


    def get_profile_for_analysis(self, user_id: int):
        profile = self._get_or_create_profile(user_id)
        profile_dict = profile.to_dict()
        
        profile_dict.pop('id', None)
        profile_dict.pop('user_id', None)
        
        return profile_dict

    def has_completed_required_profile_fields(self, user_id: int):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile: return False

        has_title = profile.desired_job_titles and profile.desired_job_titles.strip()
        has_resume = ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).first() is not None
        
        return has_title and has_resume