# apps/backend/models.py
from .app import db
from datetime import datetime
import pytz
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import text, Index

def get_utc_now():
    return datetime.now(pytz.utc)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    clerk_user_id = db.Column(db.String(255), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    full_name = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=True)

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
    preferred_company_size = db.Column(db.Enum('SMALL_BUSINESS', 'MEDIUM_BUSINESS', 'LARGE_ENTERPRISE', 'STARTUP', 'NO_PREFERENCE', name='company_size_enum', native_enum=True), nullable=True)
    work_style_preference = db.Column(db.Enum('STRUCTURED', 'AUTONOMOUS', 'COLLABORATIVE', 'HYBRID', 'NO_PREFERENCE', name='work_style_type_enum', native_enum=True), nullable=True)
    conflict_resolution_style = db.Column(db.Enum('DIRECT', 'MEDIATED', 'AVOIDANT', 'NO_PREFERENCE', name='conflict_resolution_enum', native_enum=True), nullable=True)
    communication_preference = db.Column(db.Enum('WRITTEN', 'VERBAL', 'VISUAL', 'NO_PREFERENCE', name='communication_pref_enum', native_enum=True), nullable=True)
    change_tolerance = db.Column(db.Enum('HIGH', 'MEDIUM', 'LOW', 'NO_PREFERENCE', name='change_tolerance_enum', native_enum=True), nullable=True)
    preferred_work_style = db.Column(db.Enum('ON_SITE', 'REMOTE', 'HYBRID', 'NO_PREFERENCE', name='work_location_enum', native_enum=True), nullable=True)
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
            'preferred_company_size': self.preferred_company_size,
            'work_style_preference': self.work_style_preference,
            'conflict_resolution_style': self.conflict_resolution_style,
            'communication_preference': self.communication_preference,
            'change_tolerance': self.change_tolerance,
            'preferred_work_style': self.preferred_work_style,
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
    job_modality = db.Column(db.Enum('ON_SITE', 'REMOTE', 'HYBRID', name='job_modality_enum', native_enum=True), nullable=True)
    deduced_job_level = db.Column(db.Enum('ENTRY', 'ASSOCIATE', 'MID', 'SENIOR', 'LEAD', 'PRINCIPAL', 'DIRECTOR', 'VP', 'EXECUTIVE', name='job_level_enum', native_enum=True), nullable=True)
    job_description_hash = db.Column(db.Text, nullable=True)

    company = db.relationship('Company', backref=db.backref('jobs', lazy=True))

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
    status = db.Column(db.Enum('SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS', 'OFFER_ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXPIRED', name='tracked_job_status_enum', native_enum=True), nullable=False, default='SAVED')
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
            'status': self.status,
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