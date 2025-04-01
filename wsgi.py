import os
import sys

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from web_search_interface import app, ensure_template_exists
    
    # Ensure template directory exists
    ensure_template_exists()
    
    # Explicitly set debug to False for production
    app.debug = False
    
    # Print some debug information
    print("WSGI application initialized successfully")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir('.')}")
    
except Exception as e:
    print(f"Error initializing application: {str(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    # Create a simple fallback app for debugging
    from flask import Flask
    app = Flask(__name__)
    
    @app.route('/')
    def error_page():
        return f"<h1>Error initializing application</h1><pre>{str(e)}</pre>"

# This is the application variable that Gunicorn looks for
application = app 