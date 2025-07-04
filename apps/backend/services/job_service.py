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

class JobService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger
        self.profile_service = ProfileService(self.logger)

    def _call_gemini_api(self, prompt, model_name="gemini-1.5-pro-latest"):
        api_key = config.GEMINI_API_KEY
        if not api_key:
            self.logger.error("Gemini API key is not configured.")
            return None

        # Using the v1 endpoint as confirmed by the successful list-models call
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        
        headers = { "Content-Type": "application/json", "x-goog-api-key": api_key }
        
        # CORRECTED: Removed the entire 'generationConfig' object. 
        # The API for this model does not support it, which was causing the 400 Bad Request.
        payload = {
            "contents": [{"parts": [{"text": prompt}]}]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            # We now rely on robust parsing since we can't force a JSON MIME type.
            text_content = data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            if not text_content:
                self.logger.error("Gemini API returned empty text response.", extra={'full_response': data})
                return None
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
            return {"title": title[:255], "company_name": company_name[:255], "description": description}
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
            return parsed_data
        except Exception as e:
            self.logger.error(f"Failed to parse AI response: {e}. Raw: {ai_response_text[:500]}")
            return None

    def analyze_job_posting(self, job_text, user_profile_data, company_profile_data=None):
        if not job_text: return None
        profile_str = json.dumps(user_profile_data, indent=2) if user_profile_data else "{}"
        company_str = json.dumps(company_profile_data, indent=2) if company_profile_data else "{}"
        prompt = f"""
        Analyze the following job posting, user profile, and company context...
        Output a JSON object...
        """
        
        ai_response = self._call_gemini_api(prompt, model_name="gemini-1.5-pro-latest")
        
        if ai_response: return self._parse_ai_response(ai_response)
        return None
    
    def create_or_get_canonical_job(self, url: str, user_id: int, commit: bool = True):
        return Job(), JobOpportunity()

    def create_or_update_job_analysis(self, user_id, job_id, ai_analysis_data):
        return JobAnalysis()

    def trigger_reanalysis_for_user(self, user_id: int):
        return