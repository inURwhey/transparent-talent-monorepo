import os
import psycopg2
from psycopg2.extras import DictCursor, Json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import time 

# --- Constants (Duplicate from app.py, as this script is standalone for import) ---
ANALYSIS_PROTOCOL_VERSION = '2.0'
REQUEST_TIMEOUT = 15 
AI_REQUEST_TIMEOUT = 120 
SCRAPE_DELAY = 0.5 

# --- Database Connection Helper (Duplicate from app.py) ---
def get_db_connection():
    """Helper function to get a database connection."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(db_url)

# --- AI Configuration & Helper (Duplicate from app.py) ---
# Ensure GEMINI_API_KEY is set in your Render environment for this to work
def run_job_analysis(job_description_text, user_profile_text):
    if not os.getenv('GEMINI_API_KEY'):
        raise ValueError("AI analysis cannot be run without GEMINI_API_KEY.")
    genai.configure(api_key=os.getenv('GEMINI_API_KEY')) 
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    prompt = f"""
        Analyze the following job description in the context of the provided user profile.
        Your output MUST be a single, minified JSON object with no extra text or markdown.

        USER PROFILE:
        ---
        {user_profile_text}
        ---

        JOB DESCRIPTION:
        ---
        {job_description_text}
        ---

        Based on "Protocol User-Driven Job Analysis v1.1", provide a comprehensive analysis.
        The JSON object must have the following snake_case keys:
        - "position_relevance_score": A number from 0-50.
        - "environment_fit_score": A number from 0-50.
        - "hiring_manager_view": A string, one of "Strong", "Possible", "Stretch", "Unlikely".
        - "matrix_rating": A string, one of "A", "B", "C", "D", "F".
        - "summary": A 2-4 sentence summary of the opportunity.
        - "qualification_gaps": An array of 2-3 strings listing key qualification gaps.
        - "recommended_testimonials": An array of 1-3 strings recommending impactful testimonials from the user's resume.
        - "job_title": The official job title from the description.
        - "company_name": The official company name from the description.
    """
    response = model.generate_content(prompt, request_options={"timeout": AI_REQUEST_TIMEOUT})
    cleaned_response_text = response.text.strip().replace('```json', '').replace('```', '').strip()
    return json.loads(cleaned_response_text)


def run_remediation_internal():
    """
    Re-analyzes jobs for users that are missing an analysis or have a legacy analysis protocol version.
    Filters out jobs with NULL or empty URLs.
    Returns a dictionary summarizing the results.
    """
    results = {
        'status': 'Processing',
        'total_to_process': 0,
        'processed_count': 0,
        'created_count': 0,
        'updated_count': 0,
        'failed_count': 0,
        'skipped_invalid_url_count': 0,
        'errors': []
    }
    conn = None

    try:
        conn = get_db_connection()
        conn.autocommit = False 
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Select all tracked_jobs that are missing an analysis for their user
            # OR have an analysis with the old protocol version.
            # Explicitly exclude jobs where job_url is NULL or empty
            cursor.execute("""
                SELECT
                    tj.user_id,
                    tj.job_id,
                    j.job_url::text AS job_url, 
                    ja.analysis_protocol_version AS existing_version
                FROM tracked_jobs tj
                JOIN jobs j ON tj.job_id = j.id
                LEFT JOIN job_analyses ja ON tj.user_id = ja.user_id AND tj.job_id = ja.job_id
                WHERE (ja.job_id IS NULL OR ja.analysis_protocol_version = '1.0')
                AND j.job_url IS NOT NULL AND j.job_url != '';
            """)
            jobs_to_reanalyze = cursor.fetchall()
            
            results['total_to_process'] = len(jobs_to_reanalyze)
            
            # Count jobs that were implicitly skipped due to NULL/empty URL
            cursor.execute("""
                SELECT COUNT(*)
                FROM tracked_jobs tj
                JOIN jobs j ON tj.job_id = j.id
                LEFT JOIN job_analyses ja ON tj.user_id = ja.user_id AND tj.job_id = ja.job_id
                WHERE (ja.job_id IS NULL OR ja.analysis_protocol_version = '1.0')
                AND (j.job_url IS NULL OR j.job_url = '');
            """)
            results['skipped_invalid_url_count'] = cursor.fetchone()[0]

            print(f"Found {results['total_to_process']} job-user pairs to re-analyze/create with valid URLs.")
            if results['skipped_invalid_url_count'] > 0:
                print(f"Skipped {results['skipped_invalid_url_count']} job-user pairs due to NULL/empty job_url.")
            
            profile_columns = [
                "short_term_career_goal", "ideal_role_description", "core_strengths",
                "skills_to_avoid", "preferred_industries", "industries_to_avoid",
                "desired_title", "non_negotiable_requirements", "deal_breakers"
            ]

            for i, row in enumerate(jobs_to_reanalyze):
                user_id = row['user_id']
                job_id = row['job_id']
                job_url = row['job_url'] 
                existing_version = row['existing_version']

                print(f"Processing ({i+1}/{results['total_to_process']}): User ID {user_id}, Job ID {job_id}, URL: {job_url} (Current version: {existing_version or 'N/A'})")

                try:
                    profile_sql = f"SELECT {', '.join(profile_columns)} FROM user_profiles WHERE user_id = %s"
                    cursor.execute(profile_sql, (user_id,))
                    user_profile_row = cursor.fetchone()

                    if not user_profile_row:
                        error_msg = f"Skipped (Sparse Profile): User ID {user_id} profile not found or too sparse for analysis."
                        print(f"  {error_msg}")
                        results['errors'].append(error_msg)
                        results['failed_count'] += 1
                        continue

                    user_profile_parts = []
                    profile_labels = {
                        "short_term_career_goal": "Short-Term Career Goal", "ideal_role_description": "Ideal Role",
                        "core_strengths": "Core Strengths", "skills_to_avoid": "Skills To Avoid",
                        "preferred_industries": "Preferred Industries", "industries_to_avoid": "Industries To Avoid",
                        "desired_title": "Desired Title", "non_negotiable_requirements": "Non-Negotiables",
                        "deal_breakers": "Deal Breakers"
                    }
                    for col in profile_columns:
                        value = user_profile_row[col]
                        if value and str(value).strip():
                            user_profile_parts.append(f"- {profile_labels[col]}: {value}")

                    if not user_profile_parts:
                        error_msg = f"Skipped (Sparse Profile): User profile for user_id {user_id} is too sparse for analysis."
                        print(f"  {error_msg}")
                        results['errors'].append(error_msg)
                        results['failed_count'] += 1
                        continue
                    
                    user_profile_text = "\n".join(user_profile_parts)

                    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                    try:
                        response = requests.get(job_url, headers=headers, timeout=REQUEST_TIMEOUT)
                        response.raise_for_status()
                    except requests.exceptions.Timeout:
                        error_msg = f"HTTP Timeout: Scraping {job_url} for Job ID {job_id} timed out after {REQUEST_TIMEOUT} seconds."
                        print(f"  {error_msg}")
                        results['errors'].append(error_msg)
                        results['failed_count'] += 1
                        continue 
                    except requests.exceptions.RequestException as e:
                        error_msg = f"HTTP Error: Failed to fetch {job_url} for Job ID {job_id}. Error: {e}"
                        print(f"  {error_msg}")
                        results['errors'].append(error_msg)
                        results['failed_count'] += 1
                        continue 

                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_text = soup.get_text(separator=' ', strip=True)

                    analysis_result = run_job_analysis(job_text, user_profile_text)

                    cursor.execute("""
                        INSERT INTO job_analyses (job_id, user_id, analysis_protocol_version, position_relevance_score, environment_fit_score, hiring_manager_view, matrix_rating, summary, qualification_gaps, recommended_testimonials)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (job_id, user_id) DO UPDATE SET
                            analysis_protocol_version = EXCLUDED.analysis_protocol_version,
                            position_relevance_score = EXCLUDED.position_relevance_score,
                            environment_fit_score = EXCLUDED.environment_fit_score,
                            hiring_manager_view = EXCLUDED.hiring_manager_view,
                            matrix_rating = EXCLUDED.matrix_rating,
                            summary = EXCLUDED.summary,
                            qualification_gaps = EXCLUDED.qualification_gaps,
                            recommended_testimonials = EXCLUDED.recommended_testimonials,
                            updated_at = CURRENT_TIMESTAMP;
                    """, (
                        job_id, user_id, ANALYSIS_PROTOCOL_VERSION,
                        analysis_result.get('position_relevance_score'), analysis_result.get('environment_fit_score'),
                        analysis_result.get('hiring_manager_view'), analysis_result.get('matrix_rating'),
                        analysis_result.get('summary'), Json(analysis_result.get('qualification_gaps', [])),
                        Json(analysis_result.get('recommended_testimonials', []))
                    ))
                    conn.commit() 
                    
                    if existing_version:
                        results['updated_count'] += 1
                        print(f"  SUCCESS: Updated analysis for User ID {user_id}, Job ID {job_id} to v{ANALYSIS_PROTOCOL_VERSION}.")
                    else:
                        results['created_count'] += 1
                        print(f"  SUCCESS: Created new analysis for User ID {user_id}, Job ID {job_id} at v{ANALYSIS_PROTOCOL_VERSION}.")
                    results['processed_count'] += 1

                except json.JSONDecodeError as e:
                    conn.rollback()
                    error_msg = f"AI Response Parse Error for Job ID {job_id} ({job_url}): {e}"
                    print(f"  {error_msg}")
                    results['errors'].append(error_msg)
                    results['failed_count'] += 1
                except genai.types.BlockedPromptException as e:
                    conn.rollback()
                    error_msg = f"Gemini API Blocked: Job ID {job_id} ({job_url}) blocked due to safety or content policy. {e}"
                    print(f"  {error_msg}")
                    results['errors'].append(error_msg)
                    results['failed_count'] += 1
                except genai.types.StopCandidateException as e:
                    conn.rollback()
                    error_msg = f"Gemini API Stopped: Job ID {job_id} ({job_url}) stopped generating mid-response. This often indicates issues with prompt length or internal model limits. {e}"
                    print(f"  {error_msg}")
                    results['errors'].append(error_msg)
                    results['failed_count'] += 1
                except Exception as e:
                    conn.rollback()
                    error_msg = f"Unexpected Error for Job ID {job_id} ({job_url}): {e}"
                    print(f"  {error_msg}")
                    results['errors'].append(error_msg)
                    results['failed_count'] += 1
                
                time.sleep(SCRAPE_DELAY)

    except psycopg2.Error as e:
        if conn: conn.rollback()
        results['overall_error'] = f"DATABASE ERROR during re-analysis: {e}"
        results['status'] = 'FAILED'
        results['failed_count'] = results['total_to_process'] - results['processed_count']
    except Exception as e:
        results['overall_error'] = f"An unexpected overall error occurred: {e}"
        results['status'] = 'FAILED'
        results['failed_count'] = results['total_to_process'] - results['processed_count']
    finally:
        if conn:
            conn.close()
    
    results['status'] = 'Completed' if results['failed_count'] == 0 else 'Completed with Errors'
    return results

def mark_unreachable_jobs_as_expired():
    """
    Marks tracked jobs as 'Expired - Unreachable' if their corresponding job_url is invalid/unreachable
    and they don't have a v2.0 analysis.
    """
    results = {
        'status': 'Processing',
        'marked_count': 0,
        'errors': []
    }
    conn = None
    try:
        conn = get_db_connection()
        conn.autocommit = False
        with conn.cursor() as cursor:
            # Corrected SQL query for UPDATE FROM syntax
            update_query = """
                UPDATE tracked_jobs
                SET
                    status = 'Expired - Unreachable',
                    applied_at = NULL, 
                    updated_at = CURRENT_TIMESTAMP
                FROM jobs j
                LEFT JOIN job_analyses ja ON tracked_jobs.user_id = ja.user_id AND tracked_jobs.job_id = ja.job_id
                WHERE tracked_jobs.job_id = j.id -- This links tracked_jobs with jobs
                AND (ja.job_id IS NULL OR ja.analysis_protocol_version != '2.0') 
                AND (
                    j.job_url IS NULL OR
                    j.job_url = '' OR
                    j.job_url = 'None' OR 
                    j.job_id = %s -- Specifically target Job ID 11 which previously returned a 404
                )
                RETURNING tracked_jobs.id;
            """
            cursor.execute(update_query, (11,)) # Pass Job ID 11 as a parameter
            marked_jobs_ids = cursor.fetchall()
            conn.commit()
            results['marked_count'] = len(marked_jobs_ids)
            results['status'] = 'Completed'
            print(f"Successfully marked {results['marked_count']} jobs as 'Expired - Unreachable'.")

    except psycopg2.Error as e:
        if conn: conn.rollback()
        error_msg = f"DATABASE ERROR during marking unreachable jobs: {e}"
        results['overall_error'] = error_msg
        results['status'] = 'FAILED'
        results['errors'].append(error_msg)
        print(f"ERROR: {error_msg}")
    except Exception as e:
        if conn: conn.rollback()
        error_msg = f"An unexpected error occurred during marking unreachable jobs: {e}"
        results['overall_error'] = error_msg
        results['status'] = 'FAILED'
        results['errors'].append(error_msg)
        print(f"ERROR: {error_msg}")
    finally:
        if conn:
            conn.close()
    return results