"""
WebSocket Service for Real-Time Agent Coordination with Enhanced MCP Integration
Provides real-time communication between agents and users
"""

import json
import logging
import threading # Keep for existing sync streaming, or refactor to full async with socketio.start_background_task
import uuid
import asyncio # For new async swarm message handling
import os # For environment variables
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from flask import current_app, request
from flask_socketio import Namespace, emit, join_room, leave_room, SocketIO

# Import BaseService for proper service registration
# Ensure this path is correct for your project structure
import sys
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Check if this is needed

from utils.service_utils import BaseService, ServiceHealth, ServiceStatus
from utils.error_handler import SwarmError # Assuming SwarmError is in utils
# Import orchestrator getter
from backend.swarm_orchestrator import get_orchestrator, SwarmOrchestrator


logger = logging.getLogger(__name__)

DEFAULT_AGENT_MODEL = os.getenv("DEFAULT_AGENT_MODEL", "anthropic/claude-3.5-sonnet")

class AgentStatus(Enum):
    """Agent status enumeration"""

    IDLE = "idle"
    THINKING = "thinking"
    PROCESSING = "processing"
    RESPONDING = "responding"
    ERROR = "error"


class WebSocketMessage:
    """WebSocket message structure"""

    def __init__(
        self,
        message_id: str,
        message_type: str,
        content: str,
        sender_id: str,
        recipient_id: str = None, # Can be a single agent ID or 'swarm'
        room_id: str = None, # Typically client_id for direct messages
        metadata: Dict[str, Any] = None,
    ):
        self.message_id = message_id
        self.message_type = message_type
        self.content = content
        self.sender_id = sender_id # User/client ID
        self.recipient_id = recipient_id
        self.room_id = room_id
        self.metadata = metadata or {}
        self.timestamp = datetime.now(timezone.utc)


