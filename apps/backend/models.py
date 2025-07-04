# apps/backend/models.py
from .app import db
from datetime import datetime
import pytz
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text, Index
import enum

def get_utc_now():
    return datetime.now(pytz.utc)

# --- Enum Definitions ---
class CompanySizeEnum(enum.Enum):
    SMALL_BUSINESS = 'SMALL_BUSINESS'
    MEDIUM_BUSINESS = 'MEDIUM_BUSINESS'
    LARGE_ENTERPRISE = 'LARGE_ENTERPRISE'
    STARTUP = 'STARTUP'
    NO_PREFERENCE = 'NO_PREFERENCE'

class WorkStyleTypeEnum(enum.Enum):
    STRUCTURED = 'STRUCTURED'
    AUTONOMOUS = 'AUTONOMOUS'
    COLLABORATIVE = 'COLLABORATIVE'
    HYBRID = 'HYBRID'
    NO_PREFERENCE = 'NO_PREFERENCE'

class ConflictResolutionEnum(enum.Enum):
    DIRECT = 'DIRECT'
    MEDIATED = 'MEDIATED'
    AVOIDANT = 'AVOIDANT'
    NO_PREFERENCE = 'NO_PREFERENCE'

class CommunicationPrefEnum(enum.Enum):
    WRITTEN = 'WRITTEN'
    VERBAL = 'VERBAL'
    VISUAL = 'VISUAL'
    NO_PREFERENCE = 'NO_PREFERENCE'

class ChangeToleranceEnum(enum.Enum):
    HIGH = 'HIGH'
    MEDIUM = 'MEDIUM'
    LOW = 'LOW'
    NO_PREFERENCE = 'NO_PREFERENCE'

class WorkLocationEnum(enum.Enum):
    ON_SITE = 'ON_SITE'
    REMOTE = 'REMOTE'
    HYBRID = 'HYBRID'
    NO_PREFERENCE = 'NO_PREFERENCE'

class JobModalityEnum(enum.Enum):
    ON_SITE = 'ON_SITE'
    REMOTE = 'REMOTE'
    HYBRID = 'HYBRID'

class JobLevelEnum(enum.Enum):
    ENTRY = 'ENTRY'
    ASSOCIATE = 'ASSOCIATE'
    MID = 'MID'
    SENIOR = 'SENIOR'
    LEAD = 'LEAD'
    PRINCIPAL = 'PRINCIPAL'
    DIRECTOR = 'DIRECTOR'
    VP = 'VP'
    EXECUTIVE = 'EXECUTIVE'

class TrackedJobStatusEnum(enum.Enum):
    SAVED = 'SAVED'
    APPLIED = 'APPLIED'
    INTERVIEWING = 'INTERVIEWING'
    OFFER_NEGOTIATIONS = 'OFFER_NEGOTIATIONS'
    OFFER_ACCEPTED = 'OFFER_ACCEPTED'
    REJECTED = 'REJECTED'
    WITHDRAWN = 'WITHDRAWN'
    EXPIRED = 'EXPIRED'


