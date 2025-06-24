"""
Entry point for the Swarm Multi-Agent System Flask application.
This file ensures compatibility with deployment platforms like Render.
UPDATED: With proper static file serving fixes
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# CRITICAL: Patch eventlet BEFORE any other imports for WebSocket support
# Temporarily disabled due to Python 3.13 compatibility issues
# import eventlet
# eventlet.monkey_patch()

# Import Flask for static file handling
from flask import send_from_directory, send_file
from werkzeug.exceptions import NotFound

# Import the Flask app factory
from backend.main import create_app

# Create the application instance
logger.info("Creating Flask application with static file fixes...")
app = create_app()

# Get the frontend dist path
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
logger.info(f"Frontend dist path: {FRONTEND_DIST}")
logger.info(f"Frontend dist exists: {FRONTEND_DIST.exists()}")

# Clear Flask's automatic static handling
app.static_folder = None
app.static_url_path = None

# Add explicit route for root
@app.route('/', methods=['GET'])
def serve_index():
    """Serve index.html"""
    try:
        return send_from_directory(str(FRONTEND_DIST), 'index.html')
    except Exception as e:
        logger.error(f"Failed to serve index.html: {e}")
        return f"Frontend not found: {e}", 404

# Add explicit route for assets - CRITICAL FIX
@app.route('/assets/<path:filename>', methods=['GET'])
def serve_assets(filename):
    """Serve asset files with proper content"""
    assets_dir = FRONTEND_DIST / 'assets'
    try:
        # Log for debugging
        logger.info(f"Serving asset: {filename}")
        file_path = assets_dir / filename
        
        if not file_path.exists():
            logger.error(f"Asset file not found: {file_path}")
            return f"Asset not found: {filename}", 404
            
        # Use send_file to ensure content is actually sent
        return send_file(str(file_path))
    except Exception as e:
        logger.error(f"Error serving asset {filename}: {e}")
        return f"Error serving asset: {e}", 500

# Catch-all for React Router
@app.route('/<path:path>', methods=['GET'])
def catch_all(path):
    """Serve index.html for all non-API routes"""
    # Skip API and socket.io routes
    if path.startswith(('api/', 'socket.io')):
        return "Not found", 404
    
    # Try to serve static file if it exists
    file_path = FRONTEND_DIST / path
    if file_path.exists() and file_path.is_file():
        return send_file(str(file_path))
    
    # Otherwise serve index.html for client-side routing
    return send_from_directory(str(FRONTEND_DIST), 'index.html')

# Debug endpoint
@app.route('/api/debug/static', methods=['GET'])
def debug_static():
    """Debug static files configuration"""
    assets_dir = FRONTEND_DIST / 'assets'
    
    debug_info = {
        "frontend_dist": str(FRONTEND_DIST),
        "exists": FRONTEND_DIST.exists(),
        "index_exists": (FRONTEND_DIST / 'index.html').exists(),
        "assets_exists": assets_dir.exists(),
        "assets_files": [],
        "cwd": os.getcwd(),
        "app_location": __file__
    }
    
    if assets_dir.exists():
        debug_info["assets_files"] = [f.name for f in assets_dir.iterdir() if f.is_file()]
    
    return debug_info

# Import SocketIO after app creation to avoid circular imports
try:
    from backend.main import swarm_app
    socketio = swarm_app.socketio if hasattr(swarm_app, 'socketio') else None
    if socketio:
        logger.info("SocketIO instance available for WebSocket support")
        # For eventlet, expose the socketio-wrapped app
        application = socketio
    else:
        logger.warning("SocketIO not available")
        application = app
except Exception as e:
    logger.error(f"Could not import socketio: {e}")
    socketio = None
    application = app

# Expose both for compatibility
__all__ = ['app', 'application', 'socketio']

if __name__ == '__main__':
    # Use SocketIO run method for proper WebSocket support
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting server on {host}:{port} (debug={debug})")
    if socketio:
        socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    else:
        app.run(host=host, port=port, debug=debug)
