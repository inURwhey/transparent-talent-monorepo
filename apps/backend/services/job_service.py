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
from ..models import Job, Company, JobAnalysis, User, JobOpportunity
from ..config import config
from .profile_service import ProfileService

MAX_RESUME_TEXT_LENGTH = 25000
MAX_JOB_TEXT_LENGTH = 50000

class JobService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.profile_service = ProfileService(self.logger)

    def _call_gemini_api(self, prompt, model_name="gemini-1.5-pro-latest"):
        api_key = config.GEMINI_API_KEY
        if not api_key:
            self.logger.error("Gemini API key is not configured.")
            return None

        # CORRECTED: Reverted to the simpler, working v1beta endpoint and payload structure.
        # Removed the 'generationConfig' that was causing the 400 Bad Request error.
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        headers = { "Content-Type": "application/json" }
        payload = { "contents": [{"parts": [{"text": prompt}]}] }

        try:
            self.logger.info(f"Calling Gemini API with model {model_name}")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # Reinstated robust parsing from the original working version.
            text_content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            if not text_content:
                self.logger.error("Gemini API returned an empty text response.", extra={'full_response': data})
                return None
            
            return text_content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Gemini API: {e}")
            if e.response is not None:
                self.logger.error(f"Gemini API Response Status: {e.response.status_code}")
                self.logger.error(f"Gemini API Response Body: {e.response.text}")
            return None
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error parsing Gemini API response structure: {e}", extra={'full_response': data})
            return None

    def _extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text

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

            return {
                "title": title[:255],
                "company_name": company_name[:255],
                "description": description[:MAX_JOB_TEXT_LENGTH],
                "extracted_location": None
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during lightweight scrape of {url}: {e}")
            return None

    def _validate_enum(self, value, enum_class):
        if value is None: return None
        try:
            if isinstance(value, enum_class): return value
            return enum_class[value.upper().replace('-', '_')]
        except (KeyError, AttributeError):
            self.logger.warning(f"Invalid ENUM value '{value}' for {enum_class.__name__}. Setting to None.")
            return None

    def _parse_and_validate_int(self, value):
        if value is None or value == '': return None
        try:
            return int(value)
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid integer value '{value}'. Setting to None.")
            return None
            
    def _parse_ai_response(self, ai_response_text):
        try:
            # Reinstated robust JSON extraction from markdown code fences.
            match = re.search(r"```json\n(.+?)\n```", ai_response_text, re.DOTALL)
            json_string = match.group(1) if match else ai_response_text
            parsed_data = json.loads(json_string)
            
            parsed_data['job_title'] = parsed_data.get('job_title', 'Unknown Title').strip()
            parsed_data['company_name'] = parsed_data.get('company_name', 'Unknown Company').strip()
            
            parsed_data['salary_min'] = self._parse_and_validate_int(parsed_data.get('salary_min'))
            parsed_data['salary_max'] = self._parse_and_validate_int(parsed_data.get('salary_max'))
            parsed_data['required_experience_years'] = self._parse_and_validate_int(parsed_data.get('required_experience_years'))
            
            job_modality_enum = Job.job_modality.type.enum_class
            deduced_job_level_enum = Job.deduced_job_level.type.enum_class

            parsed_data['job_modality'] = self._validate_enum(parsed_data.get('job_modality'), job_modality_enum)
            parsed_data['deduced_job_level'] = self._validate_enum(parsed_data.get('deduced_job_level'), deduced_job_level_enum)

            matrix_rating = parsed_data.get('matrix_rating', 'N/A')
            parsed_data['matrix_rating'] = str(matrix_rating)[:50]

            return parsed_data
        except (json.JSONDecodeError, AttributeError) as e:
            self.logger.error(f"Failed to decode or parse JSON from AI response: {e}. Raw text: {ai_response_text}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing AI response: {e}. Raw text: {ai_response_text}")
            return None

    def analyze_job_posting(self, job_text, user_profile_data, company_profile_data=None):
        if not job_text:
            return {"error": "Job text is empty for AI analysis."}
        if len(job_text) > MAX_JOB_TEXT_LENGTH:
            job_text = job_text[:MAX_JOB_TEXT_LENGTH]

        profile_str = json.dumps(user_profile_data, indent=2) if user_profile_data else "{}"
        company_str = json.dumps(company_profile_data, indent=2) if company_profile_data else "{}"

        prompt = f"""
        Analyze the following job posting and user profile to determine the candidate's fit.
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

        Strictly conform to the JSON structure. If a field cannot be determined, use null or appropriate default.
        Your response MUST be valid JSON wrapped in ```json ... ```.
        """
        self.logger.info("Sending job posting to Gemini for analysis.")
        ai_response = self._call_gemini_api(prompt, model_name="gemini-1.5-pro-latest")

        if ai_response:
            return self._parse_ai_response(ai_response)
        
        self.logger.error("AI analysis failed or returned no data.")
        return None
    
    def create_or_get_canonical_job(self, url: str, user_id: int, commit: bool = True):
        existing_opportunity = JobOpportunity.query.filter_by(url=url).first()
        if existing_opportunity and existing_opportunity.job:
            existing_opportunity.updated_at = datetime.now(pytz.utc)
            if commit: db.session.commit()
            return existing_opportunity.job, existing_opportunity

        scraped_data = self._lightweight_scrape(url)
        if not scraped_data:
            return None, None
        
        job_title = scraped_data.get('title')
        company_name = scraped_data.get('company_name')
        job_description = scraped_data.get('description')

        if not company_name or not job_title or not job_description:
            return None, None

        company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()
        if not company:
            company = Company(name=company_name)
            db.session.add(company)
            if commit: 
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()

        canonical_job = Job.query.filter(
            Job.company_id == company.id,
            db.func.lower(Job.job_title) == job_title.lower()
        ).first()

        if not canonical_job:
            company_profile_for_ai = company.to_dict() if company else {}
            ai_analysis_data = self.analyze_job_posting(job_description, {}, company_profile_for_ai)
            
            if not ai_analysis_data: ai_analysis_data = {}

            job_desc_hash = hashlib.sha256(job_description.encode('utf-8')).hexdigest()

            canonical_job = Job(
                company_id=company.id if company else None,
                company_name=company_name,
                job_title=ai_analysis_data.get('job_title', job_title),
                status='Active',
                job_description_hash=job_desc_hash,
                salary_min=ai_analysis_data.get('salary_min'),
                salary_max=ai_analysis_data.get('salary_max'),
                required_experience_years=ai_analysis_data.get('required_experience_years'),
                job_modality=ai_analysis_data.get('job_modality'),
                deduced_job_level=ai_analysis_data.get('deduced_job_level'),
                notes=job_description
            )
            db.session.add(canonical_job)
            if commit: db.session.commit()
            
            profile_service = ProfileService(self.logger)
            if user_id and profile_service.has_completed_required_profile_fields(user_id):
                user_profile_data = profile_service.get_profile_for_analysis(user_id)
                self.create_or_update_job_analysis(user_id, canonical_job.id, ai_analysis_data)

        if existing_opportunity:
            existing_opportunity.job_id = canonical_job.id
            new_opportunity = existing_opportunity
        else:
            new_opportunity = JobOpportunity(job_id=canonical_job.id, url=url)
            db.session.add(new_opportunity)
        
        if commit: db.session.commit()

        return canonical_job, new_opportunity

    def create_or_update_job_analysis(self, user_id, job_id, ai_analysis_data):
        if not ai_analysis_data:
            self.logger.warning(f"No AI analysis data provided for user {user_id}, job {job_id}. Skipping update.")
            return None

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
        
        try:
            db.session.commit()
            return analysis
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating/updating job analysis: {e}")
            raise e

    def trigger_reanalysis_for_user(self, user_id: int):
        user_profile_data = self.profile_service.get_profile_for_analysis(user_id)
        if not user_profile_data:
            return

        jobs_to_reanalyze = db.session.query(Job).join(
            JobOpportunity
        ).join(
            TrackedJob, TrackedJob.job_opportunity_id == JobOpportunity.id
        ).filter(TrackedJob.user_id == user_id).options(
            joinedload(Job.company)
        ).distinct().all()

        for job in jobs_to_reanalyze:
            company_data = job.company.to_dict() if job.company else None
            job_description = job.notes
            if job_description:
                ai_analysis_data = self.analyze_job_posting(job_description, user_profile_data, company_data)
                if ai_analysis_data:
                    self.create_or_update_job_analysis(user_id, job.id, ai_analysis_data)