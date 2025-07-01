import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import re
from ..config import config

class JobService:
    def __init__(self, logger):
        """
        Initializes the Job Service.

        Args:
            logger: The Flask app's logger instance for logging messages.
        """
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

        # Define valid ENUM values for validation of AI output
        self.VALID_JOB_MODALITIES = {'On-site', 'Remote', 'Hybrid'}
        self.VALID_JOB_LEVELS = {'Entry', 'Mid', 'Senior', 'Staff', 'Principal', 'Manager', 'Director', 'VP', 'C-Suite'}


    def get_job_details_and_analysis(self, job_url: str, user_profile_text: str):
        """
        Fetches job text from a URL and performs an AI analysis against a user profile.

        Args:
            job_url: The URL of the job posting.
            user_profile_text: A string containing the user's formatted profile data.

        Returns:
            A dictionary containing the job text and the structured AI analysis result,
            or raises an exception if fetching or analysis fails.
        """
        self.logger.info(f"Fetching job text for URL: {job_url}")
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            response = requests.get(job_url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            job_text = soup.get_text(separator=' ', strip=True)
            
            # Job text length validation
            if not job_text or len(job_text) < 100:
                 raise ValueError("Extracted job text is too short or empty for meaningful analysis.")
            if len(job_text) > config.MAX_JOB_TEXT_LENGTH:
                raise ValueError(f"Extracted job text too long ({len(job_text)} characters). Please keep it under {config.MAX_JOB_TEXT_LENGTH} characters.")

            # --- NEW: AI Classification Check ---
            is_job_posting = self.is_job_posting_content(job_text)
            if not is_job_posting:
                raise ValueError("The provided text does not appear to be a job posting. Please submit a valid job description URL.")
            # --- END NEW ---

            self.logger.info(f"Successfully fetched job text. Length: {len(job_text)} characters.")
            
            analysis = self._run_ai_analysis(job_text, user_profile_text)
            
            return {
                "job_text": job_text,
                "analysis": analysis
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch job URL '{job_url}': {e}")
            raise  # Re-raise the exception to be handled by the route
        except Exception as e:
            self.logger.error(f"An unexpected error occurred in get_job_details_and_analysis for url '{job_url}': {e}")
            raise


    def _run_ai_analysis(self, job_text: str, user_profile_text: str) -> dict:
        """
        Private method to run the job analysis using the configured AI model.
        """
        if not self.model:
            self.logger.error("Cannot run AI analysis: Model is not configured.")
            raise ConnectionError("AI Service is not configured due to missing API key.")

        # Updated instructions for matrix_rating to output a letter grade
        # Also added instructions for new structured data fields
        prompt = f"""
            You are a meticulous career-focused analyst for a platform called "Transparent Talent".
            Your task is to analyze a job description in the context of a user's professional profile.
            Produce a JSON object with the exact keys specified below. Do not include any introductory text or markdown formatting.

            For the 'matrix_rating', calculate the average of 'position_relevance_score' and 'environment_fit_score'.
            Then, assign a letter grade based on this average:
            - 90-100: A+
            - 80-89: A
            - 70-79: B+
            - 60-69: B
            - 50-59: C+
            - 40-49: C
            - 30-39: D
            - 0-29: F

            Extract the following structured data points from the job description:
            - `salary_min` and `salary_max`: The minimum and maximum annual salary in USD. If only one value is given, use it for both min and max. If a range like "$150k - $180k" is given, extract both numbers. If "DOE" (Depends On Experience), "Competitive", or no salary is stated, set to null.
            - `required_experience_years`: The minimum number of years of experience explicitly stated or clearly implied by the role's seniority (e.g., "Senior" often implies 5+ years, "Director" implies 10+). If not stated or ambiguously implied (e.g. "several years"), set to null.
            - `job_modality`: The work arrangement. Choose exactly one from "On-site", "Remote", or "Hybrid". Infer based on location keywords (e.g., "New York, NY" implies On-site unless stated otherwise), explicit remote policy, or hybrid mentions. If unsure or if role can be either (e.g., "remote/in-office"), set to null.
            - `deduced_job_level`: The seniority level of the role. Choose exactly one from "Entry", "Mid", "Senior", "Staff", "Principal", "Manager", "Director", "VP", "C-Suite". Infer based on title, responsibilities, and implied years of experience. If unsure, set to null.

            USER PROFILE:
            ---
            {user_profile_text}
            ---

            JOB DESCRIPTION:
            ---
            {job_text}
            ---

            JSON_OUTPUT_SCHEMA:
            {{
                "company_name": "string",
                "job_title": "string",
                "salary_min": "integer (annual salary in USD, e.g., 120000) or null",
                "salary_max": "integer (annual salary in USD, e.g., 150000) or null",
                "required_experience_years": "integer (e.g., 5) or null",
                "job_modality": "string ('On-site', 'Remote', 'Hybrid') or null",
                "deduced_job_level": "string ('Entry', 'Mid', 'Senior', 'Staff', 'Principal', 'Manager', 'Director', 'VP', 'C-Suite') or null",
                "position_relevance_score": "integer (1-100)",
                "environment_fit_score": "integer (1-100)",
                "hiring_manager_view": "string (A concise paragraph from the hiring manager's perspective on the candidate's fit)",
                "matrix_rating": "string (A letter grade based on the average of position_relevance_score and environment_fit_score, e.g., 'A+', 'B', 'F')",
                "summary": "string (A concise, professional summary of the role and its alignment with the user's goals)",
                "qualification_gaps": "array of strings (List specific, actionable qualification gaps)",
                "recommended_testimonials": "array of strings (List 3-5 specific skills or experiences from the user's profile to highlight)"
            }}
        """
        
        self.logger.info("Sending request to Gemini AI for job analysis.")
        try:
            response = self.model.generate_content(prompt)
            # Clean the response text by removing markdown backticks and 'json' label
            cleaned_response = re.sub(r'```json\s*|\s*```', '', response.text.strip())
            
            self.logger.info("Received AI response. Attempting to parse JSON.")
            parsed_data = json.loads(cleaned_response)

            # --- Extract and Validate New Structured Fields ---
            analysis = {}
            # Copy existing fields first
            for key in ["company_name", "job_title", "position_relevance_score", "environment_fit_score",
                        "hiring_manager_view", "matrix_rating", "summary", "qualification_gaps", "recommended_testimonials"]:
                analysis[key] = parsed_data.get(key)
            
            # New structured fields with validation/casting
            analysis['salary_min'] = self._parse_and_validate_int(parsed_data.get('salary_min'), 'salary_min')
            analysis['salary_max'] = self._parse_and_validate_int(parsed_data.get('salary_max'), 'salary_max')
            analysis['required_experience_years'] = self._parse_and_validate_int(parsed_data.get('required_experience_years'), 'required_experience_years')
            analysis['job_modality'] = self._validate_enum(parsed_data.get('job_modality'), self.VALID_JOB_MODALITIES, 'job_modality')
            analysis['deduced_job_level'] = self._validate_enum(parsed_data.get('deduced_job_level'), self.VALID_JOB_LEVELS, 'deduced_job_level')

            self.logger.info(f"Successfully parsed and validated AI analysis for job. Modality: {analysis.get('job_modality')}, Level: {analysis.get('deduced_job_level')}, Salary: {analysis.get('salary_min')}-{analysis.get('salary_max')}")
            return analysis
        except Exception as e:
            self.logger.error(f"AI analysis failed. Raw response was: {response.text if 'response' in locals() else 'N/A'}")
            self.logger.error(f"Error during AI analysis or JSON parsing: {e}")
            raise # Re-raise to be handled by the route

    # --- New Helper Methods for Validation ---
    def _parse_and_validate_int(self, value, field_name):
        if value is None:
            return None
        try:
            # Attempt to convert to string first to handle cases like Decimal, then int
            return int(str(value))
        except (ValueError, TypeError):
            self.logger.warning(f"AI returned invalid integer for {field_name}: '{value}'. Setting to None.")
            return None

    def _validate_enum(self, value, valid_set, field_name):
        if value is None:
            return None
        if isinstance(value, str) and value.strip() in valid_set:
            return value.strip()
        self.logger.warning(f"AI returned invalid enum value for {field_name}: '{value}'. Expected one of {valid_set}. Setting to None.")
        return None
    # --- END New Helper Methods ---


    # --- NEW: AI Classification Methods ---
    def is_resume_content(self, text: str) -> bool:
        """
        Uses AI to classify if the given text content is a resume.
        Returns True if it's a resume, False otherwise.
        """
        return self._run_ai_classification(text, 'resume')

    def is_job_posting_content(self, text: str) -> bool:
        """
        Uses AI to classify if the given text content is a job posting.
        Returns True if it's a job posting, False otherwise.
        """
        return self._run_ai_classification(text, 'job_posting')

    def _run_ai_classification(self, text: str, content_type: str) -> bool:
        """
        Private method to run a lightweight AI classification.
        """
        if not self.model:
            self.logger.error("Cannot run AI classification: Model is not configured.")
            # For classification, we can default to True if AI is down to avoid blocking,
            # and rely on downstream parsing for actual errors.
            return True 

        classification_prompt = f"""
            Analyze the following text content. Determine if it is a valid and recognizable {content_type}.
            Respond with only "YES" if it is, and "NO" if it is not.
            Do not include any other text, punctuation, or formatting.

            TEXT CONTENT:
            ---
            {text[:config.MAX_CLASSIFICATION_TEXT_LENGTH]} # Use a limited length for classification to save tokens
            ---
            Is this a {content_type}? (YES/NO):
        """
        self.logger.info(f"Sending request to Gemini AI for {content_type} classification.")
        try:
            response = self.model.generate_content(classification_prompt)
            # Clean and normalize response for robust comparison
            cleaned_response = response.text.strip().upper()
            self.logger.info(f"AI classified {content_type} as: {cleaned_response}")
            return cleaned_response == "YES"
        except Exception as e:
            self.logger.error(f"AI classification for {content_type} failed: {e}")
            # If AI classification fails, assume valid to avoid blocking valid submissions due to AI issues.
            # Downstream parsing will catch if it's truly invalid.
            return True
    # --- END NEW ---

    def check_url_validity(self, full_url_string: str) -> bool:
        """
        Extracts a clean URL and performs an HTTP HEAD request to check if it's reachable.
        """
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