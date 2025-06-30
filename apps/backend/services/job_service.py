# Path: apps/backend/services/job_service.py

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
            
            if not job_text or len(job_text) < 100:
                 raise ValueError("Extracted job text is too short or empty.")

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

        # --- IMPORTANT AI PROMPT UPDATE ---
        # Updated instructions for matrix_rating to output a letter grade
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
                "position_relevance_score": "integer (1-100)",
                "environment_fit_score": "integer (1-100)",
                "hiring_manager_view": "string (A concise paragraph from the hiring manager's perspective on the candidate's fit)",
                "matrix_rating": "string (A letter grade based on the average of position_relevance_score and environment_fit_score, e.g., 'A+', 'B', 'F')",
                "summary": "string (A concise, professional summary of the role and its alignment with the user's goals)",
                "qualification_gaps": "array of strings (List specific, actionable qualification gaps)",
                "recommended_testimonials": "array of strings (List 3-5 specific skills or experiences from the user's profile to highlight)"
            }}
        """
        # --- END IMPORTANT AI PROMPT UPDATE ---
        
        self.logger.info("Sending request to Gemini AI for job analysis.")
        try:
            response = self.model.generate_content(prompt)
            # Clean the response text by removing markdown backticks and 'json' label
            cleaned_response = re.sub(r'```json\s*|\s*```', '', response.text.strip())
            
            self.logger.info("Received AI response. Attempting to parse JSON.")
            return json.loads(cleaned_response)
        except Exception as e:
            self.logger.error(f"AI analysis failed. Raw response was: {response.text}")
            self.logger.error(f"Error during AI analysis or JSON parsing: {e}")
            raise # Re-raise to be handled by the route

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