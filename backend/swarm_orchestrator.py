# 🤖 SWARM AGENT ORCHESTRATION SYSTEM - CLEANED & REFACTORED

import os
import json
import asyncio
import aiohttp
import aiofiles
import smtplib
import logging
import re # Added for mention extraction
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field # Added field
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type # Added for retries

# Import utilities from current structure
from utils.error_handler import SwarmError, ErrorCode
from utils.async_utils import AsyncTaskManager
from utils.service_utils import BaseService
from utils.validators import validate_api_key, validate_email, validate_url

# Initialize logger
logger = logging.getLogger(__name__)

@dataclass
class AgentCapability:
    """Represents an agent's capability with metadata"""
    name: str
    description: str
    confidence_level: float
    execution_time_estimate: int  # in seconds
    tags: List[str] = field(default_factory=list) # Added tags for capability matching

@dataclass
class AgentPerformanceMetrics:
    """Tracks agent performance metrics"""
    total_tasks: int = 0
    successful_tasks: int = 0
    average_response_time: float = 0.0
    last_active: Optional[datetime] = None
    confidence_score: float = 0.8 # Default confidence, can be adjusted
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        return (self.successful_tasks / max(self.total_tasks, 1)) * 100

@dataclass
class SwarmAgent:
    """Enhanced agent with comprehensive capabilities and performance tracking"""
    id: str
    name: str
    role: str
    personality: str
    capabilities: List[AgentCapability]
    status: str = "idle" # Default status
    current_model: str = "anthropic/claude-3.5-sonnet" # Default model
    collaboration_style: str = "coordinator" # Default style
    performance: AgentPerformanceMetrics = field(default_factory=AgentPerformanceMetrics) # Ensure performance is initialized

    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary for API responses"""
        data = asdict(self)
        data['performance'] = asdict(self.performance) # Ensure performance is also a dict
        data['capabilities'] = [asdict(cap) for cap in self.capabilities] # Ensure capabilities are dicts
        return data

class SwarmOrchestrator:
    """
    Enhanced Swarm Intelligence Orchestration System
    
    Manages multiple AI agents with sophisticated coordination,
    performance tracking, and intelligent task distribution.
    """
    
    def __init__(self, agent_config_path: str = "agents_config.json"): # Added config path
        self.agents: Dict[str, SwarmAgent] = {}
        self.active_conversations: Dict[str, Dict] = {}
        self.task_queue: List[Dict] = [] # Consider if this is still needed or managed elsewhere
        self.performance_history: List[Dict] = [] # Consider persistence for this
        self.agent_config_path = agent_config_path
        
        # Initialize services
        self._initialize_agents()
        self._setup_services()
        
        logger.info("🤖 Swarm Agent Orchestration System initialized")
        logger.info(f"🚀 {len(self.agents)} agents loaded and ready for deployment")
    
    def _initialize_agents(self) -> None:
        """Load agent configurations from the JSON file."""
        try:
            # Construct path relative to this file's directory if not absolute
            if not os.path.isabs(self.agent_config_path):
                base_dir = os.path.dirname(os.path.abspath(__file__))
                config_file_path = os.path.join(base_dir, self.agent_config_path)
            else:
                config_file_path = self.agent_config_path

            if not os.path.exists(config_file_path):
                logger.error(f"Agent configuration file not found at {config_file_path}")
                raise SwarmError(f"Agent configuration file not found: {config_file_path}", ErrorCode.CONFIG_ERROR)

            with open(config_file_path, 'r') as f:
                agents_data = json.load(f)

            for agent_config_data in agents_data:
                # Convert capability dicts to AgentCapability objects
                cap_data_list = agent_config_data.pop("capabilities", [])
                capabilities = [AgentCapability(**cap_data) for cap_data in cap_data_list]

                # Ensure performance is handled correctly (it has a default factory now)
                performance_data = agent_config_data.pop("performance", None)

                agent = SwarmAgent(capabilities=capabilities, **agent_config_data)
                if performance_data: # If performance data was in JSON, update the default
                    agent.performance = AgentPerformanceMetrics(**performance_data)

                self.agents[agent.id] = agent

            logger.info(f"✅ Successfully loaded {len(self.agents)} agents from {config_file_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding agent configuration file {self.agent_config_path}: {e}")
            raise SwarmError(f"Invalid JSON in agent configuration: {e}", ErrorCode.CONFIG_ERROR)
        except FileNotFoundError:
            logger.error(f"Agent configuration file not found: {self.agent_config_path}")
            # This is already checked above, but as a safeguard
            raise SwarmError(f"Agent configuration file not found: {self.agent_config_path}", ErrorCode.CONFIG_ERROR)
        except Exception as e:
            logger.error(f"An unexpected error occurred during agent initialization: {e}")
            raise SwarmError(f"Failed to initialize agents: {str(e)}", ErrorCode.INITIALIZATION_ERROR)

    def _setup_services(self) -> None:
        """Initialize external services with proper error handling"""
        # This method can remain largely the same, just ensure keys are validated.
        try:
            # Validate API keys
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            if not openrouter_key or not validate_api_key(openrouter_key, 'OpenRouter'): # Assuming validate_api_key exists
                logger.warning("OpenRouter API key not configured or invalid.")
            else:
                logger.info("✅ OpenRouter API configured.")
            
            supermemory_key = os.getenv('SUPERMEMORY_API_KEY')
            if not supermemory_key or not validate_api_key(supermemory_key, 'Supermemory'):
                logger.warning("SuperMemory API key not configured or invalid.")
            else:
                logger.info("✅ SuperMemory API configured.")
            
            mailgun_key = os.getenv('MAILGUN_API_KEY')
            if not mailgun_key or not validate_api_key(mailgun_key, 'Mailgun'):
                logger.warning("Mailgun API key not configured or invalid.")
            else:
                logger.info("✅ Mailgun API configured.")
                
        except Exception as e: # Catch a more general exception if validate_api_key itself raises one
            logger.error(f"Error setting up services: {e}")

    def extract_mentions(self, message: str) -> List[str]:
        """
        Extracts @mentions (agent IDs or names) from a message.
        Returns a list of unique agent IDs.
        """
        # Regex to find @ followed by alphanumeric characters, underscores, or hyphens
        mentions = re.findall(r"@([a-zA-Z0-9_\-]+)", message)
        mentioned_agent_ids = set()

        for mention in mentions:
            # Check if the mention is a direct agent ID
            if mention in self.agents:
                mentioned_agent_ids.add(mention)
            else:
                # Check if the mention is an agent name (case-insensitive)
                for agent_id, agent_obj in self.agents.items():
                    if agent_obj.name.lower() == mention.lower():
                        mentioned_agent_ids.add(agent_id)
                        break # Found, no need to check other agents for this mention
        
        return list(mentioned_agent_ids)

    async def select_best_agent(self, task_description: str, required_capabilities: List[str] = None) -> Optional[SwarmAgent]:
        """
        Intelligently select the best agent for a given task.
        (This method might be less used if mentions or explicit IDs are primary)
        """
        if not self.agents:
            return None
        
        agent_scores = {}
        task_desc_lower = task_description.lower()

        for agent_id, agent in self.agents.items():
            if agent.status == "offline": # Assuming 'offline' is a possible status
                continue
            
            score = 0.0
            
            # Capability matching (name or tags)
            matched_cap_confidence = 0.0
            num_matched_caps = 0

            for cap in agent.capabilities:
                cap_match = False
                if required_capabilities and cap.name in required_capabilities:
                    cap_match = True

                # Also check capability tags against task_description keywords
                for tag in cap.tags:
                    if tag.lower() in task_desc_lower:
                        cap_match = True
                        break # Tag matched for this capability

                if cap_match:
                    matched_cap_confidence += cap.confidence_level
                    num_matched_caps +=1
            
            if num_matched_caps > 0:
                avg_confidence = matched_cap_confidence / num_matched_caps
                score += avg_confidence * 0.6 # Weight for capability match

            # Performance history
            score += (agent.performance.success_rate / 100.0) * 0.3 # Weight for success rate
            
            # Current load (prefer idle agents)
            if agent.status == "idle":
                score += 0.1 # Bonus for being idle
            
            agent_scores[agent_id] = score
        
        if not agent_scores:
            return None
        
        best_agent_id = max(agent_scores, key=agent_scores.get)
        logger.debug(f"Selected agent {best_agent_id} with score {agent_scores[best_agent_id]} for task: {task_description[:50]}...")
        return self.agents[best_agent_id]

    async def process_message(self, message: str, agent_ids: List[str] = None, 
                              conversation_id: str = None) -> List[Dict[str, Any]]:
        """
        Process a message through the swarm.
        If agent_ids is provided, uses those. Otherwise, extracts @mentions.
        If no agent_ids and no mentions, uses _auto_select_agents.
        """
        responses_payload = []
        
        targeted_agent_ids = set(agent_ids or [])

        if not targeted_agent_ids: # No specific agent_ids provided by caller
            extracted_ids = self.extract_mentions(message)
            if extracted_ids:
                targeted_agent_ids.update(extracted_ids)

        selected_agents_list: List[SwarmAgent] = []
        if targeted_agent_ids:
            selected_agents_list = [self.agents[aid] for aid in targeted_agent_ids if aid in self.agents]
            if not selected_agents_list:
                logger.warning(f"Provided/extracted agent_ids {targeted_agent_ids} not found or invalid.")
                return [{"error": "Specified agents not found.", "agent_id": list(targeted_agent_ids), "status": "failure"}]
        else:
            # Fallback to auto-select if no specific agents and no mentions
            # This could be a configurable behavior (e.g., error if no mentions/ids)
            auto_selected_agent = await self.select_best_agent(message) # select_best_agent returns one agent
            if auto_selected_agent:
                selected_agents_list = [auto_selected_agent]
            else:
                logger.warning("No suitable agents found for message via auto-selection.")
                return [{"error": "No suitable agents found.", "agent_id": None, "status": "failure"}]

        if not selected_agents_list:
             logger.warning("No agents selected to process the message.")
             return [{"error": "No agents available to process message.", "agent_id": None, "status": "failure"}]

        tasks = []
        for agent in selected_agents_list:
            # Use the retry-wrapped version here
            tasks.append(self._get_agent_response_with_retry(agent, message, conversation_id))

        # Run all agent responses concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result_or_exc in enumerate(results):
            agent = selected_agents_list[i]
            agent.performance.total_tasks += 1 # Increment total tasks for every attempt

            if isinstance(result_or_exc, Exception):
                logger.error(f"Error getting response from agent {agent.name} ({agent.id}): {result_or_exc}")
                responses_payload.append({
                    "agent_id": agent.id, "agent_name": agent.name,
                    "status": "failure", "error": str(result_or_exc)
                })
                # Note: successful_tasks is not incremented
            elif result_or_exc: # This is the dictionary from _get_agent_response_logic
                responses_payload.append({
                    "agent_id": agent.id, "agent_name": agent.name,
                    "status": "success", "response": result_or_exc
                })
                agent.performance.successful_tasks += 1
                agent.performance.last_active = datetime.now()
                # Average response time update is handled within _get_agent_response_logic
            else: # Agent returned None without an exception (should be rare if validation is good)
                logger.warning(f"Agent {agent.name} ({agent.id}) returned no content without exception.")
                responses_payload.append({
                    "agent_id": agent.id, "agent_name": agent.name,
                    "status": "failure", "error": "Agent returned no content."
                })
        
        return responses_payload

    async def _auto_select_agents(self, message: str) -> List[SwarmAgent]: # Kept for now, but select_best_agent is more targeted
        """Automatically select appropriate agents based on message content and capability tags."""
        message_lower = message.lower()
        selected_agent_ids = set()

        # Iterate through all agents and their capabilities
        for agent_id, agent in self.agents.items():
            if agent.status == "offline":
                continue
            for capability in agent.capabilities:
                for tag in capability.tags:
                    if tag.lower() in message_lower:
                        selected_agent_ids.add(agent_id)
                        break # Move to next capability or agent
                if agent_id in selected_agent_ids and any(tag.lower() in message_lower for tag in capability.tags):
                    break # Agent already added for a matching tag in another capability, move to next agent

        # Fallback logic (e.g., default agent) if no specific match
        if not selected_agent_ids and 'cathy' in self.agents: # Example: default to 'cathy'
            selected_agent_ids.add('cathy')
            logger.debug("No specific agent matched by tags, defaulting to Cathy.")
        
        return [self.agents[aid] for aid in selected_agent_ids if aid in self.agents]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10), # shorter min for quicker first retry
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError, SwarmError)) # SwarmError can be for specific API issues
    )
    async def _get_agent_response_with_retry(self, agent: SwarmAgent, message: str,
                                             conversation_id: str = None) -> Optional[Dict[str, Any]]:
        """Wrapper for _get_agent_response_logic to include retry logic."""
        return await self._get_agent_response_logic(agent, message, conversation_id)

    async def _get_agent_response_logic(self, agent: SwarmAgent, message: str,
                                        conversation_id: str = None) -> Optional[Dict[str, Any]]:
        """Actual logic to get response from a specific agent using OpenRouter API."""
        
        if not os.getenv('OPENROUTER_API_KEY'):
            logger.error("OPENROUTER_API_KEY not set.")
            raise SwarmError("OpenRouter API key not configured.", ErrorCode.API_KEY_MISSING)

        agent.status = "busy" # Consider making status updates more granular if needed
        start_time = datetime.now()
        
        try:
            system_prompt = f"""You are {agent.name}, a {agent.role}.
