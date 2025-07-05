# Path: apps/backend/services/company_service.py
import requests
import json
import re
from flask import current_app
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import pytz

from ..app import db
from ..models import Company
from ..config import config

GEMINI_PRO_MODEL = "gemini-1.5-pro"

class CompanyService:
    def __init__(self, logger=None):
        self.logger = logger or current_app.logger

    def _call_gemini_api(self, prompt, model_name=GEMINI_PRO_MODEL):
        api_key = config.GEMINI_API_KEY
        if not api_key:
            self.logger.error("Gemini API key is not configured.")
            return None

        # CORRECTED: Using the robust v1beta endpoint and header-based auth
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        headers = { 
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        payload = { "contents": [{"parts": [{"text": prompt}]}] }

        try:
            self.logger.info(f"Calling Gemini for company research with model {model_name}")
            response = requests.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
            data = response.json()
            
            candidates = data.get('candidates', [])
            if not candidates:
                self.logger.error("Company research: Gemini API returned no candidates.", extra={'full_response': data})
                return None
            
            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                self.logger.error("Company research: Gemini API returned no parts in content.", extra={'full_response': data})
                return None

            text_content = parts[0].get('text', '')
            if not text_content:
                self.logger.error("Company research: Gemini API returned empty text response.", extra={'full_response': data})
                return None
            
            return text_content
        except requests.exceptions.RequestException as e:
            if e.response is not None:
                self.logger.error(f"Company research Gemini API Error: {e.response.status_code} - {e.response.text}")
            else:
                self.logger.error(f"Company research Gemini API Error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error in company research Gemini API call: {e}", exc_info=True)
            return None

    def _parse_company_ai_response(self, ai_response):
        """Parses and validates the JSON output from company AI research."""
        if not ai_response: return None
        try:
            # CORRECTED: Using the more robust regex from job_service.py
            match = re.search(r"```json\s*([\s\S]*?)\s*```", ai_response, re.DOTALL)
            json_string = match.group(1).strip() if match else ai_response.strip()
            json_string = re.sub(r",\s*([\}\]])", r"\1", json_string)
            
            parsed_data = json.loads(json_string)

            # Basic validation and cleaning
            parsed_data['name'] = parsed_data.get('name', 'Unknown Company').strip()
            parsed_data['company_size_min'] = int(parsed_data['company_size_min']) if parsed_data.get('company_size_min') else None
            parsed_data['company_size_max'] = int(parsed_data['company_size_max']) if parsed_data.get('company_size_max') else None

            return parsed_data
        except Exception as e:
            self.logger.error(f"Error processing company AI response: {e}. Raw response: {ai_response[:500]}")
            return None

    def research_and_update_company_profile(self, company_id: int):
        """
        Performs AI-driven research to enrich a company's profile.
        If company does not exist, it will not create it (expects pre-existing company).
        """
        company = Company.query.filter_by(id=company_id).first()
        if not company:
            self.logger.warning(f"Company ID {company_id} not found for research. Skipping.")
            return None

        if company.industry and company.description and company.mission:
            self.logger.info(f"Company {company.name} (ID: {company.id}) already has sufficient profile data. Skipping research.")
            return company

        self.logger.info(f"Starting AI research for company: {company.name} (ID: {company.id})")

        prompt = f"""
        Research the following company and provide a structured JSON output with key information.
        If a piece of information cannot be found, use null.
        Company Name: {company.name}
        {f"Company Website (if known): {company.website_url}" if company.website_url else ""}

        Output a JSON object with the following structure:
        - name (string, exact company name)
        - industry (string, e.g., "Software Development", "Financial Services")
        - description (string, a brief overview of what the company does)
        - mission (string, the company's stated mission or core purpose)
        - business_model (string, how the company generates revenue)
        - company_size_min (integer, minimum employee count, nullable)
        - company_size_max (integer, maximum employee count, nullable)
        - headquarters (string, city, state, country)
        - founded_year (integer, nullable)
        - website_url (string, official website, nullable)

        Strictly conform to the JSON structure and wrap the entire response in ```json ... ```.
        """
        
        ai_response = self._call_gemini_api(prompt, model_name=GEMINI_PRO_MODEL)

        if ai_response:
            parsed_data = self._parse_company_ai_response(ai_response)
            if parsed_data:
                company.name = parsed_data.get('name', company.name)
                company.industry = parsed_data.get('industry', company.industry)
                company.description = parsed_data.get('description', company.description)
                company.mission = parsed_data.get('mission', company.mission)
                company.business_model = parsed_data.get('business_model', company.business_model)
                company.company_size_min = parsed_data.get('company_size_min', company.company_size_min)
                company.company_size_max = parsed_data.get('company_size_max', company.company_size_max)
                company.headquarters = parsed_data.get('headquarters', company.headquarters)
                company.founded_year = parsed_data.get('founded_year', company.founded_year)
                company.website_url = parsed_data.get('website_url', company.website_url)
                company.updated_at = datetime.now(pytz.utc)

                try:
                    db.session.commit()
                    self.logger.info(f"Successfully updated company profile for {company.name} (ID: {company.id}).")
                    return company
                except Exception as e:
                    db.session.rollback()
                    self.logger.error(f"Error saving updated company profile for {company.name}: {e}", exc_info=True)
                    return None
            else:
                self.logger.error(f"AI company research for {company.name} (ID: {company.id}) failed to parse response.")
                return None
        else:
            self.logger.warning(f"AI company research for {company.name} (ID: {company.id}) received empty response.")
            return None

    def get_company(self, company_id: int):
        return Company.query.filter_by(id=company_id).first()

    def get_company_by_name(self, company_name: str):
        return Company.query.filter(db.func.lower(Company.name) == company_name.lower()).first()