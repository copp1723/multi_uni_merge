"""
WebSocket-enabled Flask application with real-time communication
Combines REST API endpoints with Socket.IO support
"""

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import eventlet
import os
import logging
from datetime import datetime, timezone

# Patch eventlet for WebSocket support
eventlet.monkey_patch()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services
from backend.services.openrouter_service import get_openrouter_service
from backend.services.mcp_filesystem import get_mcp_filesystem_service
from backend.services.supermemory_service import get_supermemory_service
from backend.services.websocket_service import WebSocketService
from backend.services.agent_service import AgentOrchestrator

# Import orchestrator
from backend.swarm_orchestrator import SwarmOrchestrator

# Import utilities
from backend.utils.error_handler import SwarmError, handle_errors
from backend.utils.service_utils import format_api_response

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize CORS
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Initialize orchestrator
orchestrator = SwarmOrchestrator()

# Initialize services
logger.info("Initializing services...")

# Get service instances
openrouter = get_openrouter_service()
mcp_fs = get_mcp_filesystem_service()
supermemory = get_supermemory_service()

# Initialize AgentOrchestrator
orchestrator = AgentOrchestrator(openrouter, supermemory)

# Initialize WebSocket service with socketio instance
websocket_service = None
if socketio:
    try:
        websocket_service = WebSocketService(socketio, openrouter, supermemory)
        logger.info("WebSocket service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize WebSocket service: {e}")

# ============= REST API Routes =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check endpoint"""
    try:
        # Simple health check for services
        health_data = {
            "mcp_filesystem": "not_configured",
            "supermemory": "not_configured",
            "openrouter": "not_configured",
            "websocket": "not_configured",
            "version": "3.0.0"
        }
        
        # Check if MCP filesystem service is available
        if mcp_fs:
            health_data["mcp_filesystem"] = "healthy"
        
        # Check if Supermemory service is available
        if supermemory:
            health_data["supermemory"] = "healthy"
        
        # Check if OpenRouter service is available
        if openrouter:
            health_data["openrouter"] = "healthy"
        
        # Check if WebSocket service is available
        if websocket_service:
            health_data["websocket"] = "healthy"
        
        return jsonify({
            "status": "success",
            "data": health_data
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Retrieve available AI models from OpenRouter"""
    try:
        if not openrouter:
            return jsonify({
                "status": "error",
                "message": "OpenRouter service not initialized"
            }), 500

        models = openrouter.get_available_models()
        return jsonify({
            "status": "success",
            "data": models
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/transform', methods=['POST'])
def transform_text():
    """Transform text using specified agent"""
    try:
        data = request.get_json() or {}
        text = data.get("text", "").strip()
        agent_id = data.get("agent_id", "communication_agent")
        model = data.get("model", "openai/gpt-4o")
        
        if not text:
            return jsonify({
                "status": "error",
                "message": "No text provided for transformation"
            }), 400
        
        if not openrouter:
            return jsonify({
                "status": "error",
                "message": "OpenRouter service not initialized"
            }), 500
        
        # Use openrouter to transform the text
        response = openrouter.transform_text(text, agent_id, model)
        
        # Save interaction to supermemory
        if supermemory:
            supermemory.save_interaction(agent_id, text, response)
        
        return jsonify({
            "status": "success",
            "data": {
                "transformed_text": response,
                "agent_id": agent_id,
                "model_used": model
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get available agents"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 500

        agents = orchestrator.get_available_agents()
        return jsonify(format_api_response(agents))
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/agents/<agent_id>/config', methods=['GET'])
def get_agent_config(agent_id: str):
    """Get agent configuration"""
    try:
        if not orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not initialized"
            }), 500

        config = orchestrator.get_agent_config(agent_id)
        if not config:
            return jsonify({
                "status": "error",
                "message": f"Agent {agent_id} not found"
            }), 404

        return jsonify(format_api_response(config))
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# ============= WebSocket Event Handlers =============

@socketio.on('connect', namespace='/swarm')
def handle_connect():
    """Handle client connection"""
    logger.info(f'Client connected: {request.sid}')
    emit('connection_status', {'status': 'connected', 'session_id': request.sid})

@socketio.on('disconnect', namespace='/swarm')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f'Client disconnected: {request.sid}')

# REPLACE the existing 'send_message' handler with this one
@socketio.on('send_message', namespace='/swarm')
def handle_message(data):
    try:
        message = data.get('content')
        agent_ids = data.get('agent_ids', [])
        model = data.get('model', 'openai/gpt-4o')  # Added default model
        
        # If agent_ids are not explicitly provided by the frontend, parse the message for @mentions
        if not agent_ids:
            agent_ids = orchestrator.parse_mentions(message)
            
        # If still no agents, fall back to the recipient_id (for single-agent chats)
        if not agent_ids and data.get('recipient_id'):
            agent_ids = [data.get('recipient_id')]

        # If no target agent can be determined, send an error back to the client
        if not agent_ids:
            emit('response_stream_error', {'error': 'No valid agent specified.'})
            return

        # Route the message to all identified agents via the orchestrator
        for agent_id in agent_ids:
            orchestrator.route_message_to_agent(
                agent_id, message, model, request.sid
            )
            
    except Exception as e:
        print(f"Error in handle_message: {str(e)}") # Added for better debugging
        emit('response_stream_error', {'error': str(e)})

@socketio.on('swarm_message', namespace='/swarm')
def handle_swarm_message(data):
    """Handle swarm-specific messages"""
    try:
        logger.info(f"Received swarm message from {request.sid}: {data}")
        
        message = data.get('message', '')
        agent_ids = data.get('agent_ids', [])
        model = data.get('model', 'openai/gpt-4o')
        
        if not message:
            emit('error', {'message': 'No message content provided'})
            return
        
        # Emit acknowledgment
        emit('message_received', {
            'status': 'processing',
            'message': message,
            'agents': agent_ids
        })
        
        # For now, echo the message back with a simulated response
        # This will be replaced with actual agent processing
        response_data = {
            'responses': [{
                'agent_id': agent_id,
                'agent_name': f'Agent {agent_id}',
                'content': f'Echo from {agent_id}: {message}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            } for agent_id in agent_ids] if agent_ids else [{
                'agent_id': 'system',
                'agent_name': 'System',
                'content': f'Echo: {message}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            }]
        }
        
        emit('swarm_responses', response_data)
        
    except Exception as e:
        logger.error(f"Error handling swarm message: {e}")
        emit('error', {'error': str(e)})

@socketio.on('join_room', namespace='/swarm')
def handle_join_room(data):
    """Handle room joining for multi-user collaboration"""
    room = data.get('room')
    if room:
        join_room(room)
        logger.info(f"Client {request.sid} joined room {room}")
        emit('room_joined', {'room': room, 'status': 'success'})

@socketio.on('leave_room', namespace='/swarm')
def handle_leave_room(data):
    """Handle room leaving"""
    room = data.get('room')
    if room:
        leave_room(room)
        logger.info(f"Client {request.sid} left room {room}")
        emit('room_left', {'room': room, 'status': 'success'})

# ============= Main Entry Point =============

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting WebSocket server on port {port}")
    logger.info(f"Debug mode: {debug}")
    logger.info(f"Services initialized: OpenRouter={openrouter is not None}, "
                f"MCP={mcp_fs is not None}, Supermemory={supermemory is not None}, "
                f"WebSocket={websocket_service is not None}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug)