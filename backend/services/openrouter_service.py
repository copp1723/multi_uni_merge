"""
OpenRouter service for AI model interactions with streaming support
Robust implementation with proper error handling and model management
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Generator, Iterator
import requests

# Import BaseService using relative imports
from ..utils.service_utils import BaseService, ServiceHealth, ServiceStatus

logger = logging.getLogger(__name__)

@dataclass
class ModelInfo:
    """Information about an available AI model"""
    id: str
    name: str
    description: str
    context_length: int
    pricing: Dict[str, str]

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> "ModelInfo":
        """Create ModelInfo from API response"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            context_length=data.get("context_length", 0),
            pricing=data.get("pricing", {}),
        )

@dataclass
class ChatMessage:
    """Represents a chat message"""
    role: str  # 'system', 'user', 'assistant'
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}

@dataclass
class ChatResponse:
    """Response from chat completion"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None

class OpenRouterService(BaseService):
    """Service for interacting with OpenRouter API with streaming support"""
    
    def __init__(self, api_key: str):
        super().__init__("openrouter")  # Initialize BaseService with service name
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://swarm-agents-web.onrender.com",
            "X-Title": "Swarm Multi-Agent System",
        }
        self._models_cache = None
        self._cache_timestamp = 0
        self.cache_duration = 300  # 5 minutes
    
    async def _health_check(self) -> ServiceHealth:
        """Implement service-specific health check"""
        try:
            # Test API connection by fetching models
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                models_data = response.json()
                model_count = len(models_data.get("data", []))
                
                return ServiceHealth(
                    status=ServiceStatus.HEALTHY, 
                    message="Service operational", 
                    details={
                        "api_status": "connected",
                        "available_models": model_count,
                        "base_url": self.base_url
                    }, 
                    last_check=datetime.now(timezone.utc).isoformat()
                )
            else:
                return ServiceHealth(
                    status=ServiceStatus.UNHEALTHY,
                    message=f"API returned status {response.status_code}",
                    details={"error": f"API returned status {response.status_code}"},
                    last_check=datetime.now(timezone.utc).isoformat()
                )
        except Exception as e:
            return ServiceHealth(
                status=ServiceStatus.UNHEALTHY, 
                message=f"Connection failed: {str(e)}", 
                details={"error": str(e)}, 
                last_check=datetime.now(timezone.utc).isoformat()
            )
    
    def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models with caching"""
        # Check cache
        current_time = time.time()
        if (
            self._models_cache is not None
            and current_time - self._cache_timestamp < self.cache_duration
        ):
            logger.info("Returning cached models")
            return self._models_cache
        
        logger.info("Fetching models from OpenRouter API")
        
        try:
            response = requests.get(f"{self.base_url}/models", headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if "data" not in data:
                logger.error("Invalid response format from OpenRouter models API")
                return []
            
            models = []
            for model_data in data["data"]:
                try:
                    model = ModelInfo.from_api_response(model_data)
                    models.append(model)
                except Exception as e:
                    logger.warning(f"Failed to parse model data: {e}")
                    continue
            
            # Cache the results
            self._models_cache = models
            self._cache_timestamp = current_time
            
            logger.info(f"✅ Retrieved {len(models)} models from OpenRouter")
            return models
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Failed to fetch models from OpenRouter: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching models: {e}")
            return []
    
    def get_model_by_id(self, model_id: str) -> Optional[ModelInfo]:
        """Get specific model information by ID"""
        models = self.get_available_models()
        for model in models:
            if model.id == model_id:
                return model
        return None
    
    def chat_completion(
        self,
        messages: List[ChatMessage],
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> ChatResponse:
        """
        Create a chat completion
        
        Args:
            messages: List of chat messages
            model: Model ID to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters
        
        Returns:
            ChatResponse object
        """
        try:
            payload = {
                "model": model,
                "messages": [msg.to_dict() for msg in messages],
                "temperature": temperature,
                "stream": stream,
                **kwargs
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            logger.info(f"🤖 Sending chat completion request to {model}")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_streaming_response(response, model)
            else:
                return self._handle_standard_response(response, model)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ OpenRouter API request failed: {e}")
            raise Exception(f"OpenRouter API error: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in chat completion: {e}")
            raise Exception(f"Chat completion error: {e}")
    
    def _handle_standard_response(self, response: requests.Response, model: str) -> ChatResponse:
        """Handle standard (non-streaming) response"""
        data = response.json()
        
        if "choices" not in data or not data["choices"]:
            raise Exception("Invalid response format from OpenRouter")
        
        choice = data["choices"][0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})
        
        logger.info(f"✅ Received response from {model}")
        
        return ChatResponse(
            content=content,
            model=model,
            usage=usage
        )
    
    def _handle_streaming_response(self, response: requests.Response, model: str) -> Generator[str, None, None]:
        """Handle streaming response"""
        logger.info(f"🔄 Starting streaming response from {model}")
        
        try:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # Remove 'data: ' prefix
                        
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except Exception as e:
            logger.error(f"❌ Error in streaming response: {e}")
            raise Exception(f"Streaming error: {e}")
    
    def chat_completion_stream(
        self,
        messages: List[ChatMessage],
        model: str = "anthropic/claude-3.5-sonnet",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Generator[str, None, None]:
        """
        Create a streaming chat completion
        
        Args:
            messages: List of chat messages
            model: Model ID to use
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
        
        Yields:
            Content chunks as they arrive
        """
        try:
            payload = {
                "model": model,
                "messages": [msg.to_dict() for msg in messages],
                "temperature": temperature,
                "stream": True,
                **kwargs
            }
            
            if max_tokens:
                payload["max_tokens"] = max_tokens
            
            logger.info(f"🔄 Starting streaming chat completion with {model}")
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                stream=True
            )
            response.raise_for_status()
            
            yield from self._handle_streaming_response(response, model)
            
        except Exception as e:
            logger.error(f"❌ Streaming chat completion failed: {e}")
            raise Exception(f"Streaming error: {e}")
    
    def get_popular_models(self) -> List[ModelInfo]:
        """Get list of popular/recommended models"""
        all_models = self.get_available_models()
        
        # Define popular model IDs
        popular_model_ids = [
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "openai/gpt-3.5-turbo",
            "meta-llama/llama-3.1-8b-instruct",
            "google/gemini-pro",
            "mistralai/mistral-7b-instruct"
        ]
        
        popular_models = []
        for model_id in popular_model_ids:
            model = self.get_model_by_id(model_id)
            if model:
                popular_models.append(model)
        
        return popular_models
    
    def test_connection(self) -> bool:
        """Test the OpenRouter API connection"""
        try:
            models = self.get_available_models()
            if models:
                logger.info("✅ OpenRouter connection test successful")
                return True
            else:
                logger.error("❌ OpenRouter connection test failed - no models returned")
                return False
        except Exception as e:
            logger.error(f"❌ OpenRouter connection test failed: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status information"""
        try:
            models = self.get_available_models()
            return {
                "status": "healthy" if models else "unhealthy",
                "models_available": len(models),
                "cache_status": "active" if self._models_cache else "empty",
                "last_cache_update": self._cache_timestamp,
                "api_endpoint": self.base_url
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "models_available": 0,
                "cache_status": "error"
            }


# Global OpenRouter service instance
openrouter_service: Optional[OpenRouterService] = None

def initialize_openrouter(api_key: str) -> OpenRouterService:
    """Initialize OpenRouter service"""
    global openrouter_service
    openrouter_service = OpenRouterService(api_key)
    return openrouter_service

def get_openrouter_service() -> Optional[OpenRouterService]:
    """Get the global OpenRouter service instance"""
    return openrouter_service
