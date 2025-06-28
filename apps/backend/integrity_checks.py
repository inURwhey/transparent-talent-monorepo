import click
from flask.cli import with_appcontext
from psycopg2.extras import DictCursor
import os
import psycopg2

def get_db_connection():
    """Helper function to get a database connection."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url: raise ValueError("DATABASE_URL not set")
    return psycopg2.connect(db_url)

def run_integrity_checks_internal():
    """
    Runs a series of non-destructive data integrity checks and returns a dictionary of results.
    """
    results = {}
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Check 1: Tracked jobs missing a corresponding user-specific analysis
            cursor.execute("""
                SELECT COUNT(*)
                FROM tracked_jobs tj
                LEFT JOIN job_analyses ja ON tj.user_id = ja.user_id AND tj.job_id = ja.job_id
                WHERE ja.job_id IS NULL;
            """)
            missing_analyses_count = cursor.fetchone()[0]
            results['missing_user_job_analyses'] = {
                'count': missing_analyses_count,
                'status': 'WARNING' if missing_analyses_count > 0 else 'OK',
                'message': f"Found {missing_analyses_count} tracked jobs missing a user-specific analysis."
            }

            # Check 2: Analyses created with a legacy protocol version
            cursor.execute("SELECT COUNT(*) FROM job_analyses WHERE analysis_protocol_version = '1.0';")
            legacy_analyses_count = cursor.fetchone()[0]
            results['legacy_analyses_v1_0'] = {
                'count': legacy_analyses_count,
                'status': 'INFO' if legacy_analyses_count > 0 else 'OK',
                'message': f"Found {legacy_analyses_count} legacy (v1.0) analyses that could be re-run."
            }
            
            # Check 3: Orphaned user_profiles (profile exists but user does not)
            cursor.execute("SELECT COUNT(*) FROM user_profiles up LEFT JOIN users u ON up.user_id = u.id WHERE u.id IS NULL;")
            orphaned_profiles_count = cursor.fetchone()[0]
            results['orphaned_user_profiles'] = {
                'count': orphaned_profiles_count,
                'status': 'ERROR' if orphaned_profiles_count > 0 else 'OK',
                'message': f"Found {orphaned_profiles_count} orphaned user profiles."
            }
            
            # Check 4a: Orphaned tracked_jobs (referencing non-existent users)
            cursor.execute("SELECT COUNT(*) FROM tracked_jobs tj LEFT JOIN users u ON tj.user_id = u.id WHERE u.id IS NULL;")
            orphaned_tracked_by_user = cursor.fetchone()[0]
            results['orphaned_tracked_jobs_by_user'] = {
                'count': orphaned_tracked_by_user,
                'status': 'ERROR' if orphaned_tracked_by_user > 0 else 'OK',
                'message': f"Found {orphaned_tracked_by_user} tracked jobs referencing non-existent users."
            }
            
            # Check 4b: Orphaned tracked_jobs (referencing non-existent jobs)
            cursor.execute("SELECT COUNT(*) FROM tracked_jobs tj LEFT JOIN jobs j ON tj.job_id = j.id WHERE j.id IS NULL;")
            orphaned_tracked_by_job = cursor.fetchone()[0]
            results['orphaned_tracked_jobs_by_job'] = {
                'count': orphaned_tracked_by_job,
                'status': 'ERROR' if orphaned_tracked_by_job > 0 else 'OK',
                'message': f"Found {orphaned_tracked_by_job} tracked jobs referencing non-existent jobs."
            }

    except Exception as e:
        results['overall_error'] = str(e)
        results['overall_status'] = 'FAILED'
    finally:
        if conn:
            conn.close()
    return results

# --- Flask CLI Command (for future use with paid plan/local execution) ---
@click.group('db')
def db_cli():
    """Database management commands."""
    pass

@db_cli.command('check-integrity')
@with_appcontext
def check_integrity_cli():
    """Runs a series of non-destructive data integrity checks (CLI version)."""
    click.echo("--- Starting Data Integrity Pass ---")
    results = run_integrity_checks_internal()
    for key, value in results.items():
        if isinstance(value, dict) and 'status' in value:
            color = 'green'
            if value['status'] == 'WARNING': color = 'yellow'
            elif value['status'] == 'ERROR': color = 'red'
            elif value['status'] == 'INFO': color = 'cyan'
            click.secho(f"[{value['status']}] {value['message']}", fg=color)
        elif key == 'overall_error':
            click.secho(f"An overall error occurred: {value}", fg='red')
    click.echo("--- Data Integrity Pass Complete ---")

def register_cli_commands(app):
    """Registers the CLI commands with the Flask app."""
    app.cli.add_command(db_cli)