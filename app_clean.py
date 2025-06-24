"""
Single entry point - Simple, clean, working
No complex factories, no multiple files, just what we need
"""
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 1. EVENTLET FIRST - Always
import eventlet
eventlet.monkey_patch()

# 2. Basic imports
from flask import Flask, jsonify, send_file, send_from_directory, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import requests

# 3. Create Flask app - SIMPLE
app = Flask(__name__)
CORS(app, origins="*")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')

# 4. Create SocketIO - SIMPLE
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 5. Frontend path
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

# 6. Static routes - EXPLICIT AND SIMPLE
@app.route('/')
def index():
    """Serve index.html"""
    return send_file(str(FRONTEND_DIST / 'index.html'))

@app.route('/assets/<path:filename>')
def assets(filename):
    """Serve assets"""
    return send_file(str(FRONTEND_ASSETS / filename))

@app.route('/<path:path>')
def catch_all(path):
    """Everything else goes to index.html for React Router"""
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    return send_file(str(FRONTEND_DIST / 'index.html'))

# 7. API Routes - Just the essentials
@app.route('/api/health')
def health():
    return jsonify({
        "status": "healthy",
        "services": {
            "websocket": "ready",
            "frontend": FRONTEND_DIST.exists()
        }
    })

@app.route('/api/agents')
def get_agents():
    """Simple agent list"""
    return jsonify({
        "data": [
            {"id": "communications", "name": "Communications Agent", "status": "ready"},
            {"id": "coder", "name": "Code Assistant", "status": "ready"},
            {"id": "creative", "name": "Creative Agent", "status": "ready"},
            {"id": "data", "name": "Data Analyst", "status": "ready"},
            {"id": "research", "name": "Research Agent", "status": "ready"},
            {"id": "personal", "name": "Personal Assistant", "status": "ready"}
        ],
        "status": "success"
    })

@app.route('/api/models')
def get_models():
    """Get AI models from OpenRouter"""
    try:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            return jsonify({"data": [], "status": "error", "message": "No API key"})
        
        response = requests.get(
            'https://openrouter.ai/api/v1/models',
            headers={'Authorization': f'Bearer {api_key}'}
        )
        
        if response.status_code == 200:
            models = response.json().get('data', [])
            # Simplify the response
            simple_models = [
                {
                    "id": m["id"],
                    "name": m.get("name", m["id"]),
                    "context_length": m.get("context_length", 4096),
                    "pricing": m.get("pricing", {})
                }
                for m in models[:50]  # Limit to 50 models
            ]
            return jsonify({"data": simple_models, "status": "success"})
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
    
    # Fallback models
    return jsonify({
        "data": [
            {"id": "openai/gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "context_length": 4096},
            {"id": "openai/gpt-4", "name": "GPT-4", "context_length": 8192},
            {"id": "anthropic/claude-2", "name": "Claude 2", "context_length": 100000}
        ],
        "status": "success"
    })

@app.route('/api/transform', methods=['POST'])
def transform():
    """Simple text transformation"""
    data = request.get_json()
    text = data.get('text', '')
    agent_id = data.get('agent_id', 'communications')
    
    # For now, just echo back with a simple transformation
    transformed = f"[Processed by {agent_id}]: {text}"
    
    return jsonify({
        "data": {
            "original_text": text,
            "transformed_text": transformed,
            "agent_id": agent_id
        },
        "status": "success"
    })

# 8. WebSocket events - SIMPLE
@socketio.on('connect', namespace='/swarm')
def handle_connect():
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'sid': request.sid})

@socketio.on('disconnect', namespace='/swarm')
def handle_disconnect():
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('user_message', namespace='/swarm')
def handle_message(data):
    logger.info(f"Message from {request.sid}: {data}")
    # Simple echo for now
    emit('message_response', {
        'message': f"Echo: {data.get('message', '')}",
        'agent': data.get('agent_id', 'system'),
        'conversation_id': data.get('conversation_id', 'default')
    })

# 9. Debug endpoint
@app.route('/api/debug/static')
def debug_static():
    return jsonify({
        "frontend_dist": str(FRONTEND_DIST),
        "exists": FRONTEND_DIST.exists(),
        "assets_exist": FRONTEND_ASSETS.exists(),
        "files": [str(f) for f in FRONTEND_ASSETS.glob('*')] if FRONTEND_ASSETS.exists() else []
    })

# 10. Export for gunicorn
application = socketio  # This is what gunicorn needs for eventlet

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=True)