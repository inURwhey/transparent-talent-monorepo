# Path: apps/backend/services/profile_service.py
from flask import current_app
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pytz

from ..app import db
from ..models import User, UserProfile, ResumeSubmission

class ProfileService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.allowed_fields = [
            'full_name', 'email', # Fields from the User model
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
        self.user_model_fields = ['full_name']
        self.profile_model_fields = [f for f in self.allowed_fields if f not in self.user_model_fields]


    def _get_or_create_profile(self, user_id):
        profile = UserProfile.query.options(joinedload(UserProfile.user)).filter_by(user_id=user_id).first()
        if not profile:
            self.logger.info(f"No profile for user {user_id}, creating default.")
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            try:
                db.session.commit()
                # After commit, eager load the user relationship
                profile = UserProfile.query.options(joinedload(UserProfile.user)).filter_by(user_id=user_id).first()
            except IntegrityError:
                db.session.rollback()
                self.logger.warning(f"Race condition creating profile for user {user_id}, fetching existing.")
                profile = UserProfile.query.options(joinedload(UserProfile.user)).filter_by(user_id=user_id).first()
        return profile

    def get_profile(self, user_id: int):
        profile = self._get_or_create_profile(user_id)
        profile_dict = profile.to_dict()
        # Add user fields to the response dictionary
        if profile.user:
            profile_dict['full_name'] = profile.user.full_name
            # The login email from Clerk is on the user table, the contact email is on the profile
            profile_dict['login_email'] = profile.user.email 
        return profile_dict

    def update_profile(self, user_id: int, data: dict):
        profile = self._get_or_create_profile(user_id)
        if not profile.user:
            self.logger.error(f"UserProfile {profile.id} is missing its associated User object.")
            # Handle this case, maybe by fetching the user separately
            profile.user = User.query.get(user_id)
            if not profile.user:
                raise Exception(f"Could not find User with ID {user_id}")
        
        for key, value in data.items():
            if key in self.user_model_fields:
                setattr(profile.user, key, value)
            elif key in self.profile_model_fields:
                if key in self.enum_fields:
                    setattr(profile, key, value)
                elif key in ['latitude', 'longitude'] and value is not None:
                    try: setattr(profile, key, float(value))
                    except (ValueError, TypeError): setattr(profile, key, None)
                elif key == 'is_remote_preferred':
                    setattr(profile, key, bool(value))
                elif key in ['desired_salary_min', 'desired_salary_max'] and value is not None:
                    try:
                        clean_value = int(str(value).replace(',', '')) if value else None
                        setattr(profile, key, clean_value)
                    except (ValueError, TypeError): setattr(profile, key, None)
                else:
                    setattr(profile, key, value if value not in [None, ''] else None)
        
        profile.updated_at = datetime.now(pytz.utc)
        profile.user.updated_at = datetime.now(pytz.utc)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise e

        return self.get_profile(user_id)

    def enrich_profile(self, user_id: int, ai_data: dict):
        profile = self._get_or_create_profile(user_id)
        update_data = {}
        for key, value in ai_data.items():
            if key in self.allowed_fields and getattr(profile, key, 'NOT_FOUND') is None:
                update_data[key] = value
        if update_data:
            self.update_profile(user_id, update_data)
        return self.get_profile(user_id)

    def get_profile_for_analysis(self, user_id: int):
        profile = self._get_or_create_profile(user_id)
        profile_dict = profile.to_dict()
        if profile.user:
            profile_dict['full_name'] = profile.user.full_name
        profile_dict.pop('id', None)
        profile_dict.pop('user_id', None)
        return profile_dict

    def has_completed_required_profile_fields(self, user_id: int):
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        if not profile: return False
        has_title = profile.desired_job_titles and profile.desired_job_titles.strip()
        has_resume = ResumeSubmission.query.filter_by(user_id=user_id, is_active=True).first() is not None
        return has_title and has_resume