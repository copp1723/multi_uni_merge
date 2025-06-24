"""
Emergency fix for static file serving - Simple and reliable approach
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch eventlet first
import eventlet
eventlet.monkey_patch()

# Now import Flask and other modules
from flask import Flask, send_from_directory, send_file
from backend.main import swarm_app

# Get the existing app but override the routes
app = swarm_app.app
socketio = swarm_app.socketio

# Clear any existing static folder config
app.static_folder = None
app.static_url_path = None

# Define the frontend dist path
FRONTEND_DIST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend", "dist")
logger.info(f"Frontend dist path: {FRONTEND_DIST}")
logger.info(f"Frontend dist exists: {os.path.exists(FRONTEND_DIST)}")

# Override the root route
@app.route('/', methods=['GET'])
def index():
    """Serve index.html"""
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    else:
        return f"index.html not found at {index_path}", 404

# Override the assets route
@app.route('/assets/<path:filename>', methods=['GET'])
def assets(filename):
    """Serve assets"""
    assets_path = os.path.join(FRONTEND_DIST, 'assets')
    logger.info(f"Serving asset: {filename} from {assets_path}")
    try:
        return send_from_directory(assets_path, filename)
    except Exception as e:
        logger.error(f"Failed to serve asset {filename}: {e}")
        return f"Asset not found: {filename}", 404

# Catch-all for React Router (must be last)
@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    """Serve index.html for all other routes (React Router)"""
    # Don't catch API routes
    if path.startswith('api/'):
        return "Not found", 404
    
    # Try to serve the file if it exists
    file_path = os.path.join(FRONTEND_DIST, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)
    
    # Otherwise serve index.html
    index_path = os.path.join(FRONTEND_DIST, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    else:
        return "Frontend not found", 404

# Expose the socketio app for gunicorn
application = socketio

logger.info("✅ App ready with static file serving fixes")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)