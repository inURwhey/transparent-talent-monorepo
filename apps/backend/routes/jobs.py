from flask import Blueprint, request, jsonify, g, current_app
from psycopg2.extras import Json
from ..auth import token_required
from ..services.job_service import JobService
from ..services.profile_service import ProfileService
from ..database import get_db
from ..config import config
import psycopg2

jobs_bp = Blueprint('jobs_bp', __name__)

@jobs_bp.route('/jobs/submit', methods=['POST'])
@token_required
def submit_job():
    user_id = g.current_user['id']
    data = request.get_json()
    job_url = data.get('job_url')
    if not job_url:
        return jsonify({"error": "job_url is required"}), 400

    job_service = JobService(current_app.logger)
    profile_service = ProfileService(current_app.logger)
    db = get_db()
    
    try:
        # 1. Check if user is already tracking this job
        with db.cursor() as cursor:
            cursor.execute("""
                SELECT t.id FROM tracked_jobs t JOIN jobs j ON t.job_id = j.id 
                WHERE t.user_id = %s AND j.job_url = %s
            """, (user_id, job_url))
            if cursor.fetchone():
                return jsonify({"error": "You are already tracking this job."}), 409

        # 2. Get user profile and run analysis
        user_profile_text = profile_service.get_profile_for_analysis(user_id)
        job_data = job_service.get_job_details_and_analysis(job_url, user_profile_text)
        analysis_result = job_data['analysis']

        with db.cursor() as cursor:
            # 3. Handle Company
            company_name = analysis_result.get('company_name', 'Unknown Company')
            cursor.execute("SELECT id FROM companies WHERE LOWER(name) = LOWER(%s)", (company_name,))
            company_row = cursor.fetchone()
            company_id = company_row['id'] if company_row else cursor.execute(
                "INSERT INTO companies (name) VALUES (%s) RETURNING id", (company_name,)
            ) and cursor.fetchone()['id']
            
            # 4. UPSERT Job
            job_title = analysis_result.get('job_title', 'Unknown Title')
            cursor.execute("""
                INSERT INTO jobs (company_id, company_name, job_title, job_url, source, status, last_checked_at)
                VALUES (%s, %s, %s, %s, %s, 'Active', NOW())
                ON CONFLICT (job_url) DO UPDATE SET
                    job_title = EXCLUDED.job_title,
                    status = 'Active',
                    last_checked_at = NOW()
                RETURNING id;
            """, (company_id, company_name, job_title, job_url, 'User Submission'))
            job_id = cursor.fetchone()['id']

            # 5. UPSERT Job Analysis
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
                    updated_at = NOW();
            """, (
                job_id, user_id, config.ANALYSIS_PROTOCOL_VERSION,
                analysis_result.get('position_relevance_score'), analysis_result.get('environment_fit_score'),
                analysis_result.get('hiring_manager_view'), analysis_result.get('matrix_rating'),
                analysis_result.get('summary'), Json(analysis_result.get('qualification_gaps', [])),
                Json(analysis_result.get('recommended_testimonials', []))
            ))

            # 6. Create Tracked Job - status now defaults to 'SAVED' via the DB
            cursor.execute("INSERT INTO tracked_jobs (user_id, job_id) VALUES (%s, %s) RETURNING id;", (user_id, job_id))
            tracked_job_id = cursor.fetchone()['id']
            
            db.commit()

        # 7. Fetch and return the newly created tracked job data
        with db.cursor() as cursor:
            new_job_data = _get_tracked_job_by_id(cursor, tracked_job_id)
            return jsonify(new_job_data), 201

    except ValueError as e: # Catch specific errors from services
        return jsonify({"error": str(e)}), 400
    except (requests.exceptions.RequestException, ConnectionError) as e:
        return jsonify({"error": f"Service Error: {str(e)}"}), 503
    except psycopg2.Error as e:
        db.rollback()
        current_app.logger.error(f"DATABASE ERROR in submit_job route: {e}")
        return jsonify({"error": "A database error occurred."}), 500
    except Exception as e:
        db.rollback()
        current_app.logger.error(f"An unexpected error occurred in submit_job route: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500


@jobs_bp.route('/tracked-jobs', methods=['GET'])
@token_required
def get_tracked_jobs():
    user_id = g.current_user['id']
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid pagination parameters"}), 400

    offset = (page - 1) * limit
    db = get_db()
    
    with db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM tracked_jobs WHERE user_id = %s;", (user_id,))
        total_count = cursor.fetchone()[0]

        # Query now includes all the new columns
        cursor.execute("""
            SELECT 
                j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                j.status as job_posting_status, j.last_checked_at,
                t.* 
            FROM jobs j
            JOIN tracked_jobs t ON j.id = t.job_id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT %s OFFSET %s;
        """, (user_id, limit, offset))
        
        # We need to fetch the analysis separately now as t.* includes job_id
        # For simplicity in this step, we will keep the original query structure which is less efficient
        # but correct. A future refactor could optimize this.
        cursor.execute("""
            SELECT 
                j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
                j.status as job_posting_status, j.last_checked_at,
                t.id as tracked_job_id, t.status, t.notes, t.applied_at, t.created_at, t.is_excited, t.status_reason,
                t.first_interview_at, t.offer_received_at, t.resolved_at, t.next_action_at, t.next_action_notes,
                ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
                ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
            FROM jobs j
            JOIN tracked_jobs t ON j.id = t.job_id
            LEFT JOIN job_analyses ja ON j.id = ja.job_id AND t.user_id = ja.user_id
            WHERE t.user_id = %s
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT %s OFFSET %s;
        """, (user_id, limit, offset))
        
        tracked_jobs = [_format_tracked_job(row) for row in cursor.fetchall()]
        
        return jsonify({
            "tracked_jobs": tracked_jobs,
            "total_count": total_count,
            "page": page,
            "limit": limit
        })

@jobs_bp.route('/tracked-jobs/<int:tracked_job_id>', methods=['PUT'])
@token_required
def update_tracked_job(tracked_job_id):
    user_id = g.current_user['id']
    data = request.get_json()
    if not data:
        return jsonify({"error": "No update data provided"}), 400
    
    # Updated list of fields that can be modified
    allowed_fields = [
        'status', 'notes', 'is_excited', 'status_reason', 
        'applied_at', 'first_interview_at', 'offer_received_at', 
        'resolved_at', 'next_action_at', 'next_action_notes'
    ]
    fields_to_update = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not fields_to_update:
        return jsonify({"error": "No valid fields to update"}), 400

    # The `updated_at` field is now handled by a trigger, so we don't need to set it manually
    set_clauses = [f"{field} = %s" for field in fields_to_update.keys()]
    params = list(fields_to_update.values())
    params.append(tracked_job_id)
    params.append(user_id)

    db = get_db()
    with db.cursor() as cursor:
        cursor.execute(f"""
            UPDATE tracked_jobs SET {', '.join(set_clauses)}
            WHERE id = %s AND user_id = %s RETURNING id;
        """, tuple(params))
        
        updated_row = cursor.fetchone()
        if not updated_row:
            return jsonify({"error": "Tracked job not found or permission denied"}), 404
        
        db.commit()
        updated_job_data = _get_tracked_job_by_id(cursor, updated_row['id'])
        return jsonify(updated_job_data), 200


@jobs_bp.route('/tracked-jobs/<int:tracked_job_id>', methods=['DELETE'])
@token_required
def remove_tracked_job(tracked_job_id):
    user_id = g.current_user['id']
    db = get_db()
    with db.cursor() as cursor:
        cursor.execute("DELETE FROM tracked_jobs WHERE id = %s AND user_id = %s RETURNING id", (tracked_job_id, user_id))
        if cursor.fetchone():
            db.commit()
            return jsonify({"message": "Tracked job removed successfully"}), 200
        else:
            return jsonify({"error": "Tracked job not found or permission denied"}), 404

# --- Private Helper Functions ---

def _get_tracked_job_by_id(cursor, tracked_job_id):
    """Fetches a single tracked job by its ID, formats it, and returns it."""
    cursor.execute("""
        SELECT 
            j.id as job_id, j.company_name, j.job_title, j.job_url, j.source, j.found_at,
            j.status as job_posting_status, j.last_checked_at,
            t.id as tracked_job_id, t.status, t.notes, t.applied_at, t.created_at, t.is_excited, t.status_reason,
            t.first_interview_at, t.offer_received_at, t.resolved_at, t.next_action_at, t.next_action_notes,
            ja.position_relevance_score, ja.environment_fit_score, ja.hiring_manager_view,
            ja.matrix_rating, ja.summary as ai_summary, ja.qualification_gaps, ja.recommended_testimonials
        FROM jobs j
        JOIN tracked_jobs t ON j.id = t.job_id
        LEFT JOIN job_analyses ja ON j.id = ja.job_id AND t.user_id = ja.user_id
        WHERE t.id = %s;
    """, (tracked_job_id,))
    row = cursor.fetchone()
    return _format_tracked_job(row) if row else None

def _format_tracked_job(row):
    """Formats a row from the database into the standard tracked job JSON structure."""
    if not row: return None
    
    job = {
        "tracked_job_id": row["tracked_job_id"],
        "job_id": row["job_id"],
        "job_title": row["job_title"],
        "company_name": row["company_name"],
        "job_url": row["job_url"],
        "status": row["status"], # Now an ENUM from the DB
        "user_notes": row["notes"],
        "applied_at": row["applied_at"],
        "created_at": row["created_at"],
        "is_excited": row["is_excited"],
        "job_posting_status": row["job_posting_status"],
        "last_checked_at": row["last_checked_at"],
        "status_reason": row["status_reason"],
        "first_interview_at": row["first_interview_at"],
        "offer_received_at": row["offer_received_at"],
        "resolved_at": row["resolved_at"],
        "next_action_at": row["next_action_at"],
        "next_action_notes": row["next_action_notes"],
        "ai_analysis": None
    }
    if row["position_relevance_score"] is not None:
        job["ai_analysis"] = {
            "position_relevance_score": row["position_relevance_score"],
            "environment_fit_score": row["environment_fit_score"],
            "hiring_manager_view": row["hiring_manager_view"],
            "matrix_rating": row["matrix_rating"],
            "summary": row["ai_summary"],
            "qualification_gaps": row["qualification_gaps"],
            "recommended_testimonials": row["recommended_testimonials"]
        }
    return job