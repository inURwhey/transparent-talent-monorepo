# apps/backend/models.py
from apps.backend.app import db # Import db from app.py now
from datetime import datetime
import pytz

# Helper for timezone-aware default timestamps
def get_utc_now():
    return datetime.now(pytz.utc)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    clerk_user_id = db.Column(db.String(255), unique=True, nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    full_name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

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
    # Contact & Basic Information
    phone_number = db.Column(db.String(50))
    linkedin_url = db.Column(db.String(255))
    github_url = db.Column(db.String(255))
    portfolio_url = db.Column(db.String(255))
    location = db.Column(db.String(255))
    latitude = db.Column(db.Numeric(precision=10, scale=8))
    longitude = db.Column(db.Numeric(precision=11, scale=8))
    # Career Aspirations
    current_role = db.Column(db.String(255))
    desired_job_titles = db.Column(db.Text)
    desired_salary_min = db.Column(db.Integer)
    desired_salary_max = db.Column(db.Integer)
    target_industries = db.Column(db.Text)
    career_goals = db.Column(db.Text)
    # Work Environment & Requirements
    preferred_company_size = db.Column(db.Enum('SMALL_BUSINESS', 'MEDIUM_BUSINESS', 'LARGE_ENTERPRISE', 'STARTUP', 'NO_PREFERENCE', name='company_size_enum'))
    work_style_preference = db.Column(db.Enum('STRUCTURED', 'AUTONOMOUS', 'COLLABORATIVE', 'HYBRID', 'NO_PREFERENCE', name='work_style_type_enum'))
    conflict_resolution_style = db.Column(db.Enum('DIRECT', 'MEDIATED', 'AVOIDANT', 'NO_PREFERENCE', name='conflict_resolution_enum'))
    communication_preference = db.Column(db.Enum('WRITTEN', 'VERBAL', 'VISUAL', 'NO_PREFERENCE', name='communication_pref_enum'))
    change_tolerance = db.Column(db.Enum('HIGH', 'MEDIUM', 'LOW', 'NO_PREFERENCE', name='change_tolerance_enum'))
    preferred_work_style = db.Column(db.Enum('ON_SITE', 'REMOTE', 'HYBRID', 'NO_PREFERENCE', name='work_location_enum'))
    is_remote_preferred = db.Column(db.Boolean, default=False)
    # Skills & Industry Focus (to be populated by resume parsing or manual input)
    skills = db.Column(db.Text)
    education = db.Column(db.Text)
    work_experience = db.Column(db.Text)
    # Personality & Self-Assessment (from resume parsing or manual input)
    personality_16_personalities = db.Column(db.String(50)) # e.g., 'INTJ', 'ESTP'
    other_personal_attributes = db.Column(db.Text) # Open text for other self-assessment
    # Onboarding Status
    has_completed_onboarding = db.Column(db.Boolean, default=False)

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
    industry = db.Column(db.String(255))
    description = db.Column(db.Text)
    mission = db.Column(db.Text)
    business_model = db.Column(db.Text)
    company_size_min = db.Column(db.Integer)
    company_size_max = db.Column(db.Integer)
    headquarters = db.Column(db.String(255))
    founded_year = db.Column(db.Integer)
    website_url = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

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

# NEW MODEL: JobOpportunity
class JobOpportunity(db.Model):
    __tablename__ = 'job_opportunities'
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False) # FK to the canonical Job
    url = db.Column(db.Text, unique=True, nullable=False) # Unique URL for this specific opportunity
    source_platform = db.Column(db.Text)
    posted_at = db.Column(db.DateTime(timezone=True))
    extracted_location = db.Column(db.Text) # Location as explicitly found on this posting URL
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_checked_at = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationship to the canonical Job
    job = db.relationship('Job', backref='opportunities') # backref 'opportunities' added to Job model

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

# MODIFIED MODEL: Job
class Job(db.Model):
    __tablename__ = 'jobs'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id', ondelete='CASCADE'))
    company_name = db.Column(db.String(255))
    job_title = db.Column(db.Text, nullable=False)
    # job_url = db.Column(db.Text, unique=True) # REMOVED THIS COLUMN - handled by JobOpportunity
    source = db.Column(db.String(255)) # This column might become redundant or repurposed later
    notes = db.Column(db.Text)
    found_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    status = db.Column(db.String(50), nullable=False, default='Active') # This 'status' refers to the job posting itself
    last_checked_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    salary_min = db.Column(db.Integer)
    salary_max = db.Column(db.Integer)
    required_experience_years = db.Column(db.Integer)
    job_modality = db.Column(db.Enum('ON_SITE', 'REMOTE', 'HYBRID', name='job_modality_enum'))
    deduced_job_level = db.Column(db.Enum('ENTRY', 'ASSOCIATE', 'MID', 'SENIOR', 'LEAD', 'PRINCIPAL', 'DIRECTOR', 'VP', 'EXECUTIVE', name='job_level_enum'))
    job_description_hash = db.Column(db.Text) # NEW COLUMN: A hash of the canonical job description

    # Relationships
    company = db.relationship('Company', backref='jobs')
    # 'opportunities' backref is now automatically added via JobOpportunity model

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

