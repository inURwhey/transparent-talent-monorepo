# Path: apps/backend/services/job_service.py
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import re
from ..config import config
from ..database import get_db

# This version helps track which version of our prompt/logic generated the data.
COMPANY_RESEARCH_PROTOCOL_VERSION = "1.0"

class JobService:
    def __init__(self, logger):
        self.logger = logger
        if config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.logger.info("Gemini AI model configured successfully.")
            except Exception as e:
                self.logger.error(f"Error configuring Gemini AI: {e}")
                self.model = None
        else:
            self.model = None
            self.logger.warning("JobService initialized without a GEMINI_API_KEY. AI analysis is disabled.")

        self.VALID_JOB_MODALITIES = {'On-site', 'Remote', 'Hybrid'}
        self.VALID_JOB_LEVELS = {'Entry', 'Mid', 'Senior', 'Staff', 'Principal', 'Manager', 'Director', 'VP', 'C-Suite'}

    def research_and_get_company_profile(self, company_id: int):
        """
        Checks if a company profile exists. If not, triggers AI research to create one.
        Returns the company profile data dictionary. This is a best-effort service.
        """
        db = get_db()
        with db.cursor() as cursor:
            # 1. Check if a profile already exists
            cursor.execute("SELECT * FROM company_profiles WHERE company_id = %s", (company_id,))
            profile = cursor.fetchone()
            if profile:
                self.logger.info(f"Found existing company profile for company_id: {company_id}")
                return dict(profile)

            # 2. If no profile, get company name to start research
            self.logger.info(f"No profile found for company_id: {company_id}. Initiating AI research.")
            cursor.execute("SELECT name FROM companies WHERE id = %s", (company_id,))
            company = cursor.fetchone()
            if not company:
                self.logger.error(f"Cannot research company: No company found for company_id: {company_id}")
                return None
            
            company_name = company.get('name')
            prompt = self._build_company_research_prompt(company_name)

            # 3. Call AI for research
            try:
                if not self.model:
                    self.logger.error(f"Cannot research company {company_name}: AI model not configured.")
                    return None
                response = self.model.generate_content(prompt)
                json_data = self._extract_json_from_response(response.text)
                if not json_data:
                    self.logger.error(f"Failed to extract JSON from company research for {company_name}")
                    return None
            except Exception as e:
                self.logger.error(f"Company research AI call failed for {company_name}: {e}")
                return None
            
            # 4. Save the new profile to the database
            try:
                cursor.execute(
                    """
                    INSERT INTO company_profiles (company_id, industry, employee_count_range, publicly_stated_mission, primary_business_model, researched_at, ai_model_version)
                    VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    ON CONFLICT (company_id) DO NOTHING
                    RETURNING *;
                    """,
                    (company_id, json_data.get('industry'), json_data.get('employee_count_range'), json_data.get('publicly_stated_mission'), json_data.get('primary_business_model'), COMPANY_RESEARCH_PROTOCOL_VERSION)
                )
                new_profile = cursor.fetchone()
                db.commit()
                self.logger.info(f"Successfully created and saved new profile for company_id: {company_id}")
                return dict(new_profile) if new_profile else None
            except Exception as e:
                db.rollback()
                self.logger.error(f"Database error saving new company profile for {company_name}: {e}")
                return None

    def get_basic_job_details(self, job_url: str):
        """
        Lightweight scraper to get only the essential details (title, company)
        for users with incomplete profiles, to avoid creating generic placeholders.
        """
        self.logger.info(f"Performing lightweight scrape for URL: {job_url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.get(job_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            page_title = soup.find('title').get_text() if soup.find('title') else 'Unknown Title'
            
            if '|' in page_title: parts = page_title.split('|')
            elif ' at ' in page_title: parts = page_title.split(' at ')
            elif '-' in page_title: parts = page_title.split('-')
            else: parts = [page_title]

            job_title_guess = parts[0].strip()
            company_name_guess = parts[-1].strip() if len(parts) > 1 else 'Unknown Company'

            generic_sites = ['LinkedIn', 'Indeed', 'Glassdoor', 'Built In']
            if any(site in company_name_guess for site in generic_sites) and len(parts) > 1:
                if ' at ' in page_title: company_name_guess = parts[-1].split(' at ')[-1].strip()
                else: company_name_guess = parts[-2].strip()

            final_job_title = job_title_guess[:252] + '...' if len(job_title_guess) > 255 else job_title_guess
            return {'job_title': final_job_title, 'company_name': company_name_guess}
        except Exception as e:
            self.logger.error(f"Lightweight scrape failed for {job_url}: {e}")
            return {'job_title': 'Scrape Failed - See URL', 'company_name': 'Unknown'}

    def get_job_details_and_analysis(self, job_url: str, user_profile_text: str, company_profile_text: str = None):
        self.logger.info(f"Fetching job text for URL: {job_url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.get(job_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            job_text = soup.get_text(separator=' ', strip=True)
            
            if not job_text or len(job_text) < 100: raise ValueError("Extracted job text is too short or empty.")
            if len(job_text) > config.MAX_JOB_TEXT_LENGTH: raise ValueError(f"Job text too long ({len(job_text)}). Max is {config.MAX_JOB_TEXT_LENGTH}.")

            if not self.is_job_posting_content(job_text): raise ValueError("Content does not appear to be a job posting.")

            self.logger.info(f"Successfully fetched job text. Length: {len(job_text)} characters.")
            analysis = self._run_ai_analysis(job_text, user_profile_text, company_profile_text)
            
            return {"job_text": job_text, "analysis": analysis}
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch job URL '{job_url}': {e}")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred in get_job_details_and_analysis for url '{job_url}': {e}")
            raise

    def analyze_existing_job(self, job_id: int, user_profile_text: str):
        self.logger.info(f"Re-analyzing existing job_id: {job_id}")
        db = get_db()
        with db.cursor() as cursor:
            cursor.execute("SELECT job_url, company_id FROM jobs WHERE id = %s", (job_id,))
            job_row = cursor.fetchone()
            if not job_row: raise ValueError(f"Job with id {job_id} not found.")
            
            company_profile = self.research_and_get_company_profile(job_row['company_id'])
            company_profile_text = json.dumps(company_profile, indent=2, default=str) if company_profile else "No company profile available."
            
            return self.get_job_details_and_analysis(job_row['job_url'], user_profile_text, company_profile_text)

    def _run_ai_analysis(self, job_text: str, user_profile_text: str, company_profile_text: str = None) -> dict:
        if not self.model: raise ConnectionError("AI Service is not configured.")

        company_context_block = f"""
            COMPANY PROFILE (for environment fit analysis):
            ---
            {company_profile_text or "No company profile available."}
            ---
        """

        prompt = f"""
            You are a meticulous career-focused analyst for a platform called "Transparent Talent".
            Your task is to analyze a job description in the context of a user's professional profile and a company's profile.
            Produce a JSON object with the exact keys specified below. Do not include any introductory text or markdown formatting.

            For the 'matrix_rating', calculate the average of 'position_relevance_score' and 'environment_fit_score'.
            Then, assign a letter grade based on this average: 90-100: A+, 80-89: A, 70-79: B+, 60-69: B, 50-59: C+, 40-49: C, 30-39: D, 0-29: F.

            Extract the following structured data points from the job description:
            - `salary_min`, `salary_max`: Annual salary in USD. If not stated, set to null.
            - `required_experience_years`: Minimum years of experience. If not stated, set to null.
            - `job_modality`: Exactly one from "On-site", "Remote", or "Hybrid". If unsure, set to null.
            - `deduced_job_level`: Exactly one from "Entry", "Mid", "Senior", "Staff", "Principal", "Manager", "Director", "VP", "C-Suite". If unsure, set to null.

            USER PROFILE:
            ---
            {user_profile_text}
            ---

            {company_context_block}

            JOB DESCRIPTION:
            ---
            {job_text}
            ---

            JSON_OUTPUT_SCHEMA:
            {{
                "company_name": "string", "job_title": "string",
                "salary_min": "integer or null", "salary_max": "integer or null",
                "required_experience_years": "integer or null",
                "job_modality": "string ('On-site', 'Remote', 'Hybrid') or null",
                "deduced_job_level": "string ('Entry', 'Mid', etc.) or null",
                "position_relevance_score": "integer (1-100)", "environment_fit_score": "integer (1-100)",
                "hiring_manager_view": "string (A concise paragraph)",
                "matrix_rating": "string (A letter grade)",
                "summary": "string (A concise summary)",
                "qualification_gaps": "array of strings",
                "recommended_testimonials": "array of strings"
            }}
        """
        
        self.logger.info("Sending request to Gemini AI for job analysis.")
        try:
            response = self.model.generate_content(prompt)
            parsed_data = self._extract_json_from_response(response.text)
            if not parsed_data: raise ValueError("AI response did not contain valid JSON.")

            if not parsed_data.get('company_name') or not parsed_data.get('job_title'):
                 raise ValueError("AI analysis missing required 'company_name' or 'job_title'.")

            analysis = {key: parsed_data.get(key) for key in ["company_name", "job_title", "position_relevance_score", "environment_fit_score", "hiring_manager_view", "matrix_rating", "summary", "qualification_gaps", "recommended_testimonials"]}
            analysis['salary_min'] = self._parse_and_validate_int(parsed_data.get('salary_min'), 'salary_min')
            analysis['salary_max'] = self._parse_and_validate_int(parsed_data.get('salary_max'), 'salary_max')
            analysis['required_experience_years'] = self._parse_and_validate_int(parsed_data.get('required_experience_years'), 'required_experience_years')
            analysis['job_modality'] = self._validate_enum(parsed_data.get('job_modality'), self.VALID_JOB_MODALITIES, 'job_modality')
            analysis['deduced_job_level'] = self._validate_enum(parsed_data.get('deduced_job_level'), self.VALID_JOB_LEVELS, 'deduced_job_level')

            self.logger.info(f"Successfully parsed AI analysis for job: {analysis.get('job_title')}")
            return analysis
        except Exception as e:
            self.logger.error(f"AI analysis failed. Raw response was: {response.text if 'response' in locals() else 'N/A'}")
            self.logger.error(f"Error during AI analysis or JSON parsing: {e}")
            raise
            
    def _build_company_research_prompt(self, company_name):
        return f"""
        Act as an expert business analyst. Research the company named "{company_name}".
        Based on publicly available information, provide a concise summary in JSON format.
        The JSON object must contain these exact keys: "industry", "employee_count_range", "publicly_stated_mission", "primary_business_model".
        If you cannot find a specific piece of information, use a value of null for that key.
        Do not include any text outside of the JSON object.
        """

    def _extract_json_from_response(self, text):
        match = re.search(r'```json\s*(\{.*?\})\s*```|(\{.*?\})', text, re.DOTALL)
        if match:
            json_str = match.group(1) or match.group(2)
            try: return json.loads(json_str)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error: {e}\\nRaw text was: {json_str}")
                return None
        return None

    def _parse_and_validate_int(self, value, field_name):
        if value is None: return None
        try: return int(str(value))
        except (ValueError, TypeError):
            self.logger.warning(f"AI returned invalid integer for {field_name}: '{value}'. Setting to None.")
            return None

    def _validate_enum(self, value, valid_set, field_name):
        if value is None: return None
        if isinstance(value, str) and value.strip() in valid_set: return value.strip()
        self.logger.warning(f"AI returned invalid enum value for {field_name}: '{value}'. Setting to None.")
        return None

    def is_resume_content(self, text: str) -> bool: return self._run_ai_classification(text, 'resume')
    def is_job_posting_content(self, text: str) -> bool: return self._run_ai_classification(text, 'job_posting')

    def _run_ai_classification(self, text: str, content_type: str) -> bool:
        if not self.model: return True 
        prompt = f"""Is the following text a {content_type}? Respond YES or NO.\nTEXT: "{text[:config.MAX_CLASSIFICATION_TEXT_LENGTH]}" """
        self.logger.info(f"Sending request to Gemini AI for {content_type} classification.")
        try:
            response = self.model.generate_content(prompt)
            self.logger.info(f"AI classified {content_type} as: {'YES' if 'YES' in response.text.upper() else 'NO'}")
            return "YES" in response.text.upper()
        except Exception as e:
            self.logger.error(f"AI classification for {content_type} failed: {e}")
            return True

    def check_url_validity(self, full_url_string: str) -> bool:
        url_match = re.search(r"https?://[^\s)\]]+", full_url_string)
        if not url_match:
            self.logger.warning(f"No valid URL pattern found in string: {full_url_string}")
            return False
        clean_url = url_match.group(0)
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.head(clean_url, timeout=5, headers=headers, allow_redirects=True)
            return 200 <= response.status_code < 400
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"Unreachable URL '{clean_url}' extracted from '{full_url_string}': {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error in check_url_validity for '{clean_url}': {e}")
            return False