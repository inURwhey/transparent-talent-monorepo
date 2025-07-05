# Path: apps/backend/services/job_service.py
import requests
from bs4 import BeautifulSoup
import json
import re
from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from datetime import datetime
import pytz
import hashlib

from ..app import db
from ..models import Job, Company, JobAnalysis, User, JobOpportunity, TrackedJob
from ..config import config
from .profile_service import ProfileService
from .company_service import CompanyService

MAX_RESUME_TEXT_LENGTH = 25000
MAX_JOB_TEXT_LENGTH = 50000

GEMINI_FLASH_MODEL = "gemini-1.5-flash"
GEMINI_PRO_MODEL = "gemini-1.5-pro"

class JobService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.profile_service = ProfileService(self.logger)
        self.company_service = CompanyService(self.logger)

    def _call_gemini_api(self, prompt, model_name=GEMINI_PRO_MODEL):
        api_key = config.GEMINI_API_KEY
        if not api_key:
            self.logger.error("Gemini API key is not configured.")
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        
        headers = { 
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        payload = { "contents": [{"parts": [{"text": prompt}]}] }

        try:
            self.logger.info(f"Calling Gemini with model {model_name} on endpoint {url}")
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            
            candidates = data.get('candidates', [])
            if not candidates:
                self.logger.error("Gemini API returned no candidates.", extra={'full_response': data})
                return None
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                self.logger.error("Gemini API returned no parts in content.", extra={'full_response': data})
                return None

            text_content = parts[0].get('text', '')
            if not text_content:
                self.logger.error("Gemini API returned empty text response.", extra={'full_response': data})
                return None
            
            return text_content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            if e.response is not None:
                self.logger.error(f"Gemini API Response Status: {e.response.status_code}")
                self.logger.error(f"Gemini API Response Body: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Error in Gemini API call or response parsing: {e}", exc_info=True)
            return None

    def _extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return '\n'.join(chunk for chunk in chunks if chunk)

    def _lightweight_scrape(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            title = soup.find('title').get_text(strip=True) if soup.find('title') else 'Unknown Title'
            company_name = 'Unknown Company'
            meta_og_site_name = soup.find('meta', property='og:site_name')
            if meta_og_site_name and meta_og_site_name.get('content'):
                company_name = meta_og_site_name.get('content')
            description = self._extract_text_from_html(html_content)
            return {"title": title[:255], "company_name": company_name[:255], "description": description}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during lightweight scrape of {url}: {e}")
            return None

    def _parse_ai_response(self, ai_response_text):
        try:
            match = re.search(r"```json\s*([\s\S]*?)\s*```", ai_response_text)
            json_string = match.group(1) if match else ai_response_text
            json_string = json_string.strip()
            json_string = re.sub(r",\s*(\n\s*[\}\]])", r"\1", json_string)
            return json.loads(json_string)
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}. Raw: {ai_response_text[:500]}")
            return None

    def analyze_job_posting(self, job_text, user_profile_data, company_profile_data=None):
        if not job_text: return None
        if len(job_text) > MAX_JOB_TEXT_LENGTH: job_text = job_text[:MAX_JOB_TEXT_LENGTH]
        profile_str = json.dumps(user_profile_data, indent=2) if user_profile_data else "{}"
        company_str = json.dumps(company_profile_data, indent=2) if company_profile_data else "{}"
        prompt = f"""
        Analyze the following job posting, user profile, and company context to determine the candidate's fit.
        Provide a JSON output matching the schema provided.

        User Profile:
        {profile_str}

        Job Posting:
        {job_text}

        Company Context:
        {company_str}

        Output a JSON object with the following structure.
        - job_title (string, max 255 chars)
        - company_name (string, max 255 chars)
        - salary_min (integer, nullable)
        - salary_max (integer, nullable)
        - required_experience_years (integer, nullable)
        - job_modality (enum: "ON_SITE", "REMOTE", "HYBRID", nullable)
        - deduced_job_level (enum: "ENTRY", "ASSOCIATE", "MID", "SENIOR", "LEAD", "PRINCIPAL", "DIRECTOR", "VP", "EXECUTIVE", nullable)
        - position_relevance_score (integer, 0-100)
        - environment_fit_score (integer, 0-100)
        - matrix_rating (string, e.g., "A+", "B-")
        - summary (string)
        - qualification_gaps (array of strings)
        - recommended_testimonials (array of strings)
        - hiring_manager_view (string)
        
        Strictly conform to the JSON structure. Your response MUST be valid JSON wrapped in ```json ... ```.
        """
        self.logger.info("Sending job posting to Gemini for analysis.")
        ai_response = self._call_gemini_api(prompt, model_name=GEMINI_PRO_MODEL)
        return self._parse_ai_response(ai_response) if ai_response else None

    def create_or_get_canonical_job(self, url: str, user_id: int, commit: bool = True):
        existing_opportunity = JobOpportunity.query.options(joinedload(JobOpportunity.job)).filter_by(url=url).first()
        if existing_opportunity and existing_opportunity.job:
            self.logger.info(f"Found existing opportunity for URL {url} linked to job {existing_opportunity.job.id}")
            return existing_opportunity.job, existing_opportunity

        scraped_data = self._lightweight_scrape(url)
        if not scraped_data: return None, None
        
        job_title, company_name, job_description = scraped_data.get('title'), scraped_data.get('company_name'), scraped_data.get('description')
        if not all([company_name, job_title, job_description]): return None, None

        company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()
        is_new_company = False
        if not company:
            self.logger.info(f"Creating new company: {company_name}")
            company = Company(name=company_name)
            db.session.add(company)
            if commit: 
                try:
                    db.session.commit()
                    is_new_company = True
                except IntegrityError:
                    db.session.rollback()
                    company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()
        
        if is_new_company and company:
            self.logger.info(f"New company created (ID: {company.id}). Triggering profile enrichment.")
            self.company_service.research_and_update_company_profile(company.id)
            # The result is not waited upon, allowing the request to complete faster.

        job_desc_hash = hashlib.sha256(job_description.encode('utf-8')).hexdigest()
        canonical_job = Job.query.filter_by(job_description_hash=job_desc_hash, company_id=company.id).first()

        if not canonical_job:
            self.logger.info(f"No canonical job found for hash. Creating new job for '{job_title}' at '{company_name}'.")
            
            ai_analysis_data = self.analyze_job_posting(job_description, {}, company.to_dict() if company else {})
            if not ai_analysis_data: ai_analysis_data = {}

            canonical_job = Job(
                company_id=company.id if company else None,
                company_name=ai_analysis_data.get('company_name', company_name),
                job_title=ai_analysis_data.get('job_title', job_title),
                status='Active',
                job_description_hash=job_desc_hash,
                notes=job_description
            )
            db.session.add(canonical_job)
            if commit: db.session.commit()
            
            if self.profile_service.has_completed_required_profile_fields(user_id):
                user_profile_data = self.profile_service.get_profile_for_analysis(user_id)
                user_specific_ai_data = self.analyze_job_posting(job_description, user_profile_data, company.to_dict() if company else {})
                if user_specific_ai_data:
                    self.create_or_update_job_analysis(user_id, canonical_job.id, user_specific_ai_data, commit=commit)

        new_opportunity = JobOpportunity.query.filter_by(url=url).first()
        if not new_opportunity:
            new_opportunity = JobOpportunity(job_id=canonical_job.id, url=url)
            db.session.add(new_opportunity)
            if commit: db.session.commit()
        elif new_opportunity.job_id != canonical_job.id:
            new_opportunity.job_id = canonical_job.id
            if commit: db.session.commit()

        return canonical_job, new_opportunity

    def create_or_update_job_analysis(self, user_id, job_id, ai_analysis_data, commit=True):
        if not ai_analysis_data: return None
        analysis = JobAnalysis.query.filter_by(user_id=user_id, job_id=job_id).first()
        if not analysis:
            analysis = JobAnalysis(job_id=job_id, user_id=user_id)
            db.session.add(analysis)

        analysis.position_relevance_score = ai_analysis_data.get('position_relevance_score')
        analysis.environment_fit_score = ai_analysis_data.get('environment_fit_score')
        analysis.hiring_manager_view = ai_analysis_data.get('hiring_manager_view')
        analysis.matrix_rating = ai_analysis_data.get('matrix_rating')
        analysis.summary = ai_analysis_data.get('summary')
        analysis.qualification_gaps = ai_analysis_data.get('qualification_gaps')
        analysis.recommended_testimonials = ai_analysis_data.get('recommended_testimonials')
        analysis.analysis_protocol_version = config.ANALYSIS_PROTOCOL_VERSION
        
        if commit:
            try: db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e
        return analysis

    def trigger_reanalysis_for_user(self, user_id: int):
        user_profile_data = self.profile_service.get_profile_for_analysis(user_id)
        if not user_profile_data: return

        jobs_to_reanalyze = db.session.query(Job).join(JobOpportunity).join(TrackedJob).filter(TrackedJob.user_id == user_id).distinct().all()
        
        self.logger.info(f"Found {len(jobs_to_reanalyze)} jobs to re-analyze for user {user_id}.")
        for job in jobs_to_reanalyze:
            company_data = job.company.to_dict() if job.company else {}
            if job.notes:
                ai_analysis_data = self.analyze_job_posting(job.notes, user_profile_data, company_data)
                if ai_analysis_data:
                    self.create_or_update_job_analysis(user_id, job.id, ai_analysis_data)