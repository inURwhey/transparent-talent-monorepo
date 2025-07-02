# Path: apps/backend/services/company_service.py
import google.generativeai as genai
import json
import re
from flask import current_app
from ..config import config
from ..database import get_db

# This version helps track which version of our prompt/logic generated the data.
COMPANY_RESEARCH_PROTOCOL_VERSION = "1.0"

class CompanyService:
    def __init__(self):
        # Configure the Gemini client if the key is available
        if not hasattr(config, 'GEMINI_API_KEY') or not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not configured.")
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')

    def research_and_update_company_profile(self, company_id):
        db = get_db()
        with db.cursor() as cursor:
            # 1. Get company name
            cursor.execute("SELECT name FROM companies WHERE id = %s", (company_id,))
            company = cursor.fetchone()
            if not company:
                return {"success": False, "message": "Company not found", "status_code": 404}
            
            company_name = company.get('name')
            current_app.logger.info(f"Initiating AI research for company: {company_name} (ID: {company_id})")

            # 2. Call Gemini API
            prompt = self._build_prompt(company_name)
            try:
                response = self.model.generate_content(prompt)
                # Extract JSON from the response text, handling markdown code blocks
                json_data = self._extract_json(response.text)
                if not json_data:
                    current_app.logger.error(f"Failed to extract JSON from Gemini response for {company_name}")
                    return {"success": False, "message": "AI response was not valid JSON.", "status_code": 500}

            except Exception as e:
                current_app.logger.error(f"Gemini API call failed for {company_name}: {e}")
                return {"success": False, "message": f"Gemini API call failed: {e}", "status_code": 502}

            # 3. UPSERT (INSERT or UPDATE) the data
            try:
                cursor.execute(
                    """
                    INSERT INTO company_profiles (
                        company_id, industry, employee_count_range, publicly_stated_mission,
                        primary_business_model, researched_at, ai_model_version
                    ) VALUES (%s, %s, %s, %s, %s, NOW(), %s)
                    ON CONFLICT (company_id) DO UPDATE SET
                        industry = EXCLUDED.industry,
                        employee_count_range = EXCLUDED.employee_count_range,
                        publicly_stated_mission = EXCLUDED.publicly_stated_mission,
                        primary_business_model = EXCLUDED.primary_business_model,
                        researched_at = NOW(),
                        ai_model_version = EXCLUDED.ai_model_version,
                        updated_at = NOW()
                    RETURNING id;
                    """,
                    (
                        company_id,
                        json_data.get('industry'),
                        json_data.get('employee_count_range'),
                        json_data.get('publicly_stated_mission'),
                        json_data.get('primary_business_model'),
                        COMPANY_RESEARCH_PROTOCOL_VERSION
                    )
                )
                profile_id = cursor.fetchone()['id']
                db.commit()
                current_app.logger.info(f"Successfully saved company profile for {company_name}. Profile ID: {profile_id}")
                return {"success": True, "message": "Company profile updated successfully.", "profile_id": profile_id, "status_code": 200}

            except Exception as e:
                db.rollback()
                current_app.logger.error(f"Database error while saving company profile for {company_name}: {e}")
                return {"success": False, "message": f"Database error: {e}", "status_code": 500}

    def _build_prompt(self, company_name):
        return f"""
        Act as an expert business analyst. Research the company named "{company_name}".
        Based on publicly available information, provide a concise summary in JSON format.

        The JSON object must contain these exact keys and nothing else:
        - "industry": The primary industry of the company (e.g., "Enterprise Software", "Healthcare Technology", "E-commerce").
        - "employee_count_range": The estimated current number of employees as a range (e.g., "1-50", "51-200", "201-500", "501-1000", "1001-5000", "5001+").
        - "publicly_stated_mission": The company's official mission or vision statement, summarized in one or two sentences.
        - "primary_business_model": The company's core business model (e.g., "B2B SaaS", "D2C E-commerce", "Advertising", "Marketplace").

        If you cannot find a specific piece of information, use a value of null for that key.
        Do not include any introductory text or explanations outside of the JSON object.

        Example output:
        ```json
        {{
          "industry": "Artificial Intelligence",
          "employee_count_range": "501-1000",
          "publicly_stated_mission": "To ensure that artificial general intelligence benefits all of humanity.",
          "primary_business_model": "Research and development with API access licensing."
        }}
        ```

        JSON data:
        """

    def _extract_json(self, text):
        # Use regex to find JSON within markdown code blocks (```json ... ```) or standalone
        match = re.search(r'```json\s*(\{.*?\})\s*```|(\{.*?\})', text, re.DOTALL)
        if match:
            # Prioritize the content of the json block if it exists
            json_str = match.group(1) if match.group(1) else match.group(2)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError as e:
                current_app.logger.error(f"JSON decode error: {e}\\nRaw text was: {json_str}")
                return None
        return None