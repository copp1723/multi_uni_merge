"""
Entry point for the Swarm Multi-Agent System Flask application.
This file ensures compatibility with deployment platforms like Render.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app from backend
from backend.main import create_app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=False)
