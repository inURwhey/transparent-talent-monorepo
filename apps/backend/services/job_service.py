# Path: apps/backend/services/job_service.py
import requests
from bs4 import BeautifulSoup
import json
import re
from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload # NEW IMPORT for eager loading relationships
from datetime import datetime
import pytz
import hashlib # For job_description_hash

from ..app import db
from ..models import Job, Company, JobAnalysis, User, JobOpportunity # Import all new models
from ..config import config
from .profile_service import ProfileService

# Constants for AI validation
MAX_RESUME_TEXT_LENGTH = 25000
MAX_JOB_TEXT_LENGTH = 50000

class JobService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.profile_service = ProfileService(self.logger)

    def _call_gemini_api(self, prompt, model_name="gemini-1.5-flash"):
        api_key = config.GEMINI_API_KEY
        if not api_key:
            self.logger.error("Gemini API key is not configured.")
            return None

        # CORRECTED: Updated to the stable v1 endpoint.
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }

        # CORRECTED: Payload includes generationConfig to force JSON output.
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json",
            }
        }

        try:
            self.logger.info(f"Calling Gemini API with model {model_name}")
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            
            # The v1 API returns the JSON directly in the 'text' field when response_mime_type is set.
            text_content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            
            if not text_content:
                self.logger.error("Gemini API returned an empty text response.")
                self.logger.error(f"Full Gemini Response: {data}")
                return None
            
            return text_content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Gemini API: {e}")
            if e.response is not None:
                self.logger.error(f"Gemini API Response Status: {e.response.status_code}")
                self.logger.error(f"Gemini API Response Body: {e.response.text}")
            return None
        except (KeyError, IndexError) as e:
            self.logger.error(f"Error parsing Gemini API response structure: {e}")
            self.logger.error(f"Full Gemini Response: {data}")
            return None

    def _extract_text_from_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        # Get text
        text = soup.get_text()
        # Break into lines and remove whitespace
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a single line
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text

    def _lightweight_scrape(self, url):
        """
        Performs a lightweight scrape to get basic job title, company name, and full description from a URL.
        Returns a dictionary {title, company_name, description, extracted_location}.
        """
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')

            # Attempt to extract title
            title = soup.find('title').get_text() if soup.find('title') else 'Unknown Title'
            
            # Attempt to extract company name from common meta tags or structured data
            company_name = 'Unknown Company'
            meta_og_site_name = soup.find('meta', property='og:site_name')
            if meta_og_site_name and meta_og_site_name.get('content'):
                company_name = meta_og_site_name.get('content')
            else:
                # Try JSON-LD for organization name if available
                script_ld_json = soup.find('script', type='application/ld+json')
                if script_ld_json:
                    try:
                        json_ld = json.loads(script_ld_json.string)
                        if isinstance(json_ld, dict) and json_ld.get('@type') == 'JobPosting' and 'hiringOrganization' in json_ld:
                            company_name = json_ld['hiringOrganization'].get('name', company_name)
                        elif isinstance(json_ld, list): # Some sites have multiple LD+JSON blocks
                             for block in json_ld:
                                if block.get('@type') == 'JobPosting' and 'hiringOrganization' in block:
                                    company_name = block['hiringOrganization'].get('name', company_name)
                                    break
                    except json.JSONDecodeError:
                        self.logger.warning(f"Could not decode JSON-LD for company name from {url}")

            # Attempt to extract location from JSON-LD or meta tags
            extracted_location = None
            if script_ld_json:
                try:
                    json_ld = json.loads(script_ld_json.string)
                    if isinstance(json_ld, dict) and json_ld.get('@type') == 'JobPosting' and 'jobLocation' in json_ld:
                        extracted_location = json_ld['jobLocation'].get('address', {}).get('addressLocality')
                        if not extracted_location:
                            extracted_location = json_ld['jobLocation'].get('address', {}).get('addressRegion') # Try region if city not found
                    elif isinstance(json_ld, list):
                        for block in json_ld:
                            if block.get('@type') == 'JobPosting' and 'jobLocation' in block:
                                extracted_location = block['jobLocation'].get('address', {}).get('addressLocality')
                                if not extracted_location:
                                    extracted_location = block['jobLocation'].get('address', {}).get('addressRegion')
                                if extracted_location: break
                except json.JSONDecodeError:
                    pass

            description = self._extract_text_from_html(html_content)

            return {
                "title": title[:255],
                "company_name": company_name[:255],
                "description": description[:MAX_JOB_TEXT_LENGTH],
                "extracted_location": extracted_location
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during lightweight scrape of {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during lightweight scrape of {url}: {e}")
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
            # With response_mime_type='application/json', the response should be a clean JSON string.
            parsed_data = json.loads(ai_response_text)
            
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
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON from AI response: {e}. Raw text: {ai_response_text}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing AI response: {e}. Raw text: {ai_response_text}")
            return None

    def analyze_job_posting(self, job_text, user_profile_data, company_profile_data=None):
        """Sends job text, user profile, and company profile to AI for analysis."""
        if not job_text:
            return {"error": "Job text is empty for AI analysis."}
        if len(job_text) > MAX_JOB_TEXT_LENGTH:
            self.logger.warning(f"Job text too long ({len(job_text)} chars) for AI analysis. Truncating.")
            job_text = job_text[:MAX_JOB_TEXT_LENGTH]

        profile_str = json.dumps(user_profile_data, indent=2) if user_profile_data else "{}"
        company_str = json.dumps(company_profile_data, indent=2) if company_profile_data else "{}"


        # CORRECTED: Simplified prompt and removed markdown wrapper instruction
        prompt = f"""
        Analyze the following job posting, user profile, and company context to determine the candidate's fit.

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
        
        Your response MUST be valid JSON.
        """
        self.logger.info("Sending job posting to Gemini for analysis.")
        ai_response = self._call_gemini_api(prompt, model_name="gemini-1.5-pro-latest")

        if ai_response:
            return self._parse_ai_response(ai_response)
        
        self.logger.error("AI analysis failed or returned unparseable data.")
        return None

    def get_job_details(self, job_id: int):
        """
        Retrieves a canonical Job along with its associated opportunities and company details.
        """
        job = db.session.query(Job).options(
            joinedload(Job.company),
            joinedload(Job.opportunities)
        ).filter(Job.id == job_id).first()

        if not job:
            return None
        
        job_dict = job.to_dict()
        job_dict['company'] = job.company.to_dict() if job.company else None
        job_dict['opportunities'] = [o.to_dict() for o in job.opportunities]
        
        return job_dict

    def create_or_get_canonical_job(self, url: str, user_id: int, commit: bool = True):
        """
        Creates or retrieves a canonical Job and a corresponding JobOpportunity.
        """
        existing_opportunity = JobOpportunity.query.filter_by(url=url).first()
        if existing_opportunity and existing_opportunity.job:
            self.logger.info(f"Existing job opportunity found for URL: {url}")
            existing_opportunity.updated_at = datetime.now(pytz.utc)
            existing_opportunity.last_checked_at = datetime.now(pytz.utc)
            existing_opportunity.is_active = True
            if commit: db.session.commit()
            return existing_opportunity.job, existing_opportunity

        self.logger.info(f"Performing lightweight scrape for URL: {url}")
        scraped_data = self._lightweight_scrape(url)
        if not scraped_data:
            self.logger.error(f"Failed lightweight scrape for URL: {url}")
            return None, None
        
        job_title = scraped_data.get('title')
        company_name = scraped_data.get('company_name')
        job_description = scraped_data.get('description')

        if not company_name or not job_title or not job_description:
            self.logger.error("Missing company name, job title, or description after scrape.")
            return None, None

        company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()
        if not company:
            self.logger.info(f"Creating new company record: {company_name}")
            company = Company(name=company_name)
            db.session.add(company)
            if commit:
                try:
                    db.session.commit()
                    db.session.refresh(company)
                except IntegrityError:
                    db.session.rollback()
                    company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()

        canonical_job = Job.query.filter(
            Job.company_id == company.id,
            db.func.lower(Job.job_title) == job_title.lower()
        ).first()

        if not canonical_job:
            self.logger.info(f"Creating new canonical job: '{job_title}' at '{company.name}'")
            company_profile_for_ai = company.to_dict() if company else {}
            ai_analysis_data = self.analyze_job_posting(job_description, {}, company_profile_for_ai)
            
            if not ai_analysis_data: ai_analysis_data = {}

            job_desc_hash = hashlib.sha256(job_description.encode('utf-8')).hexdigest()

            canonical_job = Job(
                company_id=company.id,
                company_name=company.name,
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
            if commit:
                db.session.commit()
                db.session.refresh(canonical_job)

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
        
        if commit:
            db.session.commit()
            db.session.refresh(new_opportunity)

        return canonical_job, new_opportunity

    def create_or_update_job_analysis(self, user_id, job_id, ai_analysis_data):
        """
        Creates or updates a job analysis record for a given user and canonical job.
        """
        if not ai_analysis_data:
            self.logger.warning(f"No AI analysis data provided for user {user_id}, job {job_id}. Skipping update.")
            return None

        analysis = JobAnalysis.query.filter_by(user_id=user_id, job_id=job_id).first()

        if not analysis:
            analysis = JobAnalysis(job_id=job_id, user_id=user_id)
            db.session.add(analysis)
            self.logger.info(f"Creating new job analysis for user {user_id}, job {job_id}.")
        else:
            self.logger.info(f"Updating existing job analysis for user {user_id}, job {job_id}.")

        analysis.position_relevance_score = ai_analysis_data.get('position_relevance_score')
        analysis.environment_fit_score = ai_analysis_data.get('environment_fit_score')
        analysis.hiring_manager_view = ai_analysis_data.get('hiring_manager_view')
        analysis.matrix_rating = ai_analysis_data.get('matrix_rating')
        analysis.summary = ai_analysis_data.get('summary')
        analysis.qualification_gaps = ai_analysis_data.get('qualification_gaps')
        analysis.recommended_testimonials = ai_analysis_data.get('recommended_testimonials')
        analysis.updated_at = datetime.now(pytz.utc)
        analysis.analysis_protocol_version = config.ANALYSIS_PROTOCOL_VERSION
        
        try:
            db.session.commit()
            return analysis
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating/updating job analysis: {e}")
            raise e

    def trigger_reanalysis_for_user(self, user_id: int):
        """
        Triggers AI re-analysis for all jobs tracked by a specific user.
        """
        user_profile_data = self.profile_service.get_profile_for_analysis(user_id)
        if not user_profile_data:
            self.logger.warning(f"Cannot re-analyze for user {user_id}: profile not complete.")
            return

        jobs_to_reanalyze = db.session.query(Job).join(
            JobOpportunity
        ).join(
            TrackedJob, TrackedJob.job_opportunity_id == JobOpportunity.id
        ).filter(TrackedJob.user_id == user_id).options(
            joinedload(Job.company)
        ).distinct().all()

        for job in jobs_to_reanalyze:
            company_profile_data = job.company.to_dict() if job.company else None
            job_description = job.notes 
            
            if job_description:
                self.logger.info(f"Re-analyzing canonical job {job.id} for user {user_id}...")
                ai_analysis_data = self.analyze_job_posting(job_description, user_profile_data, company_profile_data)
                if ai_analysis_data:
                    self.create_or_update_job_analysis(user_id, job.id, ai_analysis_data)
                    self.logger.info(f"Successfully re-analyzed job {job.id} for user {user_id}.")
                else:
                    self.logger.warning(f"Failed AI re-analysis for canonical job {job.id}, user {user_id}.")
            else:
                self.logger.warning(f"No job description available for re-analysis of canonical job {job.id}.")

        self.logger.info(f"Re-analysis triggered for all jobs for user {user_id}.")