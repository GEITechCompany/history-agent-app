import os
import sys
from web_search_interface import app, ensure_template_exists

# Ensure the template directory and template file exist
ensure_template_exists()

# Get the port from environment variable (Render sets this)
port = int(os.environ.get("PORT", 10000))

if __name__ == "__main__":
    print(f"Starting application on port {port}")
    # Run the application with the port from environment variable
    app.run(host="0.0.0.0", port=port, debug=False) 