Personality: {agent.personality}
Capabilities: {', '.join([cap.name for cap in agent.capabilities])}
Respond in character, leveraging your specific expertise. Keep responses concise and informative."""

            headers = {
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("APP_URL", "http://localhost"), # Recommended by OpenRouter
                "X-Title": os.getenv("APP_TITLE", "SwarmMultiAgent") # Recommended
            }

            payload = {
                "model": agent.current_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                "max_tokens": 1024, # Increased max_tokens
                "temperature": 0.7
            }

            # Use a single session for multiple requests if possible, or manage per request
            async with aiohttp.ClientSession() as session:
                # Added timeout to the post request
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60.0) # 60 second timeout for the request
                ) as response:
                    
                    response_data_text = await response.text() # Read text first for better error logging
                    if response.status == 200:
                        try:
                            data = json.loads(response_data_text)
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON response from OpenRouter: {response_data_text}")
                            raise SwarmError("Malformed JSON response from AI service.", ErrorCode.API_ERROR)

                        # Validate response structure
                        if not (data and isinstance(data, dict) and
                                "choices" in data and isinstance(data["choices"], list) and data["choices"] and
                                isinstance(data["choices"][0], dict) and "message" in data["choices"][0] and
                                isinstance(data["choices"][0]["message"], dict) and
                                "content" in data["choices"][0]["message"]):
                            logger.error(f"Unexpected API response structure from OpenRouter: {data}")
                            raise SwarmError("Received malformed or incomplete response from AI service.", ErrorCode.API_ERROR)
                        
                        content = data['choices'][0]['message']['content']
                        
                        response_time_secs = (datetime.now() - start_time).total_seconds()
                        
                        # Update average response time (cumulative moving average)
                        # This should be done only on successful_tasks, handled in process_message
                        # For now, we calculate it here, but it's used if successful.
                        # agent.performance.average_response_time = (
                        #     (agent.performance.average_response_time * (agent.performance.successful_tasks -1) + response_time_secs) /
                        #     max(agent.performance.successful_tasks, 1) # Avoid division by zero if first successful task
                        # )
                        # Simpler: update total_tasks and successful_tasks in process_message, then recompute avg there if needed.
                        # OR, just store individual response_time here.

                        return {
                            'content': content,
                            'model_used': agent.current_model, # or data.get('model') if API returns it
                            'response_time_seconds': round(response_time_secs, 2),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"OpenRouter API error: {response.status} - {response_data_text}")
                        # Raise a SwarmError to be caught by tenacity for retries if applicable
                        raise SwarmError(f"OpenRouter API request failed with status {response.status}: {response_data_text[:200]}",
                                         ErrorCode.API_ERROR, status_code=response.status)
                        
        except aiohttp.ClientError as e: # Catch specific aiohttp client errors
            logger.error(f"HTTP Client error during OpenRouter request for agent {agent.name}: {e}")
            raise SwarmError(f"Network or HTTP error communicating with AI service: {str(e)}", ErrorCode.NETWORK_ERROR) from e
        except asyncio.TimeoutError as e: # Catch asyncio timeout specifically
            logger.error(f"Timeout during OpenRouter request for agent {agent.name}: {e}")
            raise SwarmError("AI service request timed out.", ErrorCode.TIMEOUT_ERROR) from e
        except Exception as e: # General fallback, should be rare
            logger.error(f"Unexpected error getting agent {agent.name} response: {e}")
            # Re-raise as SwarmError if not already one, so tenacity can handle it if configured
            if not isinstance(e, SwarmError):
                raise SwarmError(f"An unexpected error occurred while processing your request with agent {agent.name}.", ErrorCode.UNKNOWN_ERROR) from e
            raise
        finally:
            agent.status = "idle" # Ensure agent status is reset

    async def send_email(self, to_email: str, subject: str, body: str, 
                        agent_id: str = "cathy") -> bool: # Default agent_id for sending email
        """Send email through Mailgun API with agent context"""
        
        if not validate_email(to_email): # Assuming validate_email exists
            logger.error(f"Invalid email address provided: {to_email}")
            raise SwarmError("Invalid email address", ErrorCode.VALIDATION_ERROR)
        
        mailgun_api_key = os.getenv('MAILGUN_API_KEY')
        mailgun_domain = os.getenv('MAILGUN_DOMAIN')

        if not mailgun_api_key or not mailgun_domain:
            logger.error("Mailgun API key or domain not configured.")
            raise SwarmError("Email service not configured.", ErrorCode.API_KEY_MISSING)

        try:
            # Use default agent if specified one not found, or handle error
            agent = self.agents.get(agent_id)
            if not agent:
                logger.warning(f"Agent {agent_id} not found for sending email. Using default 'cathy'.")
                agent = self.agents.get('cathy') # Fallback to Cathy
                if not agent: # If Cathy also doesn't exist
                     raise SwarmError(f"Default sending agent 'cathy' not found.", ErrorCode.AGENT_NOT_FOUND)
            
            email_body = f"{body}\n\n---\nSent by {agent.name} ({agent.role})\nSwarm Multi-Agent System"
            
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                data.add_field('from', f'{agent.name} <mailgun@{mailgun_domain}>') # Mailgun recommends this format for "from"
                data.add_field('to', to_email)
                data.add_field('subject', subject)
                data.add_field('text', email_body)
                
                auth = aiohttp.BasicAuth('api', mailgun_api_key)
                
                # Added timeout
                async with session.post(
                    f'https://api.mailgun.net/v3/{mailgun_domain}/messages',
                    data=data,
                    auth=auth,
                    timeout=aiohttp.ClientTimeout(total=30.0) # 30s timeout for email
                ) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        logger.info(f"Email sent successfully to {to_email} via Mailgun.")
                        return True
                    else:
                        logger.error(f"Failed to send email via Mailgun: {response.status} - {response_text}")
                        raise SwarmError(f"Mailgun API error {response.status}: {response_text[:200]}", ErrorCode.EMAIL_SEND_FAILURE)
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP Client error sending email: {e}")
            raise SwarmError(f"Network error sending email: {str(e)}", ErrorCode.NETWORK_ERROR) from e
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout sending email: {e}")
            raise SwarmError("Email service request timed out.", ErrorCode.TIMEOUT_ERROR) from e
        except Exception as e: # Catch any other unexpected errors
            logger.error(f"Unexpected error sending email: {e}")
            if not isinstance(e, SwarmError):
                raise SwarmError(f"Failed to send email due to an unexpected error: {str(e)}", ErrorCode.UNKNOWN_ERROR) from e
            raise

    async def store_knowledge(self, content: str, tags: List[str] = None) -> bool:
        """Store knowledge in SuperMemory system (if configured)"""
        supermemory_api_key = os.getenv('SUPERMEMORY_API_KEY')
        supermemory_base_url = os.getenv('SUPERMEMORY_BASE_URL') # e.g., http://localhost:8000

        if not supermemory_api_key or not supermemory_base_url:
            logger.warning("SuperMemory API key or base URL not configured. Skipping knowledge storage.")
            return False

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {supermemory_api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "content": content,
                    "metadata": { # SuperMemory often uses a metadata field
                        "tags": tags or [],
                        "source": "swarm_agents",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                # Added timeout
                async with session.post(
                    f"{supermemory_base_url.rstrip('/')}/api/memories", # Ensure no double slashes
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30.0)
                ) as response:
                    response_text = await response.text()
                    if response.status in [200, 201]: # Typically 201 Created or 200 OK
                        logger.info("Knowledge stored successfully in SuperMemory.")
                        return True
                    else:
                        logger.error(f"Failed to store knowledge in SuperMemory: {response.status} - {response_text}")
                        # Do not raise SwarmError here to make it non-blocking for main flow, just log and return False
                        return False
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP Client error storing knowledge: {e}")
            return False # Non-critical failure
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout storing knowledge: {e}")
            return False # Non-critical failure
        except Exception as e:
            logger.error(f"Unexpected error storing knowledge: {e}")
            return False # Non-critical failure

    async def search_knowledge(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search knowledge in SuperMemory system (if configured)"""
        supermemory_api_key = os.getenv('SUPERMEMORY_API_KEY')
        supermemory_base_url = os.getenv('SUPERMEMORY_BASE_URL')

        if not supermemory_api_key or not supermemory_base_url:
            logger.warning("SuperMemory API key or base URL not configured. Skipping knowledge search.")
            return []

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {supermemory_api_key}",
                    "Content-Type": "application/json"
                }
                
                params = { # SuperMemory search might use a JSON body or query params
                    "query": query,
                    "limit": limit
                }
                
                # Added timeout
                async with session.post( # Often search is a POST if query is complex or has filters
                    f"{supermemory_base_url.rstrip('/')}/api/memories/search", # Common endpoint pattern
                    headers=headers,
                    json=params, # Sending query in JSON body
                    timeout=aiohttp.ClientTimeout(total=30.0)
                ) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        try:
                            data = json.loads(response_text)
                            return data.get('results', data.get('memories', [])) # Common result keys
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON from SuperMemory search: {response_text}")
                            return []
                    else:
                        logger.error(f"Failed to search knowledge in SuperMemory: {response.status} - {response_text}")
                        return []
                        
        except aiohttp.ClientError as e:
            logger.error(f"HTTP Client error searching knowledge: {e}")
            return []
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout searching knowledge: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching knowledge: {e}")
            return []

    def get_agent_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            logger.warning(f"Attempted to get performance for non-existent agent: {agent_id}")
            return None
        
        # Ensure performance data is serializable
        perf_data = asdict(agent.performance)
        perf_data['success_rate'] = agent.performance.success_rate # Add property value

        return {
            'agent_id': agent.id, # Use agent.id for consistency
            'agent_name': agent.name,
            'performance': perf_data,
            'status': agent.status,
            'current_model': agent.current_model
        }
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status and metrics"""
        # Filter out agents that might not have performance initialized if loading failed partially
        valid_agents = [agent for agent in self.agents.values() if hasattr(agent, 'performance')]
        
        total_tasks = sum(agent.performance.total_tasks for agent in valid_agents)
        total_successful = sum(agent.performance.successful_tasks for agent in valid_agents)

        active_agents_count = len([a for a in valid_agents if a.status != "offline" and a.status != "error"]) # Define what "active" means

        return {
            'total_agents': len(self.agents), # Total configured agents
            'active_agents': active_agents_count,
            'total_tasks_processed': total_tasks,
            'overall_success_rate': (total_successful / max(total_tasks, 1)) * 100, # Avoid division by zero
            'agents_summary': [ # Provide a summary, not full agent dicts if too verbose
                {
                    "id": agent.id, "name": agent.name, "status": agent.status,
                    "total_tasks": agent.performance.total_tasks,
                    "success_rate": agent.performance.success_rate
                } for agent in valid_agents
            ]
        }
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents, ensuring data is serializable."""
        return [agent.to_dict() for agent in self.agents.values()]
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get specific agent configuration, ensuring data is serializable."""
        agent = self.agents.get(agent_id)
        if agent:
            return agent.to_dict()
        logger.warning(f"Agent config requested for non-existent agent: {agent_id}")
        return None
    
    def get_status(self) -> Dict[str, Any]: # Alias for get_swarm_status for compatibility
        """Get overall swarm status for testing compatibility"""
        return self.get_swarm_status()

# Global orchestrator instance
# Consider initializing this within the Flask app factory or a similar setup
# to allow passing configuration like agent_config_path easily.
# For now, keeping global initialization but making config path a parameter.
orchestrator_instance_config_path = os.getenv("AGENT_CONFIG_PATH", "agents_config.json")
orchestrator = SwarmOrchestrator(agent_config_path=orchestrator_instance_config_path)

def get_orchestrator() -> SwarmOrchestrator:
    """Returns the global orchestrator instance."""
    global orchestrator
    if orchestrator is None: # Should not happen with current setup but good practice
        logger.warning("Orchestrator accessed before initialization. Re-initializing with default path.")
        orchestrator = SwarmOrchestrator()
    return orchestrator

