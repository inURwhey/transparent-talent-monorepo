# Path: apps/backend/services/job_service.py
import requests
from bs4 import BeautifulSoup
import json
import re
from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta
import pytz
import hashlib
from cachetools import cached, TTLCache

from ..app import db
from ..models import Job, Company, JobAnalysis, User, JobOpportunity
from ..config import config
from .profile_service import ProfileService

MAX_RESUME_TEXT_LENGTH = 25000
MAX_JOB_TEXT_LENGTH = 50000

# NEW: Dynamic Model Discovery with Caching
@cached(cache=TTLCache(maxsize=1, ttl=3600))
def get_available_models():
    """Fetches the list of available generative models from the Gemini API and caches the result."""
    current_app.logger.info("Fetching available Gemini models from API...")
    api_key = config.GEMINI_API_KEY
    if not api_key:
        current_app.logger.error("Cannot fetch models, Gemini API key is not configured.")
        return []

    url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        model_names = [model['name'] for model in data.get('models', []) if 'generateContent' in model.get('supportedGenerationMethods', [])]
        current_app.logger.info(f"Successfully fetched and cached available models: {[name.split('/')[-1] for name in model_names]}")
        return model_names
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Failed to fetch available models from Google API: {e}")
        return []

def select_generative_model(prefer_flash=False):
    """Selects the best available generative model from a dynamic list."""
    available_models = get_available_models()
    
    if not available_models:
        current_app.logger.warning("Falling back to static model list due to API fetch failure.")
        available_models = ["models/gemini-1.5-pro-latest", "models/gemini-1.5-flash-latest"]

    if prefer_flash:
        preferred_order = ["models/gemini-1.5-flash-latest", "models/gemini-1.5-pro-latest"]
    else:
        preferred_order = ["models/gemini-1.5-pro-latest", "models/gemini-1.5-flash-latest"]
    
    for model_path in preferred_order:
        if model_path in available_models:
            model_name = model_path.split('/')[-1]
            current_app.logger.info(f"Selected generative model: {model_name}")
            return model_name
            
    fallback_model_path = available_models[0] if available_models else "models/gemini-1.5-pro-latest"
    fallback_model_name = fallback_model_path.split('/')[-1]
    current_app.logger.warning(f"No preferred models found, using fallback: {fallback_model_name}")
    return fallback_model_name

class JobService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.profile_service = ProfileService(self.logger)

    def _call_gemini_api(self, prompt, model_name=None):
        api_key = config.GEMINI_API_KEY
        if not api_key:
            self.logger.error("Gemini API key is not configured.")
            return None

        if not model_name:
            model_name = select_generative_model()

        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        
        headers = { "Content-Type": "application/json", "x-goog-api-key": api_key }
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": { "responseMimeType": "application/json" }
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            text_content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            if not text_content: return None
            return text_content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            if e.response is not None: self.logger.error(f"Gemini API Response: {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Error in Gemini API call or response parsing: {e}", exc_info=True)
            return None

    def _extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        for script_or_style in soup(['script', 'style']): script_or_style.decompose()
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
            if meta_og_site_name and meta_og_site_name.get('content'): company_name = meta_og_site_name.get('content')
            description = self._extract_text_from_html(html_content)
            return {"title": title[:255], "company_name": company_name[:255], "description": description[:MAX_JOB_TEXT_LENGTH]}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during lightweight scrape of {url}: {e}")
            return None

    def _validate_enum(self, value, enum_class):
        if value is None: return None
        try:
            if isinstance(value, enum_class): return value
            return enum_class[value.upper().replace('-', '_')]
        except (KeyError, AttributeError): return None

    def _parse_and_validate_int(self, value):
        if value is None or value == '': return None
        try: return int(value)
        except (ValueError, TypeError): return None
            
    def _parse_ai_response(self, ai_response_text):
        try:
            json_string = re.sub(r"```json\n?|```", "", ai_response_text).strip()
            json_string = re.sub(r"//.*", "", json_string)
            json_string = re.sub(r",\s*(\n\s*[\}\]])", r"\1", json_string)
            parsed_data = json.loads(json_string)
            parsed_data['job_title'] = parsed_data.get('job_title', 'Unknown Title').strip()[:255]
            parsed_data['company_name'] = parsed_data.get('company_name', 'Unknown Company').strip()[:255]
            return parsed_data
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}. Raw: {ai_response_text[:500]}")
            return None

    def analyze_job_posting(self, job_text, user_profile_data, company_profile_data=None):
        if not job_text: return None
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
        
        Strictly conform to the JSON structure. Your response MUST be valid JSON.
        """
        model_to_use = select_generative_model(prefer_flash=False)
        ai_response = self._call_gemini_api(prompt, model_name=model_to_use)
        
        if ai_response: return self._parse_ai_response(ai_response)
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