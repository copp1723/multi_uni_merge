"""
WSGI entry point for production deployment
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and create the Flask app
from backend.main import create_app, swarm_app

logger.info("Creating Flask app for WSGI...")
app = create_app()

# For gunicorn, we expose the Flask app directly
# The SocketIO functionality is already integrated within the app
application = app

# Debug: Log static folder configuration
logger.info(f"Flask static_folder: {app.static_folder}")
logger.info(f"Flask static_url_path: {app.static_url_path}")
if app.static_folder:
    logger.info(f"Static folder exists: {os.path.exists(app.static_folder)}")

__all__ = ['application', 'app']