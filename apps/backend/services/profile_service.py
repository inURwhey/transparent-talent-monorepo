from psycopg2.extras import DictCursor
from ..database import get_db
from decimal import Decimal

class ProfileService:
    def __init__(self, logger):
        """
        Initializes the Profile Service.
        """
        self.logger = logger
        self.allowed_fields = [
            "full_name", "current_location", "linkedin_profile_url", "resume_url",
            "short_term_career_goal", "long_term_career_goals", "desired_annual_compensation",
            "desired_title", "ideal_role_description", "preferred_company_size",
            "ideal_work_culture", "disliked_work_culture", "core_strengths",
            "skills_to_avoid", "non_negotiable_requirements", "deal_breakers",
            "preferred_industries", "industries_to_avoid", "personality_adjectives",
            "personality_16_personalities", "personality_disc", "personality_gallup_strengths",
            "preferred_work_style", "is_remote_preferred", "latitude", "longitude",
            # --- NEW "LAYER 3" FIELDS ---
            "has_completed_onboarding", "work_style_preference",
            "conflict_resolution_style", "communication_preference", "change_tolerance"
        ]

    def get_profile(self, user_id: int):
        """
        Retrieves a user's profile. Creates a default one if it doesn't exist.
        """
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM user_profiles WHERE user_id = %s", (user_id,))
            profile = cursor.fetchone()

            if not profile:
                self.logger.info(f"No profile for user_id {user_id}. Creating default.")
                cursor.execute("INSERT INTO user_profiles (user_id) VALUES (%s) RETURNING *;", (user_id,))
                profile = cursor.fetchone()
                db.commit()

            return self._format_profile(profile, cursor.description)

    def get_profile_for_analysis(self, user_id: int):
        profile = self.get_profile(user_id)
        analysis_columns = [
            "short_term_career_goal", "ideal_role_description", "core_strengths",
            "skills_to_avoid", "preferred_industries", "industries_to_avoid",
            "desired_title", "non_negotiable_requirements", "deal_breakers",
            "preferred_work_style", "is_remote_preferred"
        ]
        profile_labels = {
            "short_term_career_goal": "Short-Term Career Goal", "ideal_role_description": "Ideal Role",
            "core_strengths": "Core Strengths", "skills_to_avoid": "Skills To Avoid",
            "preferred_industries": "Preferred Industries", "industries_to_avoid": "Industries To Avoid",
            "desired_title": "Desired Title", "non_negotiable_requirements": "Non-Negotiables",
            "deal_breakers": "Deal Breakers", "preferred_work_style": "Preferred Work Style",
            "is_remote_preferred": "Remote Preference"
        }
        profile_parts = []
        for col in analysis_columns:
            value = profile.get(col)
            if col == 'is_remote_preferred':
                if value: profile_parts.append(f"- {profile_labels[col]}: Yes, remote is preferred.")
                else: profile_parts.append(f"- {profile_labels[col]}: No, remote is not preferred.")
            elif value and str(value).strip():
                profile_parts.append(f"- {profile_labels[col]}: {value}")
        if len(profile_parts) <= 1:
             raise ValueError("User profile is too sparse. Please fill out your profile to enable analysis.")
        return "\n".join(profile_parts)

    def update_profile(self, user_id: int, data: dict):
        fields_to_update = []
        params = []
        for field, value in data.items():
            if field in self.allowed_fields:
                fields_to_update.append(f"{field} = %s")
                if field in ['is_remote_preferred', 'has_completed_onboarding']:
                    params.append(bool(value))
                else:
                    params.append(value if value else None)
        if not fields_to_update:
            self.logger.warning("Update profile called with no valid fields.")
            return None
        db = get_db()
        with db.cursor() as cursor:
            sql = f"UPDATE user_profiles SET {', '.join(fields_to_update)} WHERE user_id = %s RETURNING *;"
            params.append(user_id)
            cursor.execute(sql, tuple(params))
            updated_profile = cursor.fetchone()
            db.commit()
            return self._format_profile(updated_profile, cursor.description)

    def _format_profile(self, profile_row: DictCursor, description) -> dict:
        if not profile_row: return {}
        profile_dict = {}
        string_fields = [
            'full_name', 'current_location', 'linkedin_profile_url', 'resume_url',
            'short_term_career_goal', 'long_term_career_goals', 'desired_annual_compensation',
            'desired_title', 'ideal_role_description', 'preferred_company_size',
            'ideal_work_culture', 'disliked_work_culture', 'core_strengths', 'skills_to_avoid',
            'preferred_industries', 'industries_to_avoid', 'personality_adjectives',
            'personality_16_personalities', 'personality_disc', 'personality_gallup_strengths',
            'preferred_work_style', 'non_negotiable_requirements', 'deal_breakers',
            'work_style_preference', 'conflict_resolution_style', 'communication_preference', 'change_tolerance'
        ]
        for col in description:
            col_name = col.name
            value = profile_row[col_name]
            if isinstance(value, Decimal):
                profile_dict[col_name] = float(value)
            elif col_name in string_fields and value is None:
                profile_dict[col_name] = ""
            elif col_name in ['is_remote_preferred', 'has_completed_onboarding'] and value is None:
                profile_dict[col_name] = False
            else:
                profile_dict[col_name] = value
        return profile_dict