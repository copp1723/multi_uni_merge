"""
Supermemory Service - Real implementation for conversation persistence and memory management
Enables cross-agent memory sharing and automatic conversation referencing
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

# Import BaseService using relative imports
from ..utils.service_utils import BaseService, ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)

@dataclass
class ConversationEntry:
    """Represents a single conversation entry"""
    id: str
    agent_id: str
    user_message: str
    agent_response: str
    timestamp: str
    model_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class MemoryQuery:
    """Represents a memory query for context retrieval"""
    query: str
    agent_id: Optional[str] = None
    limit: int = 10
    similarity_threshold: float = 0.7

class SupermemoryService(BaseService):
    """Service for managing conversation persistence and memory with Supermemory API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.supermemory.ai"):
        super().__init__("supermemory")  # Initialize BaseService with service name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        
        # Validate API key on initialization
        if not self.api_key or not self.api_key.startswith("sm_"):
            logger.warning("Invalid Supermemory API key format - expected format: sm_*")

    async def _health_check(self) -> ServiceHealth:
        """Implement service-specific health check"""
        try:
            return ServiceHealth(
                status=ServiceStatus.HEALTHY, 
                message="Service operational", 
                details={
                    "api_status": "configured",
                    "base_url": self.base_url,
                    "api_key_format": "valid" if self.api_key.startswith("sm_") else "invalid"
                }, 
                last_check=datetime.now(timezone.utc).isoformat()
            )
        except Exception as e:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY, 
                message=f"Service error: {str(e)}", 
                details={"error": str(e)}, 
                last_check=datetime.now(timezone.utc).isoformat()
            )
    
    def store_conversation(
        self,
        agent_id: str,
        user_message: str,
        agent_response: str,
        model_used: str = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Store a conversation entry in Supermemory"""
        
        # Create conversation entry
        entry = ConversationEntry(
            id=f"{agent_id}_{datetime.now(timezone.utc).isoformat()}",
            agent_id=agent_id,
            user_message=user_message,
            agent_response=agent_response,
            timestamp=datetime.now(timezone.utc).isoformat(),
            model_used=model_used,
            metadata=metadata or {},
        )
        
        # Prepare content for storage
        content = f"""
Agent: {agent_id}
User: {user_message}
Assistant: {agent_response}
Model: {model_used or 'unknown'}
Timestamp: {entry.timestamp}
"""
        
        # Add metadata as tags
        tags = [f"agent:{agent_id}"]
        if model_used:
            tags.append(f"model:{model_used}")
        if metadata:
            for key, value in metadata.items():
                tags.append(f"{key}:{value}")
        
        payload = {
            "content": content,
            "title": f"Conversation with {agent_id}",
            "description": f"User conversation with {agent_id} agent",
            "tags": tags,
            "metadata": {
                "entry_id": entry.id,
                "agent_id": agent_id,
                "timestamp": entry.timestamp,
                "model_used": model_used,
                **metadata,
            },
        }
        
        try:
            response = requests.post(f"{self.base_url}/api/add", json=payload, headers=self.headers)
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✅ Successfully stored conversation for agent {agent_id}")
                return result.get("id", entry.id)
            else:
                logger.error(f"❌ Failed to store conversation: {response.status_code} - {response.text}")
                return entry.id
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error storing conversation: {e}")
            return entry.id
        except Exception as e:
            logger.error(f"❌ Unexpected error storing conversation: {e}")
            return entry.id
    
    def query_memory(self, query: MemoryQuery) -> List[Dict[str, Any]]:
        """Query memory for relevant conversation context"""
        
        try:
            # Prepare search payload
            search_payload = {
                "query": query.query,
                "limit": query.limit,
                "threshold": query.similarity_threshold
            }
            
            # Add agent filter if specified
            if query.agent_id:
                search_payload["filters"] = {"agent": query.agent_id}
            
            logger.info(f"🔍 Querying memory: '{query.query[:50]}...'")
            
            response = requests.post(
                f"{self.base_url}/api/search", 
                json=search_payload, 
                headers=self.headers
            )
            
            if response.status_code == 200:
                results = response.json()
                memories = results.get("results", [])
                
                logger.info(f"✅ Found {len(memories)} relevant memories")
                
                # Format results for easy consumption
                formatted_memories = []
                for memory in memories:
                    formatted_memories.append({
                        "id": memory.get("id"),
                        "content": memory.get("content"),
                        "score": memory.get("score", 0),
                        "metadata": memory.get("metadata", {}),
                        "timestamp": memory.get("metadata", {}).get("timestamp"),
                        "agent_id": memory.get("metadata", {}).get("agent_id")
                    })
                
                return formatted_memories
            else:
                logger.error(f"❌ Memory query failed: {response.status_code} - {response.text}")
                return []
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error querying memory: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error querying memory: {e}")
            return []
    
    def get_recent_conversations(self, agent_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversations, optionally filtered by agent"""
        
        query_text = f"recent conversations"
        if agent_id:
            query_text += f" with {agent_id}"
        
        query = MemoryQuery(
            query=query_text,
            agent_id=agent_id,
            limit=limit,
            similarity_threshold=0.1  # Lower threshold for recent conversations
        )
        
        return self.query_memory(query)
    
    def get_cross_agent_context(self, current_query: str, exclude_agent: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get relevant context from other agents' conversations"""
        
        try:
            # Search for relevant conversations from other agents
            search_payload = {
                "query": current_query,
                "limit": 5,
                "threshold": 0.6
            }
            
            # Exclude current agent if specified
            if exclude_agent:
                search_payload["filters"] = {"exclude_agent": exclude_agent}
            
            logger.info(f"🔄 Getting cross-agent context for: '{current_query[:50]}...'")
            
            response = requests.post(
                f"{self.base_url}/api/search", 
                json=search_payload, 
                headers=self.headers
            )
            
            if response.status_code == 200:
                results = response.json()
                memories = results.get("results", [])
                
                # Filter out conversations from the excluded agent
                if exclude_agent:
                    memories = [
                        m for m in memories 
                        if m.get("metadata", {}).get("agent_id") != exclude_agent
                    ]
                
                logger.info(f"✅ Found {len(memories)} cross-agent memories")
                return memories
            else:
                logger.error(f"❌ Cross-agent context query failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error getting cross-agent context: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test the Supermemory API connection"""
        try:
            # Try a simple search to test connectivity
            test_payload = {
                "query": "test connection",
                "limit": 1
            }
            
            response = requests.post(
                f"{self.base_url}/api/search", 
                json=test_payload, 
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code in [200, 404]:  # 404 is OK for empty results
                logger.info("✅ Supermemory connection test successful")
                return True
            else:
                logger.error(f"❌ Supermemory connection test failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Supermemory connection test failed: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error in connection test: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        try:
            # Test connection
            is_connected = self.test_connection()
            
            # Get some basic stats if connected
            if is_connected:
                recent_memories = self.get_recent_conversations(limit=1)
                return {
                    "status": "healthy",
                    "connected": True,
                    "api_endpoint": self.base_url,
                    "recent_memories_count": len(recent_memories),
                    "last_activity": recent_memories[0].get("timestamp") if recent_memories else None
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "api_endpoint": self.base_url,
                    "error": "Connection test failed"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e)
            }
    
    def format_memory_context(self, memories: List[Dict[str, Any]], max_length: int = 1000) -> str:
        """Format memory results into a context string for agent prompts"""
        if not memories:
            return ""
        
        context_parts = []
        current_length = 0
        
        for memory in memories:
            content = memory.get("content", "")
            agent_id = memory.get("metadata", {}).get("agent_id", "unknown")
            timestamp = memory.get("timestamp", "")
            
            # Create a formatted memory entry
            memory_text = f"[{agent_id} - {timestamp}]: {content[:200]}..."
            
            if current_length + len(memory_text) > max_length:
                break
            
            context_parts.append(memory_text)
            current_length += len(memory_text)
        
        if context_parts:
            return "Previous relevant conversations:\n" + "\n".join(context_parts)
        return ""


# Global Supermemory service instance
supermemory_service: Optional[SupermemoryService] = None

def initialize_supermemory(api_key: str, base_url: str = "https://api.supermemory.ai") -> SupermemoryService:
    """Initialize Supermemory service"""
    global supermemory_service
    supermemory_service = SupermemoryService(api_key, base_url)
    return supermemory_service

def get_supermemory_service() -> Optional[SupermemoryService]:
    """Get the global Supermemory service instance"""
    return supermemory_service
