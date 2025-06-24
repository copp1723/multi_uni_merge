"""
Agent Service with Orchestration - Handles multi-agent collaboration and message routing
Enables @mention-based routing and cross-agent memory sharing
"""

import re
import logging
from typing import List, Optional, Dict, Any
from flask_socketio import emit
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Orchestrates multi-agent collaboration and message routing"""
    
    def __init__(self, openrouter, supermemory):
        self.openrouter = openrouter
        self.supermemory = supermemory
        
        # Define available agents - this could be loaded from config
        self.agents = {
            "cathy": {
                "id": "cathy",
                "name": "Cathy",
                "description": "Communication specialist",
                "system_prompt": "You are Cathy, a friendly and helpful communication specialist."
            },
            "coder": {
                "id": "coder", 
                "name": "Coder",
                "description": "Programming expert",
                "system_prompt": "You are Coder, an expert programmer who helps with coding tasks."
            }
        }
        
    def parse_mentions(self, message: str) -> List[str]:
        """Parse @mentions from a message and return list of agent IDs"""
        # Pattern to match @mentions (word characters after @)
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, message.lower())
        
        agent_ids = []
        for mention in mentions:
            # Check if mention matches any agent name or ID
            for agent_id, agent_info in self.agents.items():
                if (mention == agent_id.lower() or 
                    mention in agent_info['name'].lower() or
                    agent_info['name'].lower().startswith(mention)):
                    if agent_id not in agent_ids:
                        agent_ids.append(agent_id)
                    break
        
        logger.info(f"Parsed mentions: {mentions} -> Agent IDs: {agent_ids}")
        return agent_ids
    
    def route_message_to_agent(self, agent_id: str, message: str, model: str, session_id: str):
        """Route message to a specific agent with added cross-agent context."""
        
        try:
            # Validate agent exists
            if agent_id not in self.agents:
                logger.error(f"Agent {agent_id} not found")
                emit('response_stream_error', {
                    'error': f'Agent {agent_id} not found',
                    'agent_id': agent_id
                }, room=session_id)
                return
            
            agent_info = self.agents[agent_id]
            
            # 1. Get recent, relevant conversation history from Supermemory
            context = ""
            if self.supermemory:
                try:
                    # Query for relevant context from other agents
                    memory_results = self.supermemory.get_cross_agent_context(
                        current_query=message,
                        exclude_agent=agent_id
                    )
                    
                    if memory_results:
                        context = self.supermemory.format_memory_context(memory_results)
                        logger.info(f"Retrieved {len(memory_results)} cross-agent memories for {agent_id}")
                except Exception as e:
                    logger.warning(f"Could not retrieve cross-agent context: {e}")
            
            # 2. Build an enhanced prompt with the retrieved context
            enhanced_prompt = agent_info['system_prompt']
            
            if context:
                enhanced_prompt += f"\n\n{context}"
            
            # 3. Send initial response notification
            emit('response_stream_start', {
                'agent_id': agent_id,
                'agent_name': agent_info['name'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }, room=session_id)
            
            # 4. Stream response from OpenRouter
            if self.openrouter:
                try:
                    # Prepare messages for the chat
                    from backend.services.openrouter_service import ChatMessage
                    
                    messages = [
                        ChatMessage(role="system", content=enhanced_prompt),
                        ChatMessage(role="user", content=message)
                    ]
                    
                    full_response = ""
                    
                    # Stream the response
                    for chunk in self.openrouter.chat_completion_stream(
                        messages=messages,
                        model=model,
                        temperature=0.7
                    ):
                        full_response += chunk
                        
                        # Emit each chunk to the client
                        emit('response_stream_chunk', {
                            'agent_id': agent_id,
                            'agent_name': agent_info['name'],
                            'chunk': chunk,
                            'is_final': False,
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }, room=session_id)
                    
                    # Emit final response
                    emit('response_stream_chunk', {
                        'agent_id': agent_id,
                        'agent_name': agent_info['name'],
                        'chunk': '',
                        'is_final': True,
                        'full_response': full_response,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    }, room=session_id)
                    
                    # 5. Save interaction to Supermemory
                    if self.supermemory and full_response:
                        try:
                            self.supermemory.store_conversation(
                                agent_id=agent_id,
                                user_message=message,
                                agent_response=full_response,
                                model_used=model,
                                metadata={'session_id': session_id}
                            )
                            logger.info(f"Stored conversation for agent {agent_id}")
                        except Exception as e:
                            logger.warning(f"Could not store conversation: {e}")
                    
                except Exception as e:
                    logger.error(f"Error generating response for agent {agent_id}: {e}")
                    emit('response_stream_error', {
                        'error': str(e),
                        'agent_id': agent_id
                    }, room=session_id)
            
        except Exception as e:
            logger.error(f"Error in route_message_to_agent for {agent_id}: {e}")
            emit('response_stream_error', {
                'error': str(e),
                'agent_id': agent_id
            }, room=session_id)
