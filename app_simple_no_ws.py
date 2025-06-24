"""
Ultra-simple app - NO WebSockets, just get the UI working
"""
import os
from pathlib import Path
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)
CORS(app, origins="*")

# Frontend paths
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
FRONTEND_ASSETS = FRONTEND_DIST / "assets"

# Static routes
@app.route('/')
def index():
    """Serve index.html"""
    return send_file(str(FRONTEND_DIST / 'index.html'))

@app.route('/assets/<path:filename>')
def assets(filename):
    """Serve assets"""
    return send_file(str(FRONTEND_ASSETS / filename))

# API routes
@app.route('/api/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "message": "Simple app running without WebSockets"
    })

@app.route('/api/agents')
def agents():
    """Get agents"""
    return jsonify({
        "data": [
            {"id": "research", "name": "Research Assistant", "status": "active"},
            {"id": "coding", "name": "Coding Assistant", "status": "active"},
            {"id": "planning", "name": "Planning Assistant", "status": "active"},
            {"id": "writing", "name": "Writing Assistant", "status": "active"},
            {"id": "data", "name": "Data Analyst", "status": "active"},
            {"id": "communications", "name": "Communications", "status": "active"}
        ]
    })

@app.route('/api/models')
def models():
    """Get models"""
    return jsonify({
        "data": [
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            {"id": "gpt-4", "name": "GPT-4"}
        ]
    })

@app.route('/api/transform', methods=['POST'])
def transform():
    """Transform text"""
    data = request.get_json()
    text = data.get('text', '')
    agent_id = data.get('agent_id', 'communications')
    
    return jsonify({
        "data": {
            "original_text": text,
            "transformed_text": f"[{agent_id.upper()}]: {text} (This is a placeholder response)",
            "agent_id": agent_id,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    })

@app.route('/<path:path>')
def catch_all(path):
    """Catch all for React Router"""
    if path.startswith('api/'):
        return jsonify({"error": "Not found"}), 404
    return send_file(str(FRONTEND_DIST / 'index.html'))

# Export for gunicorn
application = app

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)