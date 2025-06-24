#!/usr/bin/env python3
"""
Production startup script with debugging
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

# Debug startup
logger.info("=" * 60)
logger.info("🚀 STARTING SWARM MULTI-AGENT SYSTEM")
logger.info("=" * 60)

# Environment info
logger.info(f"📂 Current Directory: {os.getcwd()}")
logger.info(f"🐍 Python Version: {sys.version}")
logger.info(f"🔧 Environment: {os.getenv('FLASK_ENV', 'development')}")
logger.info(f"🌐 Port: {os.getenv('PORT', '5000')}")

# Check for frontend
frontend_paths = [
    "frontend/dist",
    "dist",
    "/opt/render/project/src/frontend/dist"
]

for path in frontend_paths:
    if os.path.exists(path):
        logger.info(f"✅ Found frontend at: {path}")
        if os.path.exists(os.path.join(path, "index.html")):
            logger.info(f"   ✅ index.html exists")
        if os.path.exists(os.path.join(path, "assets")):
            logger.info(f"   ✅ assets directory exists")
            assets = os.listdir(os.path.join(path, "assets"))
            logger.info(f"   📦 Assets: {assets[:3]}...")  # First 3 files
        break
else:
    logger.warning("❌ No frontend dist directory found!")

# Check API keys
api_keys = {
    "OPENROUTER_API_KEY": "OpenRouter",
    "SUPERMEMORY_API_KEY": "Supermemory",
    "DATABASE_URL": "Database",
    "SECRET_KEY": "Secret Key"
}

logger.info("\n🔑 API Configuration:")
for key, name in api_keys.items():
    configured = "✅" if os.getenv(key) else "❌"
    logger.info(f"   {configured} {name}")

# Import and run app
logger.info("\n🏃 Starting Flask application...")
try:
    from app import app, socketio
    
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    
    logger.info(f"🌐 Server starting on {host}:{port}")
    
    if socketio:
        logger.info("✅ Using SocketIO for WebSocket support")
        socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)
    else:
        logger.info("⚠️ Running without SocketIO")
        app.run(host=host, port=port)
        
except Exception as e:
    logger.error(f"❌ Failed to start: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
