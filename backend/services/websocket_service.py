"""
WebSocket Service for Real-Time Agent Coordination with Enhanced MCP Integration
Provides real-time communication between agents and users
"""

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import current_app, request
from flask_socketio import Namespace, emit, join_room, leave_room

# Import BaseService for proper service registration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.service_utils import BaseService, ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)

class AgentStatus(Enum):
    """Agent status enumeration"""
    IDLE = "idle"
    THINKING = "thinking"
    PROCESSING = "processing"
    RESPONDING = "responding"
    ERROR = "error"

class WebSocketMessage:
    """WebSocket message structure"""
    def __init__(self, message_id: str, message_type: str, content: str,
                 sender_id: str, recipient_id: str = None, room_id: str = None,
                 metadata: Dict[str, Any] = None):
        self.message_id = message_id
        self.message_type = message_type
        self.content = content
        self.sender_id = sender_id
        self.recipient_id = recipient_id
        self.room_id = room_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)

class WebSocketService(BaseService):
    """Enhanced WebSocket service with proper MCP filesystem integration"""

    def __init__(self, app, mcp_filesystem_service=None, orchestrator=None):
        super().__init__("websocket")  # Initialize BaseService with service name
        self.app = app
        self.mcp_filesystem_service = mcp_filesystem_service
        self.orchestrator = orchestrator
        self.connected_clients = {}
        self.agent_states = {}
        self.active_rooms = {}
        self.streaming_sessions = {}
        
        # Verify MCP filesystem service
        if self.mcp_filesystem_service:
            try:
                workspace_info = self.mcp_filesystem_service.get_workspace_info()
                if workspace_info.get("status") == "healthy":
                    logger.info("✅ MCP Filesystem service connected and healthy")
                else:
                    logger.error("❌ MCP Filesystem service unhealthy")
            except Exception as e:
                logger.error(f"❌ MCP Filesystem service error: {e}")
        else:
            logger.warning("⚠️ MCP Filesystem service not provided")
    
    async def _health_check(self) -> ServiceHealth:
        """Implement service-specific health check"""
        try:
            return ServiceHealth(
                status=ServiceStatus.HEALTHY,
                message="WebSocket service operational",
                details={
                    "connected_clients": len(self.connected_clients),
                    "active_rooms": len(self.active_rooms),
                    "mcp_filesystem": "connected" if self.mcp_filesystem_service else "not_connected"
                },
                last_check=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                message=f"WebSocket service error: {str(e)}",
                details={"error": str(e)},
                last_check=datetime.now(timezone.utc).isoformat()
            )
    
    def start_streaming_response(self, session_id: str, message: WebSocketMessage, model: str):
        """Start streaming response from agent with proper Flask context"""
        try:
            session = self.streaming_sessions.get(session_id)
            if not session or not session["active"]:
                return
            
            client_id = session["client_id"]
            agent_id = session["agent_id"]
            
            # Emit stream start
            emit(
                "response_stream_start",
                {
                    "session_id": session_id,
                    "agent_id": agent_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                room=client_id,
            )
            
            # CRITICAL FIX: Use Flask app context for threading
            with self.app.app_context():
                # Import here to avoid circular imports
                from ..services.openrouter_service import get_openrouter_service
                from ..services.agent_service import get_agent_service
                from ..services.supermemory_service import get_supermemory_service
                
                # Get services with proper error handling
                try:
                    openrouter_service = get_openrouter_service()
                    supermemory_service = get_supermemory_service()
                    agent_service = get_agent_service()
                    
                    # CRITICAL_FIX: Ensure MCP filesystem service is passed correctly
                    if not self.mcp_filesystem_service:
                        logger.error("❌ MCP Filesystem service not available for agent")
                        # Try to get from app context as fallback
                        self.mcp_filesystem_service = getattr(current_app, 'mcp_filesystem_service', None)
                    
                    # Create agent service with MCP filesystem
                    if agent_service and self.mcp_filesystem_service:
                        agent_service.set_mcp_filesystem_service(self.mcp_filesystem_service)
                        
                        # Log MCP filesystem status
                        if agent_service.mcp_filesystem:
                            logger.info(f"✅ Agent {agent_id} has MCP filesystem access")
                        else:
                            logger.error(f"❌ Agent {agent_id} missing MCP filesystem access")
                    
                    # Process streaming response
                    if openrouter_service and agent_service:
                        # Get agent configuration
                        agent_config = agent_service.get_agent_config(agent_id)
                        if not agent_config:
                            raise Exception(f"Agent {agent_id} not found")
                        
                        # Prepare messages for the agent
                        messages = [
                            {"role": "system", "content": agent_config["system_prompt"]},
                            {"role": "user", "content": message.content}
                        ]
                        
                        # Add memory context if available
                        if supermemory_service:
                            try:
                                memory_context = supermemory_service.get_cross_agent_context(
                                    message.content, exclude_agent=agent_id
                                )
                                if memory_context:
                                    context_text = supermemory_service.format_memory_context(memory_context)
                                    messages[0]["content"] += f"\n\nRelevant context from previous conversations:\n{context_text}"
                            except Exception as e:
                                logger.warning(f"⚠️ Could not retrieve memory context: {e}")
                        
                        # Stream response
                        full_response = ""
                        for chunk in openrouter_service.chat_completion_stream(
                            messages=messages,
                            model=model,
                            temperature=0.7
                        ):
                            if not session.get("active", False):
                                break
                            
                            full_response += chunk
                            
                            # Emit chunk to client
                            emit(
                                "response_stream_chunk",
                                {
                                    "session_id": session_id,
                                    "agent_id": agent_id,
                                    "chunk": chunk,
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                },
                                room=client_id,
                            )
                        
                        # Store conversation in memory
                        if supermemory_service and full_response:
                            try:
                                supermemory_service.store_conversation(
                                    agent_id=agent_id,
                                    user_message=message.content,
                                    agent_response=full_response,
                                    model_used=model,
                                )
                                if self.orchestrator and os.getenv('NOTIFICATION_EMAIL'):
                                    try:
                                        asyncio.run(
                                            self.orchestrator.send_email(
                                                os.getenv('NOTIFICATION_EMAIL'),
                                                f"Conversation with {agent_id}",
                                                full_response,
                                                agent_id=agent_id,
                                            )
                                        )
                                    except Exception as e:
                                        logger.warning(f"⚠️ Could not send notification email: {e}")
                            except Exception as e:
                                logger.warning(f"⚠️ Could not store conversation: {e}")
                        
                        # Emit stream end
                        emit(
                            "response_stream_end",
                            {
                                "session_id": session_id,
                                "agent_id": agent_id,
                                "full_response": full_response,
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                            room=client_id,
                        )
                        
                except Exception as e:
                    logger.error(f"❌ Error in streaming response: {e}")
                    emit(
                        "response_stream_error",
                        {
                            "session_id": session_id,
                            "agent_id": agent_id,
                            "error": str(e),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                        room=client_id,
                    )
                finally:
                    # Clean up session
                    if session_id in self.streaming_sessions:
                        del self.streaming_sessions[session_id]
                    
                    # Update agent status
                    self.update_agent_status(agent_id, AgentStatus.IDLE)
                    
        except Exception as e:
            logger.error(f"❌ Critical error in streaming response: {e}")
    
    def update_agent_status(self, agent_id: str, status: AgentStatus, metadata: Dict[str, Any] = None):
        """Update agent status and broadcast to connected clients"""
        self.agent_states[agent_id] = {
            "status": status.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        }
        
        # Broadcast status update
        emit(
            "agent_status_update",
            {
                "agent_id": agent_id,
                "status": status.value,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "metadata": metadata or {}
            },
            broadcast=True
        )
    
    def get_connected_clients(self) -> Dict[str, Any]:
        """Get information about connected clients"""
        return {
            "total_clients": len(self.connected_clients),
            "clients": list(self.connected_clients.keys()),
            "active_rooms": list(self.active_rooms.keys()),
            "streaming_sessions": len(self.streaming_sessions)
        }
    
    def get_agent_states(self) -> Dict[str, Any]:
        """Get current states of all agents"""
        return self.agent_states
    
    def broadcast_system_message(self, message: str, message_type: str = "system"):
        """Broadcast system message to all connected clients"""
        emit(
            "system_message",
            {
                "message": message,
                "type": message_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            broadcast=True
        )
    
    def send_file_access_notification(self, client_id: str, operation: str, file_path: str, success: bool):
        """Send file access notification to specific client"""
        emit(
            "file_access_notification",
            {
                "operation": operation,
                "file_path": file_path,
                "success": success,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            room=client_id
        )
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get WebSocket service status"""
        return {
            "status": "healthy",
            "connected_clients": len(self.connected_clients),
            "active_rooms": len(self.active_rooms),
            "streaming_sessions": len(self.streaming_sessions),
            "agent_states": len(self.agent_states),
            "mcp_filesystem_available": bool(self.mcp_filesystem_service)
        }


class SwarmNamespace(Namespace):
    """Enhanced namespace for swarm agent communication"""
    
    def __init__(self, namespace, websocket_service):
        super().__init__(namespace)
        self.websocket_service = websocket_service
    
    def on_connect(self):
        """Handle client connection"""
        client_id = request.sid
        user_id = request.args.get('user_id', 'anonymous')
        
        self.websocket_service.connected_clients[client_id] = {
            "user_id": user_id,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"🔌 Client connected: {client_id} (user: {user_id})")
        
        # Send connection confirmation
        emit('connection_confirmed', {
            "client_id": client_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mcp_filesystem_available": bool(self.websocket_service.mcp_filesystem_service)
        })
    
    def on_disconnect(self):
        """Handle client disconnection"""
        client_id = request.sid
        
        if client_id in self.websocket_service.connected_clients:
            user_info = self.websocket_service.connected_clients[client_id]
            del self.websocket_service.connected_clients[client_id]
            logger.info(f"🔌 Client disconnected: {client_id} (user: {user_info.get('user_id')})")
        
        # Clean up any streaming sessions
        sessions_to_remove = [
            session_id for session_id, session in self.websocket_service.streaming_sessions.items()
            if session.get("client_id") == client_id
        ]
        
        for session_id in sessions_to_remove:
            del self.websocket_service.streaming_sessions[session_id]
    
    def on_agent_message(self, data):
        """Handle agent message from client"""
        try:
            client_id = request.sid
            agent_id = data.get('agent_id')
            message_content = data.get('message')
            model = data.get('model', 'anthropic/claude-3.5-sonnet')
            
            if not agent_id or not message_content:
                emit('error', {"message": "Missing agent_id or message"})
                return
            
            # Update client activity
            if client_id in self.websocket_service.connected_clients:
                self.websocket_service.connected_clients[client_id]["last_activity"] = datetime.now(timezone.utc).isoformat()
            
            # Create message object
            message = WebSocketMessage(
                message_id=str(uuid.uuid4()),
                message_type="user_message",
                content=message_content,
                sender_id=client_id,
                recipient_id=agent_id
            )
            
            # Update agent status
            self.websocket_service.update_agent_status(agent_id, AgentStatus.THINKING)
            
            # Create streaming session
            session_id = str(uuid.uuid4())
            self.websocket_service.streaming_sessions[session_id] = {
                "client_id": client_id,
                "agent_id": agent_id,
                "active": True,
                "started_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Start streaming response in background thread
            thread = threading.Thread(
                target=self.websocket_service.start_streaming_response,
                args=(session_id, message, model)
            )
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            logger.error(f"❌ Error handling agent message: {e}")
            emit('error', {"message": f"Error processing message: {str(e)}"})
    
    def on_stop_stream(self, data):
        """Handle stream stop request"""
        try:
            session_id = data.get('session_id')
            if session_id in self.websocket_service.streaming_sessions:
                self.websocket_service.streaming_sessions[session_id]["active"] = False
                logger.info(f"🛑 Stream stopped: {session_id}")
                emit('stream_stopped', {"session_id": session_id})
        except Exception as e:
            logger.error(f"❌ Error stopping stream: {e}")
    
    def on_join_room(self, data):
        """Handle room join request"""
        try:
            room_id = data.get('room_id')
            if room_id:
                join_room(room_id)
                self.websocket_service.active_rooms[room_id] = self.websocket_service.active_rooms.get(room_id, [])
                if request.sid not in self.websocket_service.active_rooms[room_id]:
                    self.websocket_service.active_rooms[room_id].append(request.sid)
                emit('room_joined', {"room_id": room_id})
        except Exception as e:
            logger.error(f"❌ Error joining room: {e}")
    
    def on_leave_room(self, data):
        """Handle room leave request"""
        try:
            room_id = data.get('room_id')
            if room_id:
                leave_room(room_id)
                if room_id in self.websocket_service.active_rooms:
                    if request.sid in self.websocket_service.active_rooms[room_id]:
                        self.websocket_service.active_rooms[room_id].remove(request.sid)
                    if not self.websocket_service.active_rooms[room_id]:
                        del self.websocket_service.active_rooms[room_id]
                emit('room_left', {"room_id": room_id})
        except Exception as e:
            logger.error(f"❌ Error leaving room: {e}")
    
    def on_get_status(self, data):
        """Handle status request"""
        try:
            status = self.websocket_service.get_service_status()
            emit('status_response', status)
        except Exception as e:
            logger.error(f"❌ Error getting status: {e}")
            emit('error', {"message": f"Error getting status: {str(e)}"})


# Global WebSocket service instance
websocket_service: Optional[WebSocketService] = None

def initialize_websocket_service(app, mcp_filesystem_service=None, orchestrator=None) -> WebSocketService:
    """Initialize WebSocket service"""
    global websocket_service
    websocket_service = WebSocketService(app, mcp_filesystem_service, orchestrator)
    return websocket_service

def get_websocket_service() -> Optional[WebSocketService]:
    """Get the global WebSocket service instance"""
    return websocket_service

