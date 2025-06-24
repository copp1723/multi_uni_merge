"""
Entry point for the Swarm Multi-Agent System Flask application.
This file ensures compatibility with deployment platforms like Render.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app factory
from backend.main import create_app

# Create the application instance
logger.info("Creating Flask application...")
app = create_app()

# Import SocketIO after app creation to avoid circular imports
try:
    from backend.main import swarm_app
    socketio = swarm_app.socketio if hasattr(swarm_app, 'socketio') else None
except Exception as e:
    logger.warning(f"Could not import socketio: {e}")
    socketio = None

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