class WebSocketService(BaseService):
    """Enhanced WebSocket service with proper MCP filesystem integration"""

    def __init__(self, app, mcp_filesystem_service=None, orchestrator_instance: Optional[SwarmOrchestrator]=None):
        super().__init__("websocket")  # Initialize BaseService with service name
        self.app = app
        self.mcp_filesystem_service = mcp_filesystem_service
        # If orchestrator_instance is not provided, get it using the global getter
        self.orchestrator = orchestrator_instance if orchestrator_instance is not None else get_orchestrator()
        self.connected_clients = {} # client_sid -> user_info
        self.agent_states = {} # agent_id -> state_info
        self.active_rooms = {} # room_id -> list_of_client_sids
        self.streaming_sessions = {} # session_id -> session_info (for single agent streaming)

        # Verify MCP filesystem service
        if self.mcp_filesystem_service:
            try:
                # Assuming get_workspace_info returns a dict with a 'status' key
                workspace_info = self.mcp_filesystem_service.get_workspace_info()
                if workspace_info.get("status") == "healthy": # Example check
                    logger.info("✅ MCP Filesystem service connected and healthy")
                else:
                    logger.error(f"❌ MCP Filesystem service unhealthy: {workspace_info.get('status')}")
            except Exception as e:
                logger.error(f"❌ Error verifying MCP Filesystem service: {e}")
        else:
            logger.warning("⚠️ MCP Filesystem service not provided to WebSocketService")

    async def _health_check(self) -> ServiceHealth: # Keep async if BaseService expects it
        """Implement service-specific health check"""
        # This can remain mostly synchronous in its checks unless there's an async check needed
        try:
            details = {
                "connected_clients": len(self.connected_clients),
                "active_rooms": len(self.active_rooms),
                "streaming_sessions": len(self.streaming_sessions),
                "mcp_filesystem": "connected" if self.mcp_filesystem_service else "not_connected",
                "orchestrator_available": "yes" if self.orchestrator else "no"
            }
            # Example: Check orchestrator health if it has a health check method
            if self.orchestrator and hasattr(self.orchestrator, 'is_healthy'): # Fictional health check
                 details["orchestrator_healthy"] = await self.orchestrator.is_healthy() # if orchestrator has async health check

            return ServiceHealth(
                status=ServiceStatus.HEALTHY,
                message="WebSocket service operational",
                details=details,
                last_check=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as e:
            logger.error(f"WebSocket service health check failed: {e}")
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY,
                message=f"WebSocket service error: {str(e)}",
                details={"error": str(e)},
                last_check=datetime.now(timezone.utc).isoformat(),
            )

    def _emit_error_to_client(self, client_id: str, session_id: Optional[str], agent_id: Optional[str], error_message: str, event_name: str = "response_stream_error"):
        """Helper to emit structured errors to the client."""
        payload = {
            "error": error_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if session_id:
            payload["session_id"] = session_id
        if agent_id:
            payload["agent_id"] = agent_id

        # Ensure emit is called within a Flask-SocketIO context if needed,
        # or that the SocketIO instance is correctly configured for emitting from threads/async tasks.
        # If this is called from a thread started by Flask-SocketIO, it should be fine.
        # If called from a self-managed thread, may need self.app.socketio.emit(...)
        socketio_instance = get_socketio_instance()
        if socketio_instance:
            socketio_instance.emit(event_name, payload, room=client_id)
        else:
            logger.error("SocketIO instance not available to emit error to client.")


    # Note: start_streaming_response is synchronous and uses threads.
    # For a fully async stack with Uvicorn, this would ideally be an async method using asyncio tasks.
    def start_streaming_response(
        self, session_id: str, message: WebSocketMessage, model: str
    ):
        """Start streaming response from agent with proper Flask context"""
        # This method is kept largely as-is for single-agent streaming.
        # Error handling improvements are added.

        session = self.streaming_sessions.get(session_id)
        # Added active check more carefully
        if not session or not session.get("active", False):
            logger.warning(f"Streaming session {session_id} not found or inactive.")
            return

        client_id = session.get("client_id") # Use .get for safety
        agent_id = session.get("agent_id")

        if not client_id or not agent_id:
            logger.error(f"Client ID or Agent ID missing in session {session_id}. Aborting stream.")
            if session_id in self.streaming_sessions: # Clean up bad session
                del self.streaming_sessions[session_id]
            return

        socketio_instance = get_socketio_instance() # Get socketio instance for emits

        try:
            if socketio_instance:
                socketio_instance.emit( # Emit stream start
                    "response_stream_start",
                    {"session_id": session_id, "agent_id": agent_id, "timestamp": datetime.now(timezone.utc).isoformat()},
                    room=client_id,
                )

            with self.app.app_context(): # Essential for Flask services in threads
                from ..services.openrouter_service import get_openrouter_service, ChatMessage # Specific import
                from ..services.agent_service import get_agent_service, set_mcp_filesystem_service as set_agent_mcp_fs, get_agent_config
                from ..services.supermemory_service import get_supermemory_service

                openrouter_service = get_openrouter_service()
                supermemory_service = get_supermemory_service()
                agent_service = get_agent_service() # Assuming this returns a valid service or None

                if not openrouter_service:
                    logger.error("OpenRouter service not available for streaming.")
                    self._emit_error_to_client(client_id, session_id, agent_id, "AI service connection failed.")
                    self.update_agent_status(agent_id, AgentStatus.ERROR, {"details": "OpenRouter unavailable"})
                    return

                if not agent_service: # Or if get_agent_config is part of agent_service
                    logger.error(f"Agent service or config not available for agent {agent_id}.")
                    self._emit_error_to_client(client_id, session_id, agent_id, f"Configuration for agent {agent_id} not found.")
                    self.update_agent_status(agent_id, AgentStatus.ERROR, {"details": "Agent config missing"})
                    return

                agent_config_data = get_agent_config(agent_id) # From agent_service usually
                if not agent_config_data:
                    logger.error(f"Agent {agent_id} configuration not found.")
                    self._emit_error_to_client(client_id, session_id, agent_id, f"Agent {agent_id} not found.")
                    self.update_agent_status(agent_id, AgentStatus.ERROR, {"details": "Agent config missing"})
                    return

                # MCP Filesystem for Agent Service
                if self.mcp_filesystem_service and hasattr(agent_service, 'mcp_filesystem'): # Check if agent_service uses it
                    set_agent_mcp_fs(self.mcp_filesystem_service)
                    logger.info(f"Agent {agent_id} has MCP filesystem access via agent_service.")

                messages_for_llm = [
                    ChatMessage(role="system", content=agent_config_data.get("system_prompt", "You are a helpful assistant.")),
                    ChatMessage(role="user", content=message.content),
                ]

                if supermemory_service:
                    try:
                        memory_context = supermemory_service.get_cross_agent_context(message.content, exclude_agent=agent_id)
                        if memory_context:
                            context_text = supermemory_service.format_memory_context(memory_context) # Assuming this method exists
                            messages_for_llm[0] = ChatMessage(
                                role="system",
                                content=f"{agent_config_data.get('system_prompt', '')}\n\nRelevant context from previous conversations:\n{context_text}"
                            )
                    except Exception as e:
                        logger.warning(f"⚠️ Could not retrieve memory context for agent {agent_id}: {e}")
                        # Non-fatal, continue without context

                full_response_content = ""
                try:
                    for chunk in openrouter_service.chat_completion_stream(
                        messages=messages_for_llm, model=model, temperature=0.7
                    ):
                        current_session_data = self.streaming_sessions.get(session_id, {})
                        if not current_session_data.get("active", False): # Re-check active status inside loop
                            logger.info(f"Stream {session_id} for agent {agent_id} stopped by client or system.")
                            break
                        full_response_content += chunk
                        if socketio_instance:
                           socketio_instance.emit("response_stream_chunk", {"session_id": session_id, "agent_id": agent_id, "chunk": chunk}, room=client_id)
                except SwarmError as e:
                    logger.error(f"❌ SwarmError during streaming for agent {agent_id}: {e}")
                    self._emit_error_to_client(client_id, session_id, agent_id, f"AI service error: {e.message if hasattr(e, 'message') else str(e)}")
                    self.update_agent_status(agent_id, AgentStatus.ERROR, {"details": str(e)})
                    return
                except Exception as e:
                    logger.error(f"❌ Unexpected error during OpenRouter stream for agent {agent_id}: {e}", exc_info=True)
                    self._emit_error_to_client(client_id, session_id, agent_id, "An unexpected error occurred with the AI service.")
                    self.update_agent_status(agent_id, AgentStatus.ERROR, {"details": "Streaming failed"})
                    return


                if supermemory_service and full_response_content:
                    try:
                        supermemory_service.store_conversation(
                            agent_id=agent_id, user_message=message.content, agent_response=full_response_content, model_used=model
                        )
                    except Exception as e:
                        logger.warning(f"⚠️ Could not store conversation for agent {agent_id} in SuperMemory: {e}")
                        # Non-fatal for the client response

                if self.orchestrator and os.getenv("NOTIFICATION_EMAIL") and full_response_content:
                    try:
                        asyncio.run( # This is problematic in a sync thread if not careful with event loops
                            self.orchestrator.send_email(
                                os.getenv("NOTIFICATION_EMAIL"),
                                f"Conversation with {agent_id} (Session: {session_id})",
                                f"User: {message.content}\nAgent ({model}): {full_response_content}",
                                agent_id=agent_id # Orchestrator's send_email might use this for "from"
                            )
                        )
                    except Exception as e: # Catch specific exceptions
                        logger.warning(f"⚠️ Could not send notification email for agent {agent_id}: {e}")


                if socketio_instance:
                    socketio_instance.emit("response_stream_end", {"session_id": session_id, "agent_id": agent_id, "full_response": full_response_content}, room=client_id)

        except Exception as e: # Broad catch for setup errors before streaming loop
            logger.error(f"❌ Critical error preparing streaming response for agent {agent_id} (session {session_id}): {e}", exc_info=True)
            if client_id and agent_id: # Ensure these are defined
                 self._emit_error_to_client(client_id, session_id, agent_id, "Failed to start streaming response due to a server error.")
            if agent_id: # Ensure agent_id is defined before updating status
                 self.update_agent_status(agent_id, AgentStatus.ERROR, {"details": "Streaming setup failed"})
        finally:
            if session_id in self.streaming_sessions:
                logger.debug(f"Removing streaming session {session_id} post-operation.")
                del self.streaming_sessions[session_id]
            if agent_id:
                self.update_agent_status(agent_id, AgentStatus.IDLE)


    def update_agent_status(
        self, agent_id: str, status: AgentStatus, metadata: Dict[str, Any] = None
    ):
        """Update agent status and broadcast to connected clients"""
        # This method remains largely the same.
        current_status_val = status.value
        self.agent_states[agent_id] = {
            "status": current_status_val,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
        }
        socketio_instance = get_socketio_instance()
        if socketio_instance:
            socketio_instance.emit(
                "agent_status_update",
                {"agent_id": agent_id, "status": current_status_val, "timestamp": datetime.now(timezone.utc).isoformat(), "metadata": metadata or {}},
                broadcast=True, # Emits to all clients in the default namespace
            )
        else:
            logger.error("SocketIO instance not available for agent_status_update broadcast.")


    def get_connected_clients(self) -> Dict[str, Any]:
        """Get information about connected clients"""
        # This method can remain the same.
        return {
            "total_clients": len(self.connected_clients),
            "clients_sids": list(self.connected_clients.keys()), # More specific key name
            "active_rooms_count": len(self.active_rooms),
            "streaming_sessions_count": len(self.streaming_sessions),
        }

    def get_agent_states(self) -> Dict[str, Any]:
        """Get current states of all agents"""
        # This method can remain the same.
        return self.agent_states

    def broadcast_system_message(self, message_content: str, message_type: str = "system_info"): # More specific type
        """Broadcast system message to all connected clients"""
        socketio_instance = get_socketio_instance()
        if socketio_instance:
            socketio_instance.emit(
                "system_message",
                {
                    "message": message_content, # Renamed for clarity
                    "type": message_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
                broadcast=True,
            )
        else:
            logger.error("SocketIO instance not available for system_message broadcast.")


    def send_file_access_notification( # This seems MCP specific, ensure mcp_filesystem_service is used if needed
        self, client_id: str, operation: str, file_path: str, success: bool, details: Optional[str] = None
    ):
        """Send file access notification to specific client"""
        # This method can remain the same, added optional details.
        payload = {
            "operation": operation,
            "file_path": file_path,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if details:
            payload["details"] = details

        socketio_instance = get_socketio_instance()
        if socketio_instance:
            socketio_instance.emit("file_access_notification", payload, room=client_id)
        else:
            logger.error(f"SocketIO instance not available to send file_access_notification to {client_id}.")


    def get_service_status(self) -> Dict[str, Any]: # Used by health check or status endpoints
        """Get WebSocket service status"""
        # This method can remain the same.
        return {
            "status": "healthy", # This should be dynamically determined by _health_check ideally
            "connected_clients": len(self.connected_clients),
            "active_rooms": len(self.active_rooms), # Consider if this should be count or list of rooms
            "streaming_sessions": len(self.streaming_sessions),
            "agent_states_count": len(self.agent_states), # More specific key
            "mcp_filesystem_available": bool(self.mcp_filesystem_service),
            "orchestrator_available": bool(self.orchestrator)
        }


class SwarmNamespace(Namespace):
    """Enhanced namespace for swarm agent communication.
    Needs access to WebSocketService instance, typically passed during initialization.
    """

    def __init__(self, namespace, websocket_service_instance: WebSocketService):
        super().__init__(namespace)
        self.ws_service = websocket_service_instance # Renamed for clarity
        if not self.ws_service.orchestrator:
             logger.error("Orchestrator not available in SwarmNamespace. Swarm messages will fail.")


    def on_connect(self):
        """Handle client connection. Implement authentication here."""
        client_sid = request.sid
        # TODO: Implement proper authentication (e.g., token-based)
        # For now, using user_id from query args if provided, else anonymous
        user_id = request.args.get("user_id", f"anon_{client_sid[:6]}")
        auth_token = request.args.get("token") # Example: token-based auth

        # Basic token validation placeholder
        if False: # Replace with: not auth_token or not self._is_valid_token(auth_token): # _is_valid_token needs implementation
            logger.warning(f"Client {client_sid} failed authentication. Disconnecting.")
            # Emit directly to sid before disconnecting
            get_socketio_instance().emit("auth_failed", {"message": "Authentication required or token invalid."}, room=client_sid)
            # current_app.socketio.disconnect(client_sid) # How to disconnect depends on Flask-SocketIO version
            return False # Returning False from on_connect should reject the connection

        self.ws_service.connected_clients[client_sid] = {
            "user_id": user_id, # Store authenticated user_id
            "client_sid": client_sid,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
        }
        logger.info(f"🔌 Client connected: {client_sid} (user: {user_id})")
        emit("connection_confirmed", { # emit is fine here as it's in Namespace context
            "client_id": client_sid,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mcp_filesystem_available": bool(self.ws_service.mcp_filesystem_service)
        }, room=client_sid)

    def _is_valid_token(self, token: str) -> bool:
        # Placeholder for actual token validation logic
        # E.g., validate JWT, call an auth service, etc.
        logger.debug(f"Validating token (placeholder): {token[:10]}...")
        return True # Insecure: replace with real validation


    def on_disconnect(self):
        """Handle client disconnection"""
        client_sid = request.sid
        if client_sid in self.ws_service.connected_clients:
            user_info = self.ws_service.connected_clients.pop(client_sid) # Use pop
            logger.info(f"🔌 Client disconnected: {client_sid} (user: {user_info.get('user_id')})")
        else:
            logger.info(f"🔌 Client disconnected: {client_sid} (no prior user info found)")

        # Clean up any streaming sessions associated with this client
        sessions_to_remove = [
            session_id for session_id, session_data in self.ws_service.streaming_sessions.items()
            if session_data.get("client_id") == client_sid
        ]
        for session_id in sessions_to_remove:
            logger.debug(f"Removing streaming session {session_id} for disconnected client {client_sid}")
            # Also mark as inactive to stop any ongoing stream loops
            if session_id in self.ws_service.streaming_sessions:
                 self.ws_service.streaming_sessions[session_id]["active"] = False # Signal thread to stop
            # Deletion is handled by the stream thread itself or after a timeout if preferred

    def on_agent_message(self, data: Dict[str, Any]):
        """Handle single agent message from client (for streaming primarily)"""
        client_sid = request.sid
        try:
            agent_id = data.get("agent_id")
            message_content = data.get("message")
            # Use global default model, allow override from client
            model = data.get("model", DEFAULT_AGENT_MODEL)

            if not agent_id or not message_content:
                logger.warning(f"Client {client_sid} sent invalid agent_message: Missing agent_id or message.")
                emit("error", {"message": "Missing agent_id or message content."}, room=client_sid)
                return

            if client_sid in self.ws_service.connected_clients:
                self.ws_service.connected_clients[client_sid]["last_activity"] = datetime.now(timezone.utc).isoformat()

            msg_obj = WebSocketMessage(
                message_id=str(uuid.uuid4()), message_type="user_to_agent_stream",
                content=message_content, sender_id=client_sid, recipient_id=agent_id
            )

            self.ws_service.update_agent_status(agent_id, AgentStatus.THINKING) # Update status

            session_id = str(uuid.uuid4())
            self.ws_service.streaming_sessions[session_id] = {
                "client_id": client_sid, "agent_id": agent_id, "active": True,
                "started_at": datetime.now(timezone.utc).isoformat(), "type": "single_agent_stream"
            }

            # Use a thread for this synchronous, blocking call.
            # If start_streaming_response were async, could use socketio.start_background_task
            thread = threading.Thread(
                target=self.ws_service.start_streaming_response, # This is instance method of WebSocketService
                args=(session_id, msg_obj, model),
            )
            thread.daemon = True # Ensure thread doesn't block app exit
            thread.start()
            logger.info(f"Started streaming thread for session {session_id}, agent {agent_id}.")

        except KeyError as e: # More specific error for missing data keys
            logger.error(f"❌ Missing key in agent_message data from {client_sid}: {e}", exc_info=True)
            emit("error", {"message": f"Invalid message format: missing {e}."}, room=client_sid)
        except Exception as e:
            logger.error(f"❌ Error handling agent_message from {client_sid}: {e}", exc_info=True)
            emit("error", {"message": f"Error processing your message: {str(e)}"}, room=client_sid)


    async def on_swarm_message(self, data: Dict[str, Any]):
        """Handle message intended for multiple agents or orchestrator-led processing (async)."""
        client_sid = request.sid
        logger.info(f"Received swarm_message from {client_sid}: {str(data.get('message', ''))[:50]}...") # Log first 50 chars

        if not self.ws_service.orchestrator: # Check if orchestrator is available
            logger.error(f"Orchestrator not available for swarm_message from {client_sid}.")
            emit("error", {"message": "Swarm intelligence is currently unavailable."}, room=client_sid)
            return

        message_content = data.get("message")
        target_agent_ids = data.get("agent_ids") # Optional: client can specify agent IDs
        conversation_id = data.get("conversation_id", str(uuid.uuid4())) # Generate if not provided

        if not message_content:
            logger.warning(f"Client {client_sid} sent swarm_message with no content.")
            emit("error", {"message": "Missing message content for swarm."}, room=client_sid)
            return

        # Update client activity
        if client_sid in self.ws_service.connected_clients:
            self.ws_service.connected_clients[client_sid]["last_activity"] = datetime.now(timezone.utc).isoformat()

        try:
            # Orchestrator's process_message is async and handles mentions/selection
            # It returns a list of dictionaries, each with agent_id, status, response/error
            orchestrator_responses = await self.ws_service.orchestrator.process_message(
                message=message_content,
                agent_ids=target_agent_ids, # Can be None, orchestrator will handle
                conversation_id=conversation_id
            )

            emit("swarm_responses", { # This emit is within the async handler context
                "conversation_id": conversation_id,
                "original_message": message_content,
                "responses": orchestrator_responses # This is the structured list
            }, room=client_sid)
            logger.info(f"Sent swarm_responses for conversation {conversation_id} to {client_sid}.")

        except SwarmError as e: # Catch custom errors from orchestrator
            logger.error(f"❌ SwarmError in on_swarm_message from orchestrator (client {client_sid}): {e}", exc_info=True)
            emit("error", {"message": f"Swarm processing error: {e.message if hasattr(e, 'message') else str(e)}", "code": e.code.value if hasattr(e, 'code') else None}, room=client_sid)
        except Exception as e:
            logger.error(f"❌ Unexpected error in on_swarm_message (client {client_sid}): {e}", exc_info=True)
            emit("error", {"message": f"An unexpected error occurred while processing your swarm message: {str(e)}"}, room=client_sid)


    def on_stop_stream(self, data: Dict[str, Any]):
        """Handle stream stop request for single agent streaming"""
        client_sid = request.sid # Get client_sid for logging/context
        try:
            session_id = data.get("session_id")
            if not session_id:
                logger.warning(f"Client {client_sid} sent stop_stream without session_id.")
                emit("error", {"message": "session_id missing for stop_stream."}, room=client_sid)
                return

            if session_id in self.ws_service.streaming_sessions:
                logger.info(f"🛑 Client {client_sid} requested stop for stream: {session_id}")
                self.ws_service.streaming_sessions[session_id]["active"] = False
                # The streaming thread itself will clean up the session entry after loop termination.
                emit("stream_stopped", {"session_id": session_id}, room=client_sid) # Acknowledge stop
            else:
                logger.warning(f"Client {client_sid} requested stop for non-existent or already stopped stream: {session_id}")
                emit("error", {"message": f"Stream session {session_id} not found or already stopped."}, room=client_sid)
        except Exception as e:
            logger.error(f"❌ Error handling stop_stream from {client_sid} for session {data.get('session_id')}: {e}", exc_info=True)
            emit("error", {"message": "Error processing stop_stream request."}, room=client_sid)


    def on_join_room(self, data: Dict[str, Any]):
        """Handle room join request. Ensure room_id is validated if necessary."""
        client_sid = request.sid
        try:
            room_id = data.get("room_id")
            if not room_id or not isinstance(room_id, str) or len(room_id) > 64: # Basic validation
                emit("error", {"message": "Invalid room_id provided."}, room=client_sid)
                return

            join_room(room_id) # Flask-SocketIO function
            # Update active_rooms in WebSocketService
            if room_id not in self.ws_service.active_rooms:
                self.ws_service.active_rooms[room_id] = set()
            self.ws_service.active_rooms[room_id].add(client_sid)

            logger.info(f"Client {client_sid} joined room: {room_id}")
            emit("room_joined", {"room_id": room_id, "client_id": client_sid}, room=client_sid) # Also emit to client
            # emit("user_joined_room", {"room_id": room_id, "client_id": client_sid}, room=room_id, include_self=False) # Notify others in room

        except Exception as e:
            logger.error(f"❌ Error handling join_room for {client_sid}, room {data.get('room_id')}: {e}", exc_info=True)
            emit("error", {"message": "Error joining room."}, room=client_sid)


    def on_leave_room(self, data: Dict[str, Any]):
        """Handle room leave request"""
        client_sid = request.sid
        try:
            room_id = data.get("room_id")
            if not room_id: # Basic validation
                emit("error", {"message": "room_id not provided for leaving."}, room=client_sid)
                return

            leave_room(room_id) # Flask-SocketIO function
            if room_id in self.ws_service.active_rooms:
                self.ws_service.active_rooms[room_id].discard(client_sid)
                if not self.ws_service.active_rooms[room_id]: # If room is empty, remove it
                    del self.ws_service.active_rooms[room_id]

            logger.info(f"Client {client_sid} left room: {room_id}")
            emit("room_left", {"room_id": room_id, "client_id": client_sid}, room=client_sid)
            # emit("user_left_room", {"room_id": room_id, "client_id": client_sid}, room=room_id, include_self=False)

        except Exception as e:
            logger.error(f"❌ Error handling leave_room for {client_sid}, room {data.get('room_id')}: {e}", exc_info=True)
            emit("error", {"message": "Error leaving room."}, room=client_sid)


    def on_get_status(self, data: Optional[Dict[str, Any]] = None): # data might not be used but good to have consistent signature
        """Handle status request from client"""
        client_sid = request.sid
        try:
            # Consider what status info is safe and useful for the client
            # For now, using the existing get_service_status, but it might expose too much.
            # A filtered version might be better for client requests.
            service_status = self.ws_service.get_service_status()
            client_view_status = {
                "connected_clients": service_status.get("connected_clients"),
                "mcp_available": service_status.get("mcp_filesystem_available"),
                "orchestrator_available": service_status.get("orchestrator_available")
                # Add other relevant, safe-to-expose statuses
            }
            emit("status_response", client_view_status, room=client_sid)
        except Exception as e:
            logger.error(f"❌ Error handling get_status for {client_sid}: {e}", exc_info=True)
            emit("error", {"message": "Error retrieving service status."}, room=client_sid)


# --- Service Initialization ---

_websocket_service_instance: Optional[WebSocketService] = None
_socketio_instance: Optional[SocketIO] = None # To hold the SocketIO object

def initialize_websocket(flask_app, socketio: SocketIO, mcp_service=None, orchestrator_svc: Optional[SwarmOrchestrator]=None) -> WebSocketService:
    """
    Initializes the WebSocketService and registers the SwarmNamespace.
    This should be called once during app setup.
    """
    global _websocket_service_instance, _socketio_instance

    if _websocket_service_instance:
        logger.warning("WebSocketService already initialized. Returning existing instance.")
        return _websocket_service_instance

    if not orchestrator_svc:
        orchestrator_svc = get_orchestrator() # Get from global if not passed
        logger.info("Using global orchestrator instance for WebSocketService.")

    _websocket_service_instance = WebSocketService(
        app=flask_app,
        mcp_filesystem_service=mcp_service,
        orchestrator_instance=orchestrator_svc
    )

    _socketio_instance = socketio # Store the SocketIO instance

    # Register the namespace with the SocketIO instance
    # The namespace path can be configurable, e.g., '/swarm'
    # Pass the WebSocketService instance to the Namespace
    socketio.on_namespace(SwarmNamespace('/swarm', _websocket_service_instance))

    logger.info(f"WebSocketService initialized and SwarmNamespace registered on '/swarm'. Orchestrator: {'Yes' if orchestrator_svc else 'No'}")
    return _websocket_service_instance


def get_websocket_service() -> Optional[WebSocketService]:
    """
    Get the global WebSocket service instance.
    Returns None if initialize_websocket has not been called.
    """
    if not _websocket_service_instance:
        # This log might be too noisy if called by utilities before app fully up.
        # logger.error("WebSocketService accessed before initialization.")
        pass
    return _websocket_service_instance

def get_socketio_instance() -> Optional[SocketIO]:
    """Get the global SocketIO instance."""
    if not _socketio_instance:
        # logger.error("SocketIO instance accessed before initialization or not set.")
        pass
    return _socketio_instance