# --- Model Definitions ---

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    clerk_user_id = db.Column(db.String(255), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    full_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'clerk_user_id': self.clerk_user_id,
            'email': self.email,
            'full_name': self.full_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    phone_number = db.Column(db.String(50), nullable=True)
    linkedin_url = db.Column(db.String(255), nullable=True)
    github_url = db.Column(db.String(255), nullable=True)
    portfolio_url = db.Column(db.String(255), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    latitude = db.Column(db.Numeric(precision=10, scale=8), nullable=True)
    longitude = db.Column(db.Numeric(precision=11, scale=8), nullable=True)
    current_role = db.Column(db.String(255), nullable=True)
    desired_job_titles = db.Column(db.Text, nullable=True)
    desired_salary_min = db.Column(db.Integer, nullable=True)
    desired_salary_max = db.Column(db.Integer, nullable=True)
    target_industries = db.Column(db.Text, nullable=True)
    career_goals = db.Column(db.Text, nullable=True)
    preferred_company_size = db.Column(db.Enum(CompanySizeEnum, name='company_size_enum', native_enum=True), nullable=True)
    work_style_preference = db.Column(db.Enum(WorkStyleTypeEnum, name='work_style_type_enum', native_enum=True), nullable=True)
    conflict_resolution_style = db.Column(db.Enum(ConflictResolutionEnum, name='conflict_resolution_enum', native_enum=True), nullable=True)
    communication_preference = db.Column(db.Enum(CommunicationPrefEnum, name='communication_pref_enum', native_enum=True), nullable=True)
    change_tolerance = db.Column(db.Enum(ChangeToleranceEnum, name='change_tolerance_enum', native_enum=True), nullable=True)
    preferred_work_style = db.Column(db.Enum(WorkLocationEnum, name='work_location_enum', native_enum=True), nullable=True)
    is_remote_preferred = db.Column(db.Boolean, default=False, nullable=True)
    skills = db.Column(db.Text, nullable=True)
    education = db.Column(db.Text, nullable=True)
    work_experience = db.Column(db.Text, nullable=True)
    personality_16_personalities = db.Column(db.String(50), nullable=True)
    other_personal_attributes = db.Column(db.Text, nullable=True)
    has_completed_onboarding = db.Column(db.Boolean, default=False, nullable=True)

    user = db.relationship('User', backref=db.backref('profile', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'phone_number': self.phone_number,
            'linkedin_url': self.linkedin_url,
            'github_url': self.github_url,
            'portfolio_url': self.portfolio_url,
            'location': self.location,
            'latitude': float(self.latitude) if self.latitude is not None else None,
            'longitude': float(self.longitude) if self.longitude is not None else None,
            'current_role': self.current_role,
            'desired_job_titles': self.desired_job_titles,
            'desired_salary_min': self.desired_salary_min,
            'desired_salary_max': self.desired_salary_max,
            'target_industries': self.target_industries,
            'career_goals': self.career_goals,
            'preferred_company_size': self.preferred_company_size.value if self.preferred_company_size else None,
            'work_style_preference': self.work_style_preference.value if self.work_style_preference else None,
            'conflict_resolution_style': self.conflict_resolution_style.value if self.conflict_resolution_style else None,
            'communication_preference': self.communication_preference.value if self.communication_preference else None,
            'change_tolerance': self.change_tolerance.value if self.change_tolerance else None,
            'preferred_work_style': self.preferred_work_style.value if self.preferred_work_style else None,
            'is_remote_preferred': self.is_remote_preferred,
            'skills': self.skills,
            'education': self.education,
            'work_experience': self.work_experience,
            'personality_16_personalities': self.personality_16_personalities,
            'other_personal_attributes': self.other_personal_attributes,
            'has_completed_onboarding': self.has_completed_onboarding
        }

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    industry = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    mission = db.Column(db.Text, nullable=True)
    business_model = db.Column(db.Text, nullable=True)
    company_size_min = db.Column(db.Integer, nullable=True)
    company_size_max = db.Column(db.Integer, nullable=True)
    headquarters = db.Column(db.String(255), nullable=True)
    founded_year = db.Column(db.Integer, nullable=True)
    website_url = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'industry': self.industry,
            'description': self.description,
            'mission': self.mission,
            'business_model': self.business_model,
            'company_size_min': self.company_size_min,
            'company_size_max': self.company_size_max,
            'headquarters': self.headquarters,
            'founded_year': self.founded_year,
            'website_url': self.website_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class JobOpportunity(db.Model):
    __tablename__ = 'job_opportunities'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False)
    url = db.Column(db.Text, unique=True, nullable=False)
    source_platform = db.Column(db.Text, nullable=True)
    posted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    extracted_location = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_checked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    job = db.relationship('Job', backref=db.backref('opportunities', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'url': self.url,
            'source_platform': self.source_platform,
            'posted_at': self.posted_at.isoformat() if self.posted_at else None,
            'extracted_location': self.extracted_location,
            'is_active': self.is_active,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'), nullable=True)
    company_name = db.Column(db.String(255), nullable=True)
    job_title = db.Column(db.Text, nullable=False)
    source = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    found_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Active')
    last_checked_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)
    salary_max = db.Column(db.Integer, nullable=True)
    required_experience_years = db.Column(db.Integer, nullable=True)
    job_modality = db.Column(db.Enum(JobModalityEnum, name='job_modality_enum', native_enum=True), nullable=True)
    deduced_job_level = db.Column(db.Enum(JobLevelEnum, name='job_level_enum', native_enum=True), nullable=True)
    job_description_hash = db.Column(db.Text, nullable=True)

    company = db.relationship('Company', backref=db.backref('jobs', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'company_name': self.company_name,
            'job_title': self.job_title,
            'source': self.source,
            'notes': self.notes,
            'found_at': self.found_at.isoformat() if self.found_at else None,
            'status': self.status,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
            'salary_min': self.salary_min,
            'salary_max': self.salary_max,
            'required_experience_years': self.required_experience_years,
            'job_modality': self.job_modality.value if self.job_modality else None,
            'deduced_job_level': self.deduced_job_level.value if self.deduced_job_level else None,
            'job_description_hash': self.job_description_hash,
        }

class TrackedJob(db.Model):
    __tablename__ = 'tracked_jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_opportunity_id = db.Column(db.Integer, db.ForeignKey('job_opportunities.id', ondelete='CASCADE'), nullable=False)
    applied_at = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=True)
    is_excited = db.Column(db.Boolean, default=False, nullable=True)
    status = db.Column(db.Enum(TrackedJobStatusEnum, name='tracked_job_status_enum', native_enum=True), nullable=False, default=TrackedJobStatusEnum.SAVED)
    status_reason = db.Column(db.Text, nullable=True)
    first_interview_at = db.Column(db.DateTime(timezone=True), nullable=True)
    offer_received_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    next_action_at = db.Column(db.DateTime(timezone=True), nullable=True)
    next_action_notes = db.Column(db.Text, nullable=True)

    user = db.relationship('User', backref=db.backref('tracked_jobs', lazy=True))
    job_opportunity = db.relationship('JobOpportunity', backref=db.backref('tracked_by_users', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_opportunity_id': self.job_opportunity_id,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_excited': self.is_excited,
            'status': self.status.value if self.status else None,
            'status_reason': self.status_reason,
            'first_interview_at': self.first_interview_at.isoformat() if self.first_interview_at else None,
            'offer_received_at': self.offer_received_at.isoformat() if self.offer_received_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'next_action_at': self.next_action_at.isoformat() if self.next_action_at else None,
            'next_action_notes': self.next_action_notes,
        }

class JobAnalysis(db.Model):
    __tablename__ = 'job_analyses'
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    position_relevance_score = db.Column(db.Integer, nullable=True)
    environment_fit_score = db.Column(db.Integer, nullable=True)
    hiring_manager_view = db.Column(db.Text, nullable=True)
    matrix_rating = db.Column(db.String(50), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    qualification_gaps = db.Column(JSONB, nullable=True)
    recommended_testimonials = db.Column(JSONB, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=True)
    analysis_protocol_version = db.Column(db.String(20), nullable=False)

    job = db.relationship('Job', backref=db.backref('analyses', lazy=True))
    user = db.relationship('User', backref=db.backref('job_analyses', lazy=True))

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'user_id': self.user_id,
            'position_relevance_score': self.position_relevance_score,
            'environment_fit_score': self.environment_fit_score,
            'hiring_manager_view': self.hiring_manager_view,
            'matrix_rating': self.matrix_rating,
            'summary': self.summary,
            'qualification_gaps': self.qualification_gaps,
            'recommended_testimonials': self.recommended_testimonials,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'analysis_protocol_version': self.analysis_protocol_version
        }

class ResumeSubmission(db.Model):
    __tablename__ = 'resume_submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=False)
    source = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        Index('_user_active_resume_idx', 'user_id', unique=True,
              postgresql_where=text('is_active IS TRUE')),
    )

    user = db.relationship('User', backref=db.backref('resume_submissions', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'raw_text': self.raw_text,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'source': self.source,
            'is_active': self.is_active
        }

class JobOffer(db.Model):
    __tablename__ = 'job_offers'
    id = db.Column(db.Integer, primary_key=True)
    tracked_job_id = db.Column(db.Integer, db.ForeignKey('tracked_jobs.id', ondelete='CASCADE'), nullable=False)
    salary = db.Column(db.Integer, nullable=True)
    bonus = db.Column(db.Integer, nullable=True)
    equity = db.Column(db.Text, nullable=True)
    is_accepted = db.Column(db.Boolean, default=False, nullable=False)
    offer_date = db.Column(db.DateTime(timezone=True), nullable=True)
    expiration_date = db.Column(db.DateTime(timezone=True), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=True)

    tracked_job = db.relationship('TrackedJob', backref=db.backref('offers', uselist=True, lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'tracked_job_id': self.tracked_job_id,
            'salary': self.salary,
            'bonus': self.bonus,
            'equity': self.equity,
            'is_accepted': self.is_accepted,
            'offer_date': self.offer_date.isoformat() if self.offer_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }