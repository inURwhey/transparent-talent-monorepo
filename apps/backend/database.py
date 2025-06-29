import psycopg2
from psycopg2.extras import DictCursor
from flask import g
from .config import config

def get_db():
    """
    Opens a new database connection if there is none yet for the
    current application context.
    """
    if 'db' not in g:
        g.db = psycopg2.connect(config.DATABASE_URL, cursor_factory=DictCursor)
    return g.db

def close_db(e=None):
    """
    Closes the database connection at the end of the request.
    This function is intended to be registered with app.teardown_appcontext.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_app(app):
    """
    Register database functions with the Flask app. This is called from
    the application factory.
    """
    app.teardown_appcontext(close_db)