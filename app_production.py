"""
Production-ready Flask application with proper static file serving
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

# Import Flask
from flask import Flask, send_from_directory, request
from werkzeug.exceptions import NotFound

# Import the backend modules
from backend.main import create_app as backend_create_app, swarm_app

# Patch eventlet BEFORE creating the app
import eventlet
eventlet.monkey_patch()

def create_production_app():
    """Create Flask app with proper static file serving"""
    # Get the base app from backend
    app = backend_create_app()
    
    # Get absolute paths
    base_dir = Path(__file__).parent.absolute()
    frontend_dist = base_dir / "frontend" / "dist"
    
    logger.info(f"Base directory: {base_dir}")
    logger.info(f"Frontend dist: {frontend_dist}")
    logger.info(f"Frontend dist exists: {frontend_dist.exists()}")
    
    # Override all static handling with explicit routes
    app.static_folder = None  # Disable automatic static handling
    
    @app.route('/', methods=['GET'])
    def serve_index():
        """Serve the main index.html"""
        try:
            return send_from_directory(str(frontend_dist), 'index.html')
        except NotFound:
            logger.error(f"index.html not found in {frontend_dist}")
            return "Frontend not found. Please check if the frontend is built.", 404
    
    @app.route('/assets/<path:filename>', methods=['GET'])
    def serve_asset(filename):
        """Serve asset files (JS, CSS, etc.)"""
        try:
            assets_dir = frontend_dist / 'assets'
            logger.debug(f"Serving asset: {filename} from {assets_dir}")
            return send_from_directory(str(assets_dir), filename)
        except NotFound:
            logger.error(f"Asset not found: {filename}")
            return f"Asset not found: {filename}", 404
    
    @app.route('/<path:path>', methods=['GET'])
    def serve_spa(path):
        """Catch-all route for SPA"""
        # Skip API routes
        if path.startswith('api/') or path.startswith('socket.io'):
            return "Not found", 404
        
        # Try to serve the file if it exists
        file_path = frontend_dist / path
        if file_path.exists() and file_path.is_file():
            return send_from_directory(str(frontend_dist), path)
        
        # Otherwise serve index.html for client-side routing
        return send_from_directory(str(frontend_dist), 'index.html')
    
    # Add a debug route to check static files
    @app.route('/api/debug/static', methods=['GET'])
    def debug_static():
        """Debug endpoint to check static file setup"""
        assets_dir = frontend_dist / 'assets'
        return {
            "frontend_dist": str(frontend_dist),
            "exists": frontend_dist.exists(),
            "index_exists": (frontend_dist / 'index.html').exists(),
            "assets_exists": assets_dir.exists(),
            "assets_files": list(map(str, assets_dir.glob('*'))) if assets_dir.exists() else []
        }
    
    return app

# Create the app
logger.info("Creating production Flask application...")
app = create_production_app()

# Get SocketIO instance
socketio = swarm_app.socketio if hasattr(swarm_app, 'socketio') else None

if socketio:
    logger.info("✅ SocketIO instance found - WebSocket support enabled")
    # IMPORTANT: When using eventlet, we expose the app wrapped by socketio
    application = socketio
else:
    logger.warning("⚠️ SocketIO not found - WebSocket will not work")
    application = app

# For debugging
if __name__ == '__main__':
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    if socketio:
        socketio.run(app, host=host, port=port, debug=True)
    else:
        app.run(host=host, port=port, debug=True)