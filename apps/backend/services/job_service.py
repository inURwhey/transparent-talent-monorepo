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

    def _call_gemini_api(self, prompt, model_name="gemini-pro"):
        api_key = config.GEMINI_API_KEY
        if not api_key:
            self.logger.error("Gemini API key is not configured.")
            return None

        headers = {
            "Content-Type": "application/json"
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

        try:
            response = requests.post(url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}]})
            response.raise_for_status()
            data = response.json()
            # Extract text from the response structure
            text_content = data.get('candidates', [])[0].get('content', {}).get('parts', [])[0].get('text', '')
            return text_content
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error calling Gemini API: {e}")
            self.logger.error(f"Gemini API Response: {getattr(e, 'response', 'No response attribute')}")
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
                    pass # Already logged, no need to re-log

            description = self._extract_text_from_html(html_content)

            return {
                "title": title[:255], # Truncate to fit schema
                "company_name": company_name[:255], # Truncate to fit schema
                "description": description[:MAX_JOB_TEXT_LENGTH], # Truncate to fit AI limit
                "extracted_location": extracted_location
            }
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error during lightweight scrape of {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during lightweight scrape of {url}: {e}")
            return None


    def _validate_enum(self, value, enum_class):
        """Validates if a value is part of an ENUM and returns the ENUM member."""
        if value is None:
            return None
        try:
            # If value is already an Enum member, return it
            if isinstance(value, enum_class):
                return value
            # Otherwise, try to convert string to Enum member
            return enum_class[value.upper().replace('-', '_')]
        except KeyError:
            self.logger.warning(f"Invalid ENUM value '{value}' for {enum_class.__name__}. Setting to None.")
            return None

    def _parse_and_validate_int(self, value):
        """Parses a value to an integer, returning None if invalid."""
        if value is None or value == '':
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid integer value '{value}'. Setting to None.")
            return None
            
    def _parse_ai_response(self, ai_response):
        """Parses and validates the JSON output from the AI."""
        try:
            # Attempt to find the JSON string within the response
            match = re.search(r"```json\n(.+?)\n```", ai_response, re.DOTALL)
            if match:
                json_string = match.group(1)
            else:
                # If no code block, assume the whole response is JSON
                json_string = ai_response

            parsed_data = json.loads(json_string)

            # Validate and clean up parsed data
            parsed_data['job_title'] = parsed_data.get('job_title', 'Unknown Title').strip()
            parsed_data['company_name'] = parsed_data.get('company_name', 'Unknown Company').strip()
            
            parsed_data['salary_min'] = self._parse_and_validate_int(parsed_data.get('salary_min'))
            parsed_data['salary_max'] = self._parse_and_validate_int(parsed_data.get('salary_max'))
            parsed_data['required_experience_years'] = self._parse_and_validate_int(parsed_data.get('required_experience_years'))
            
            # Map 'job_modality' and 'deduced_job_level' to ENUMs from SQLAlchemy models
            parsed_data['job_modality'] = self._validate_enum(parsed_data.get('job_modality'), Job.job_modality.type.enum_class)
            parsed_data['deduced_job_level'] = self._validate_enum(parsed_data.get('deduced_job_level'), Job.deduced_job_level.type.enum_class)

            # Ensure 'matrix_rating' is within reasonable bounds or defaults
            matrix_rating = parsed_data.get('matrix_rating', 'N/A')
            if not isinstance(matrix_rating, str) or len(matrix_rating) > 50: # max length for VARCHAR(50)
                matrix_rating = 'N/A'
            parsed_data['matrix_rating'] = matrix_rating[:50]

            return parsed_data
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON from AI response: {e}. Raw response: {ai_response}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing AI response: {e}. Raw response: {ai_response}")
            return None

    def analyze_job_posting(self, job_text, user_profile_data, company_profile_data=None):
        """Sends job text, user profile, and company profile to AI for analysis."""
        if not job_text:
            return {"error": "Job text is empty for AI analysis."}
        if len(job_text) > MAX_JOB_TEXT_LENGTH:
            self.logger.warning(f"Job text too long ({len(job_text)} chars) for AI analysis. Truncating.")
            job_text = job_text[:MAX_JOB_TEXT_LENGTH]

        profile_str = json.dumps(user_profile_data, indent=2) if user_profile_data else "No user profile provided."
        company_str = json.dumps(company_profile_data, indent=2) if company_profile_data else "No company profile provided."


        # The prompt is simplified for brevity in this example.
        # In a real scenario, this would be highly detailed and likely come from a database (ai_protocols table).
        prompt = f"""
        Analyze the following job posting and user profile to determine the candidate's fit.
        Provide a detailed JSON output matching the schema provided.

        User Profile:
        ```json
        {profile_str}
        ```

        Job Posting:
        ```text
        {job_text}
        ```

        Company Context:
        ```json
        {company_str}
        ```

        Output a JSON object with the following structure.
        Ensure all string values are properly escaped for JSON.
        - job_title (string, max 255 chars): Deduced exact job title.
        - company_name (string, max 255 chars): Deduced exact company name.
        - salary_min (integer, nullable): Minimum annual salary in USD.
        - salary_max (integer, nullable): Maximum annual salary in USD.
        - required_experience_years (integer, nullable): Years of experience required.
        - job_modality (enum: "ON_SITE", "REMOTE", "HYBRID", nullable): How the job is performed.
        - deduced_job_level (enum: "ENTRY", "ASSOCIATE", "MID", "SENIOR", "LEAD", "PRINCIPAL", "DIRECTOR", "VP", "EXECUTIVE", nullable): Deduced level of the job.
        - position_relevance_score (integer, 0-100): Score based on skills, experience match.
        - environment_fit_score (integer, 0-100): Score based on cultural alignment, work style.
        - matrix_rating (string, e.g., "A+", "B-"): An overall letter grade for the fit.
        - summary (string): A concise summary of the overall fit.
        - qualification_gaps (JSON array of strings): Key areas where the user falls short.
        - recommended_testimonials (JSON array of strings): Example testimonials/skills from the user's past that directly address job requirements.
        - hiring_manager_view (string): A brief paragraph describing how a hiring manager would perceive this candidate for THIS role.

        Strictly conform to the JSON structure. If a field cannot be determined, use null or appropriate default.
        """
        self.logger.info(f"Sending job posting to Gemini for analysis.")
        ai_response = self._call_gemini_api(prompt)

        if ai_response:
            parsed_data = self._parse_ai_response(ai_response)
            if parsed_data:
                self.logger.info("AI analysis successful.")
                return parsed_data
        
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
        Performs initial deduplication based on URL, then company_id and job_title.
        """
        # 1. Check for existing JobOpportunity by URL
        existing_opportunity = JobOpportunity.query.filter_by(url=url).first()
        if existing_opportunity:
            self.logger.info(f"Existing job opportunity found for URL: {url}")
            # Ensure it has a valid canonical job relationship
            if existing_opportunity.job:
                # Update opportunity's last_checked_at and is_active status
                existing_opportunity.updated_at = datetime.now(pytz.utc)
                existing_opportunity.last_checked_at = datetime.now(pytz.utc)
                existing_opportunity.is_active = True
                if commit: db.session.commit()
                db.session.refresh(existing_opportunity)
                return existing_opportunity.job, existing_opportunity
            else:
                self.logger.warning(f"Existing opportunity {existing_opportunity.id} has no canonical job. Re-scraping and trying to link.")
                # This case indicates corrupted data, try to fix it by re-processing
                # For now, we proceed to scrape and re-link/create a canonical job
                pass # Continue to scrape logic below

        # 2. Lightweight scrape for initial data (for new URLs or corrupted existing ones)
        self.logger.info(f"Performing lightweight scrape for URL: {url}")
        scraped_data = self._lightweight_scrape(url)
        if not scraped_data:
            self.logger.error(f"Failed lightweight scrape for URL: {url}")
            return None, None
        
        job_title = scraped_data.get('title')
        company_name = scraped_data.get('company_name')
        job_description = scraped_data.get('description')
        extracted_location = scraped_data.get('extracted_location')

        if not company_name or not job_title or not job_description:
            self.logger.error("Missing company name, job title, or description after scrape.")
            return None, None

        # Try to find existing company by name (case-insensitive)
        company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()
        if not company:
            self.logger.info(f"Creating new company record: {company_name}")
            company = Company(name=company_name)
            db.session.add(company)
            # Need to commit and refresh company here to get its ID before creating Job
            try:
                if commit: db.session.commit()
                db.session.refresh(company)
            except IntegrityError: # Handle race condition if another process creates it
                db.session.rollback()
                company = Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()
                if not company: raise # Re-raise if still no company

        # 3. Try to find an existing canonical Job (basic deduplication)
        # Match on company_id and job_title (case-insensitive) and job_description_hash (if available)
        # For full semantic deduplication, this would involve AI/embedding similarity
        canonical_job = Job.query.filter(
            Job.company_id == company.id,
            db.func.lower(Job.job_title) == job_title.lower()
        ).first() # Add job_description_hash matching for stricter deduplication if needed

        if not canonical_job:
            self.logger.info(f"Creating new canonical job: '{job_title}' at '{company_name}'")
            ai_analysis_data = self.analyze_job_posting(job_description, {}, company.to_dict()) # Pass company data
            
            if not ai_analysis_data:
                self.logger.warning(f"AI analysis failed for new canonical job '{job_title}'. Proceeding with basic data.")
                ai_analysis_data = {} # Use empty dict to avoid KeyError

            # Compute and store job_description_hash
            job_desc_hash = hashlib.sha256(job_description.encode('utf-8')).hexdigest()

            canonical_job = Job(
                company_id=company.id,
                company_name=company_name,
                job_title=job_title,
                status='Active', # Initial status for the job posting
                found_at=datetime.now(pytz.utc),
                last_checked_at=datetime.now(pytz.utc),
                job_description_hash=job_desc_hash,
                salary_min=ai_analysis_data.get('salary_min'),
                salary_max=ai_analysis_data.get('salary_max'),
                required_experience_years=ai_analysis_data.get('required_experience_years'),
                job_modality=ai_analysis_data.get('job_modality'),
                deduced_job_level=ai_analysis_data.get('deduced_job_level'),
                notes=job_description # Store full description in notes for now
            )
            db.session.add(canonical_job)
            try:
                if commit: db.session.commit()
                db.session.refresh(canonical_job)
            except IntegrityError: # Handle race condition if another process creates it
                db.session.rollback()
                canonical_job = Job.query.filter(
                    Job.company_id == company.id,
                    db.func.lower(Job.job_title) == job_title.lower()
                ).first()
                if not canonical_job: raise # Re-raise if still no job

            # Create initial JobAnalysis for the submitting user if the profile is complete
            profile_service = ProfileService(self.logger)
            if user_id and profile_service.has_completed_required_profile_fields(user_id):
                user_profile_data = profile_service.get_profile_for_analysis(user_id)
                if user_profile_data and ai_analysis_data: # Ensure analysis data is present
                    self.create_or_update_job_analysis(user_id, canonical_job.id, ai_analysis_data)
                else:
                    self.logger.warning(f"Skipping initial analysis for new canonical job {canonical_job.id} as profile or AI data incomplete.")

        # 4. Create the new JobOpportunity linking to the canonical job
        # If we arrived here, existing_opportunity was either None or corrupted.
        if existing_opportunity:
             # Update the existing (corrupted) opportunity to link it to the found/created canonical job
            self.logger.info(f"Re-linking existing (corrupted) JobOpportunity {existing_opportunity.id} to canonical job {canonical_job.id}.")
            existing_opportunity.job_id = canonical_job.id
            existing_opportunity.url = url # Ensure URL is correct
            existing_opportunity.source_platform = scraped_data.get('source')
            existing_opportunity.posted_at = datetime.now(pytz.utc) # Or scraped_data.get('posted_at')
            existing_opportunity.last_checked_at = datetime.now(pytz.utc)
            existing_opportunity.is_active = True
            new_opportunity = existing_opportunity # Use this object
        else:
            self.logger.info(f"Creating new JobOpportunity for canonical job {canonical_job.id} at URL: {url}")
            new_opportunity = JobOpportunity(
                job_id=canonical_job.id,
                url=url,
                source_platform=scraped_data.get('source'), # Use source from scraped data, assuming it's added to scrape
                posted_at=datetime.now(pytz.utc), # Use scraped posted_at if available, else now
                last_checked_at=datetime.now(pytz.utc),
                is_active=True,
                extracted_location=extracted_location
            )
            db.session.add(new_opportunity)
        
        try:
            if commit: db.session.commit()
            db.session.refresh(new_opportunity)
        except IntegrityError: # Handle race condition if another process creates it
            db.session.rollback()
            new_opportunity = JobOpportunity.query.filter_by(url=url).first()
            if not new_opportunity: raise # Re-raise if still no opportunity

        return canonical_job, new_opportunity

    def create_or_update_job_analysis(self, user_id, job_id, ai_analysis_data):
        """
        Creates or updates a job analysis record for a given user and canonical job.
        """
        analysis = JobAnalysis.query.filter_by(user_id=user_id, job_id=job_id).first()

        if analysis:
            self.logger.info(f"Updating existing job analysis for user {user_id}, job {job_id}.")
            analysis.position_relevance_score = ai_analysis_data.get('position_relevance_score')
            analysis.environment_fit_score = ai_analysis_data.get('environment_fit_score')
            analysis.hiring_manager_view = ai_analysis_data.get('hiring_manager_view')
            analysis.matrix_rating = ai_analysis_data.get('matrix_rating')
            analysis.summary = ai_analysis_data.get('summary')
            analysis.qualification_gaps = ai_analysis_data.get('qualification_gaps')
            analysis.recommended_testimonials = ai_analysis_data.get('recommended_testimonials')
            analysis.updated_at = datetime.now(pytz.utc)
            analysis.analysis_protocol_version = config.ANALYSIS_PROTOCOL_VERSION # Always update to latest
        else:
            self.logger.info(f"Creating new job analysis for user {user_id}, job {job_id}.")
            analysis = JobAnalysis(
                job_id=job_id,
                user_id=user_id,
                position_relevance_score=ai_analysis_data.get('position_relevance_score'),
                environment_fit_score=ai_analysis_data.get('environment_fit_score'),
                hiring_manager_view=ai_analysis_data.get('hiring_manager_view'),
                matrix_rating=ai_analysis_data.get('matrix_rating'),
                summary=ai_analysis_data.get('summary'),
                qualification_gaps=ai_analysis_data.get('qualification_gaps'),
                recommended_testimonials=ai_analysis_data.get('recommended_testimonials'),
                analysis_protocol_version=config.ANALYSIS_PROTOCOL_VERSION
            )
            db.session.add(analysis)
        
        try:
            db.session.commit()
            db.session.refresh(analysis)
            return analysis
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating/updating job analysis: {e}")
            raise e

    def trigger_reanalysis_for_user(self, user_id: int):
        """
        Triggers AI re-analysis for all jobs tracked by a specific user,
        typically after profile completion.
        """
        user_profile_data = self.profile_service.get_profile_for_analysis(user_id)
        if not user_profile_data:
            self.logger.warning(f"Cannot re-analyze for user {user_id}: profile not complete.")
            return

        # Get all canonical jobs associated with opportunities tracked by this user
        # Ensure we only get unique canonical jobs
        canonical_jobs = db.session.query(Job).join(
            JobOpportunity, JobOpportunity.job_id == Job.id
        ).join(
            TrackedJob, TrackedJob.job_opportunity_id == JobOpportunity.id
        ).filter(TrackedJob.user_id == user_id).options(
            joinedload(Job.company), # Eager load company for AI context
            joinedload(Job.opportunities) # Eager load opportunities to get a URL if needed
        ).distinct().all()

        for canonical_job in canonical_jobs:
            # Get the company profile for context
            company_profile_data = canonical_job.company.to_dict() if canonical_job.company else None
            
            # Re-fetch job description from notes or re-scrape an opportunity URL
            job_description_to_analyze = canonical_job.notes # Assume notes has full description for now
            if not job_description_to_analyze and canonical_job.opportunities:
                # If notes doesn't have it, try scraping the first active opportunity URL
                active_opportunity = next((o for o in canonical_job.opportunities if o.is_active), None)
                if active_opportunity:
                    self.logger.info(f"Re-scraping first active opportunity URL {active_opportunity.url} for canonical job {canonical_job.id} for re-analysis.")
                    scraped_data = self._lightweight_scrape(active_opportunity.url)
                    job_description_to_analyze = scraped_data['description'] if scraped_data else None
                else:
                    self.logger.warning(f"No active opportunity URLs for canonical job {canonical_job.id} to re-scrape.")


            if job_description_to_analyze:
                self.logger.info(f"Re-analyzing canonical job {canonical_job.id} for user {user_id}...")
                ai_analysis_data = self.analyze_job_posting(job_description_to_analyze, user_profile_data, company_profile_data)
                if ai_analysis_data:
                    self.create_or_update_job_analysis(user_id, canonical_job.id, ai_analysis_data)
                    self.logger.info(f"Successfully re-analyzed job {canonical_job.id} for user {user_id}.")
                else:
                    self.logger.warning(f"Failed AI re-analysis for canonical job {canonical_job.id}, user {user_id}.")
            else:
                self.logger.warning(f"No job description available for re-analysis of canonical job {canonical_job.id}.")

        self.logger.info(f"Re-analysis triggered for all jobs for user {user_id}.")