# MODIFIED MODEL: TrackedJob
class TrackedJob(db.Model):
    __tablename__ = 'tracked_jobs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False) # OLD COLUMN
    job_opportunity_id = db.Column(db.Integer, db.ForeignKey('job_opportunities.id', ondelete='CASCADE'), nullable=False) # NEW COLUMN
    applied_at = db.Column(db.DateTime(timezone=True))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    is_excited = db.Column(db.Boolean, default=False)
    status = db.Column(db.Enum('SAVED', 'APPLIED', 'INTERVIEWING', 'OFFER_NEGOTIATIONS', 'OFFER_ACCEPTED', 'REJECTED', 'WITHDRAWN', 'EXPIRED', name='tracked_job_status_enum'), nullable=False, default='SAVED')
    status_reason = db.Column(db.Text)
    first_interview_at = db.Column(db.DateTime(timezone=True))
    offer_received_at = db.Column(db.DateTime(timezone=True))
    resolved_at = db.Column(db.DateTime(timezone=True))
    next_action_at = db.Column(db.DateTime(timezone=True))
    next_action_notes = db.Column(db.Text)

    # Relationships
    user = db.relationship('User', backref='tracked_jobs')
    job_opportunity = db.relationship('JobOpportunity', backref=db.backref('tracked_by_users', lazy=True)) # Added lazy=True

    def to_dict(self):
        # This will be updated further in the next step to fetch nested job and company data
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
            # 'job_opportunity': self.job_opportunity.to_dict() if self.job_opportunity else None, # Relationship needs to be manually fetched
        }

# MODIFIED MODEL: JobAnalysis
class JobAnalysis(db.Model):
    __tablename__ = 'job_analyses'
    # Primary key is (job_id, user_id)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id', ondelete='CASCADE'), primary_key=True) # This still links to the canonical Job
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    position_relevance_score = db.Column(db.Integer)
    environment_fit_score = db.Column(db.Integer)
    hiring_manager_view = db.Column(db.Text)
    matrix_rating = db.Column(db.String(50))
    summary = db.Column(db.Text)
    qualification_gaps = db.Column(db.JSONB)
    recommended_testimonials = db.Column(db.JSONB)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)
    analysis_protocol_version = db.Column(db.String(20), nullable=False)

    # Relationships
    job = db.relationship('Job', backref=db.backref('analyses', lazy=True)) # Added lazy=True
    user = db.relationship('User', backref=db.backref('job_analyses', lazy=True)) # Added lazy=True

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
            'analysis_protocol_version': self.analysis_protocol_version,
        }

class ResumeSubmission(db.Model):
    __tablename__ = 'resume_submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, nullable=False)
    source = db.Column(db.String(50)) # e.g., 'file_upload', 'copy_paste'
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'is_active', name='_user_active_resume_uc',
                            postgresql_where=db.text('is_active IS TRUE')),
    )

    user = db.relationship('User', backref=db.backref('resume_submissions', lazy=True)) # Added lazy=True

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'source': self.source,
            'is_active': self.is_active,
            'raw_text_length': len(self.raw_text) # Don't return raw text for security/payload size
        }

class JobOffer(db.Model):
    __tablename__ = 'job_offers'
    id = db.Column(db.Integer, primary_key=True)
    tracked_job_id = db.Column(db.Integer, db.ForeignKey('tracked_jobs.id', ondelete='CASCADE'), nullable=False)
    salary = db.Column(db.Integer)
    bonus = db.Column(db.Integer)
    equity = db.Column(db.Text) # Stored as text for flexibility (e.g., "0.1% shares", "1000 RSUs")
    is_accepted = db.Column(db.Boolean, default=False, nullable=False)
    offer_date = db.Column(db.DateTime(timezone=True))
    expiration_date = db.Column(db.DateTime(timezone=True))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=get_utc_now)
    updated_at = db.Column(db.DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    tracked_job = db.relationship('TrackedJob', backref=db.backref('offers', uselist=True, lazy=True)) # Added lazy=True

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