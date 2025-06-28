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

@click.group('db')
def db_cli():
    """Database management commands."""
    pass

@db_cli.command('check-integrity')
@with_appcontext
def check_integrity():
    """Runs a series of non-destructive data integrity checks."""
    click.echo("--- Starting Data Integrity Pass ---")
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
            if missing_analyses_count > 0:
                click.secho(f"[WARNING] Found {missing_analyses_count} tracked jobs missing a user-specific analysis.", fg='yellow')
            else:
                click.secho("[OK] All tracked jobs have a corresponding analysis entry placeholder (or actual analysis).", fg='green')

            # Check 2: Analyses created with a legacy protocol version
            cursor.execute("SELECT COUNT(*) FROM job_analyses WHERE analysis_protocol_version = '1.0';")
            legacy_analyses_count = cursor.fetchone()[0]
            if legacy_analyses_count > 0:
                click.secho(f"[INFO] Found {legacy_analyses_count} legacy (v1.0) analyses that could be re-run.", fg='cyan')
            else:
                click.secho("[OK] No legacy analyses found.", fg='green')
            
            # Check 3: Orphaned user_profiles (profile exists but user does not)
            cursor.execute("SELECT COUNT(*) FROM user_profiles up LEFT JOIN users u ON up.user_id = u.id WHERE u.id IS NULL;")
            orphaned_profiles_count = cursor.fetchone()[0]
            if orphaned_profiles_count > 0:
                click.secho(f"[ERROR] Found {orphaned_profiles_count} orphaned user profiles.", fg='red')
            else:
                click.secho("[OK] No orphaned user profiles found.", fg='green')
            
            # Check 4: Orphaned tracked_jobs (referencing non-existent users or jobs)
            cursor.execute("SELECT COUNT(*) FROM tracked_jobs tj LEFT JOIN users u ON tj.user_id = u.id WHERE u.id IS NULL;")
            orphaned_tracked_by_user = cursor.fetchone()[0]
            if orphaned_tracked_by_user > 0:
                click.secho(f"[ERROR] Found {orphaned_tracked_by_user} tracked jobs referencing non-existent users.", fg='red')
            else:
                click.secho("[OK] All tracked jobs are linked to existing users.", fg='green')
            
            cursor.execute("SELECT COUNT(*) FROM tracked_jobs tj LEFT JOIN jobs j ON tj.job_id = j.id WHERE j.id IS NULL;")
            orphaned_tracked_by_job = cursor.fetchone()[0]
            if orphaned_tracked_by_job > 0:
                click.secho(f"[ERROR] Found {orphaned_tracked_by_job} tracked jobs referencing non-existent jobs.", fg='red')
            else:
                click.secho("[OK] All tracked jobs are linked to existing jobs.", fg='green')

    except Exception as e:
        click.secho(f"An error occurred: {e}", fg='red')
    finally:
        if conn:
            conn.close()
    click.echo("--- Data Integrity Pass Complete ---")

def register_cli_commands(app):
    """Registers the CLI commands with the Flask app."""
    app.cli.add_command(db_cli)