# apps/backend/run.py
import sys
import os

# Add the parent directory (monorepo root) to the Python path
# This allows imports like 'apps.backend.app' to work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import your create_app function from the actual location
from apps.backend.app import create_app

# Create the app instance for Flask CLI to discover
app = create_app()

# This part is for running the app directly if you ever need to
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)