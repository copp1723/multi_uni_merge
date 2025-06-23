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

# Import the Flask app factory and SocketIO
from backend.main import create_app, swarm_app

# Create the application instance
logger.info("Creating Flask application...")
app = create_app()

# Get the SocketIO instance for deployment platforms that need it
socketio = swarm_app.socketio

if __name__ == '__main__':
    # Use SocketIO run method for proper WebSocket support
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting server on {host}:{port} (debug={debug})")
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
