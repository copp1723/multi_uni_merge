"""
WSGI entry point for gunicorn with proper SocketIO support
"""
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Patch eventlet first - MUST be done before any other imports
import eventlet
eventlet.monkey_patch()

# Now import the app
from backend.main import create_app, swarm_app

# Create the Flask app
logger.info("Creating Flask app for WSGI...")
app = create_app()

# Get the SocketIO instance
socketio = swarm_app.socketio if hasattr(swarm_app, 'socketio') else None

if socketio:
    logger.info("✅ SocketIO instance found - WebSocket support enabled")
    # For gunicorn, we need to expose the SocketIO app, not the Flask app
    application = socketio
else:
    logger.error("❌ SocketIO instance not found - WebSocket will not work")
    application = app

# Also expose app and socketio at module level for debugging
__all__ = ['application', 'app', 'socketio']