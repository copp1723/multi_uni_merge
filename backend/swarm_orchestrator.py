# 🤖 SWARM AGENT ORCHESTRATION SYSTEM - CLEANED & REFACTORED

import os
import json
import asyncio
import aiohttp
import aiofiles
import smtplib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
    
@dataclass
class AgentPerformanceMetrics:
    """Tracks agent performance metrics"""
    total_tasks: int = 0
    successful_tasks: int = 0
    average_response_time: float = 0.0
    last_active: Optional[datetime] = None
    confidence_score: float = 0.8
    
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
    status: str = "idle"
    current_model: str = "gpt-4"
    collaboration_style: str = "coordinator"
    performance: AgentPerformanceMetrics = None
    
    def __post_init__(self):
        if self.performance is None:
            self.performance = AgentPerformanceMetrics()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'personality': self.personality,
            'capabilities': [asdict(cap) for cap in self.capabilities],
            'status': self.status,
            'current_model': self.current_model,
            'collaboration_style': self.collaboration_style,
            'performance': asdict(self.performance)
        }

class SwarmOrchestrator:
    """
    Enhanced Swarm Intelligence Orchestration System
    
    Manages multiple AI agents with sophisticated coordination,
    performance tracking, and intelligent task distribution.
    """
    
    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.active_conversations: Dict[str, Dict] = {}
        self.task_queue: List[Dict] = []
        self.performance_history: List[Dict] = []
        
        # Initialize services
        self._initialize_agents()
        self._setup_services()
        
        logger.info("🤖 Swarm Agent Orchestration System initialized")
        logger.info(f"🚀 {len(self.agents)} agents ready for deployment")
    
    def _initialize_agents(self) -> None:
        """Initialize the enhanced agent swarm with Communication Agent and improved capabilities"""
        
        # Communication Agent - NEW
        comms_capabilities = [
            AgentCapability("text_transformation", "Transform text into clear, professional communication", 0.95, 15),
            AgentCapability("tone_matching", "Match and maintain user's authentic communication style", 0.92, 10),
            AgentCapability("business_writing", "Create compelling business content with storytelling", 0.90, 25),
            AgentCapability("linkedin_optimization", "Optimize content for LinkedIn engagement", 0.88, 20),
            AgentCapability("message_clarity", "Improve clarity while maintaining authenticity", 0.93, 12)
        ]
        
        # Cathy - Personal Assistant (Enhanced)
        cathy_capabilities = [
            AgentCapability("email_management", "Send, read, and organize emails with professional tone", 0.95, 30),
            AgentCapability("task_scheduling", "Schedule and manage tasks with realistic timelines", 0.90, 15),
            AgentCapability("calendar_management", "Manage calendar events and time optimization", 0.85, 20),
            AgentCapability("document_organization", "Organize and categorize documents systematically", 0.80, 45),
            AgentCapability("communication_coordination", "Coordinate communications across platforms", 0.88, 25)
        ]
        
        # DataMiner - Data Analysis Specialist (Enhanced)
        dataminer_capabilities = [
            AgentCapability("data_analysis", "Analyze datasets and generate actionable business insights", 0.95, 120),
            AgentCapability("visualization", "Create compelling charts and executive dashboards", 0.90, 60),
            AgentCapability("statistical_modeling", "Build predictive models with confidence intervals", 0.85, 180),
            AgentCapability("report_generation", "Generate executive-ready analytical reports", 0.88, 90),
            AgentCapability("business_intelligence", "Transform data into strategic recommendations", 0.87, 75)
        ]
        
        # Coder - Software Development Expert (Enhanced)
        coder_capabilities = [
            AgentCapability("code_review", "Review code quality with best practices focus", 0.92, 45),
            AgentCapability("debugging", "Systematically identify and resolve technical issues", 0.88, 60),
            AgentCapability("architecture_design", "Design scalable and maintainable systems", 0.85, 120),
            AgentCapability("documentation", "Write clear technical documentation and guides", 0.90, 30),
            AgentCapability("performance_optimization", "Optimize code for efficiency and scalability", 0.83, 90)
        ]
        
        # Creative - Content Creation Specialist (Enhanced)
        creative_capabilities = [
            AgentCapability("content_writing", "Create engaging content across multiple formats", 0.90, 45),
            AgentCapability("brainstorming", "Generate innovative ideas and creative solutions", 0.95, 20),
            AgentCapability("design_concepts", "Develop visual and conceptual design approaches", 0.80, 60),
            AgentCapability("storytelling", "Craft compelling narratives that drive engagement", 0.88, 40),
            AgentCapability("brand_voice", "Maintain consistent brand voice and messaging", 0.85, 30)
        ]
        
        # Researcher - Information Gathering Expert (Enhanced)
        researcher_capabilities = [
            AgentCapability("web_research", "Conduct comprehensive and targeted research", 0.92, 90),
            AgentCapability("fact_checking", "Verify information accuracy with source validation", 0.95, 30),
            AgentCapability("synthesis", "Synthesize information into coherent insights", 0.88, 60),
            AgentCapability("citation_management", "Manage and format citations properly", 0.85, 25),
            AgentCapability("competitive_analysis", "Analyze market trends and competitive landscape", 0.87, 105)
        ]
        
        # Create enhanced agent instances
        agents_config = [
            {
                'id': 'comms', 'name': 'Communication Agent', 'role': 'Communication Specialist',
                'personality': 'Professional yet approachable, action-oriented, and authentic. Understands business context and storytelling.',
                'capabilities': comms_capabilities, 'collaboration_style': 'specialist'
            },
            {
                'id': 'cathy', 'name': 'Cathy', 'role': 'Personal Assistant',
                'personality': 'Helpful, organized, and proactive. Excellent at managing tasks and communications with efficiency.',
                'capabilities': cathy_capabilities, 'collaboration_style': 'coordinator'
            },
            {
                'id': 'dataminer', 'name': 'DataMiner', 'role': 'Data Analysis Specialist',
                'personality': 'Analytical, detail-oriented, and methodical. Transforms data into actionable business insights.',
                'capabilities': dataminer_capabilities, 'collaboration_style': 'specialist'
            },
            {
                'id': 'coder', 'name': 'Coder', 'role': 'Software Development Expert',
                'personality': 'Logical, precise, and solution-focused. Passionate about clean, efficient, maintainable code.',
                'capabilities': coder_capabilities, 'collaboration_style': 'implementer'
            },
            {
                'id': 'creative', 'name': 'Creative', 'role': 'Content Creation Specialist',
                'personality': 'Imaginative, expressive, and innovative. Creates compelling narratives that drive engagement.',
                'capabilities': creative_capabilities, 'collaboration_style': 'ideator'
            },
            {
                'id': 'researcher', 'name': 'Researcher', 'role': 'Information Gathering Expert',
                'personality': 'Curious, thorough, and objective. Dedicated to finding accurate, well-sourced information.',
                'capabilities': researcher_capabilities, 'collaboration_style': 'investigator'
            }
        ]
        
        for agent_config in agents_config:
            agent = SwarmAgent(**agent_config)
            self.agents[agent.id] = agent
        
        logger.info(f"✅ Initialized {len(self.agents)} enhanced agents including Communication Agent")
    
    def _setup_services(self) -> None:
        """Initialize external services with proper error handling"""
        try:
            # Validate API keys
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            if not openrouter_key or not validate_api_key(openrouter_key, 'OpenRouter'):
                logger.warning("OpenRouter API key not configured")
            else:
                logger.info("✅ OpenRouter API configured")
            
            supermemory_key = os.getenv('SUPERMEMORY_API_KEY')
            if not supermemory_key or not validate_api_key(supermemory_key, 'Supermemory'):
                logger.warning("SuperMemory API key not configured")
            else:
                logger.info("✅ SuperMemory API configured")
            
            mailgun_key = os.getenv('MAILGUN_API_KEY')
            if not mailgun_key or not validate_api_key(mailgun_key, 'Mailgun'):
                logger.warning("Mailgun API key not configured")
            else:
                logger.info("✅ Mailgun API configured")
                
        except Exception as e:
            logger.error(f"Error setting up services: {e}")
    
    async def select_best_agent(self, task_description: str, required_capabilities: List[str] = None) -> Optional[SwarmAgent]:
        """
        Intelligently select the best agent for a given task
        
        Args:
            task_description: Description of the task
            required_capabilities: List of required capability names
            
        Returns:
            Best suited agent or None if no suitable agent found
        """
        if not self.agents:
            return None
        
        # Score agents based on capabilities and performance
        agent_scores = {}
        
        for agent_id, agent in self.agents.items():
            if agent.status == "offline":
                continue
            
            score = 0.0
            
            # Capability matching
            if required_capabilities:
                matching_caps = [cap for cap in agent.capabilities 
                               if cap.name in required_capabilities]
                if matching_caps:
                    avg_confidence = sum(cap.confidence_level for cap in matching_caps) / len(matching_caps)
                    score += avg_confidence * 0.6
            
            # Performance history
            score += (agent.performance.success_rate / 100) * 0.3
            
            # Current load (prefer less busy agents)
            if agent.status == "idle":
                score += 0.1
            
            agent_scores[agent_id] = score
        
        if not agent_scores:
            return None
        
        # Select agent with highest score
        best_agent_id = max(agent_scores, key=agent_scores.get)
        return self.agents[best_agent_id]
    
    async def process_message(self, message: str, agent_ids: List[str] = None, 
                            conversation_id: str = None) -> List[Dict[str, Any]]:
        """
        Process a message through the swarm with enhanced coordination
        
        Args:
            message: The message to process
            agent_ids: Specific agents to involve (optional)
            conversation_id: Conversation identifier
            
        Returns:
            List of agent responses
        """
        responses = []
        
        try:
            # Determine which agents to involve
            if agent_ids:
                selected_agents = [self.agents[aid] for aid in agent_ids if aid in self.agents]
            else:
                # Auto-select based on message content
                selected_agents = await self._auto_select_agents(message)
            
            if not selected_agents:
                logger.warning("No suitable agents found for message")
                return responses
            
            # Process message through each selected agent
            for agent in selected_agents:
                try:
                    response = await self._get_agent_response(agent, message, conversation_id)
                    if response:
                        responses.append(response)
                        
                        # Update agent performance
                        agent.performance.total_tasks += 1
                        agent.performance.successful_tasks += 1
                        agent.performance.last_active = datetime.now()
                        
                except Exception as e:
                    logger.error(f"Error getting response from agent {agent.name}: {e}")
                    agent.performance.total_tasks += 1
                    # Don't increment successful_tasks for failed attempts
            
            return responses
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise SwarmError(f"Failed to process message: {str(e)}")
    
    async def _auto_select_agents(self, message: str) -> List[SwarmAgent]:
        """Automatically select appropriate agents based on message content"""
        # Simple keyword-based selection (can be enhanced with ML)
        keywords_to_agents = {
            'email': ['cathy'],
            'schedule': ['cathy'],
            'data': ['dataminer'],
            'analyze': ['dataminer'],
            'code': ['coder'],
            'program': ['coder'],
            'creative': ['creative'],
            'write': ['creative'],
            'research': ['researcher'],
            'find': ['researcher']
        }
        
        message_lower = message.lower()
        selected_agent_ids = set()
        
        for keyword, agent_ids in keywords_to_agents.items():
            if keyword in message_lower:
                selected_agent_ids.update(agent_ids)
        
        # Default to Cathy if no specific match
        if not selected_agent_ids:
            selected_agent_ids.add('cathy')
        
        return [self.agents[aid] for aid in selected_agent_ids if aid in self.agents]
    
    
    async def _get_agent_response(self, agent: SwarmAgent, message: str, 
                                conversation_id: str = None) -> Optional[Dict[str, Any]]:
        """Get response from a specific agent using OpenRouter API"""
        
        # Update agent status
        agent.status = "busy"
        start_time = datetime.now()
        
        try:
            # Prepare the prompt with agent personality
            system_prompt = f"""You are {agent.name}, a {agent.role}.
            
Personality: {agent.personality}

Capabilities: {', '.join([cap.name for cap in agent.capabilities])}

Respond in character, being helpful and leveraging your specific expertise.
Keep responses concise but informative."""

            # Make API call to OpenRouter
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": agent.current_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }
                
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data['choices'][0]['message']['content']
                        
                        # Calculate response time
                        response_time = (datetime.now() - start_time).total_seconds()
                        
                        # Update performance metrics
                        agent.performance.average_response_time = (
                            (agent.performance.average_response_time * (agent.performance.total_tasks - 1) + response_time) /
                            agent.performance.total_tasks
                        )
                        
                        return {
                            'agent_id': agent.id,
                            'agent_name': agent.name,
                            'content': content,
                            'model_used': agent.current_model,
                            'response_time': response_time,
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        logger.error(f"OpenRouter API error: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting agent response: {e}")
            return None
        finally:
            agent.status = "idle"
    
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        agent_id: str = "cathy") -> bool:
        """Send email through Mailgun API with agent context"""
        
        if not validate_email(to_email):
            raise SwarmError("Invalid email address")
        
        try:
            agent = self.agents.get(agent_id, self.agents['cathy'])
            
            # Add agent signature to email
            email_body = f"{body}\n\n---\nSent by {agent.name} ({agent.role})\nSwarm Multi-Agent System"
            
            async with aiohttp.ClientSession() as session:
                data = aiohttp.FormData()
                mailgun_domain = os.getenv('MAILGUN_DOMAIN', 'example.com')
                data.add_field('from', f'{agent.name} <noreply@{mailgun_domain}>')
                data.add_field('to', to_email)
                data.add_field('subject', subject)
                data.add_field('text', email_body)
                
                auth = aiohttp.BasicAuth('api', os.getenv('MAILGUN_API_KEY'))
                
                async with session.post(
                    f'https://api.mailgun.net/v3/{mailgun_domain}/messages',
                    data=data,
                    auth=auth
                ) as response:
                    
                    if response.status == 200:
                        logger.info(f"Email sent successfully to {to_email}")
                        return True
                    else:
                        logger.error(f"Failed to send email: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise SwarmError(f"Failed to send email: {str(e)}")
    
    
    async def store_knowledge(self, content: str, tags: List[str] = None) -> bool:
        """Store knowledge in SuperMemory system"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.getenv('SUPERMEMORY_API_KEY')}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "content": content,
                    "tags": tags or [],
                    "timestamp": datetime.now().isoformat(),
                    "source": "swarm_agents"
                }
                
                async with session.post(
                    f"{os.getenv('SUPERMEMORY_BASE_URL', 'http://localhost:8080')}/api/memories",
                    headers=headers,
                    json=payload
                ) as response:
                    
                    if response.status in [200, 201]:
                        logger.info("Knowledge stored successfully")
                        return True
                    else:
                        logger.error(f"Failed to store knowledge: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            return False
    
    
    async def search_knowledge(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search knowledge in SuperMemory system"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {os.getenv('SUPERMEMORY_API_KEY')}",
                    "Content-Type": "application/json"
                }
                
                params = {
                    "query": query,
                    "limit": limit
                }
                
                async with session.get(
                    f"{os.getenv('SUPERMEMORY_BASE_URL', 'http://localhost:8080')}/api/memories/search",
                    headers=headers,
                    params=params
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        return data.get('memories', [])
                    else:
                        logger.error(f"Failed to search knowledge: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []
    
    def get_agent_performance(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get performance metrics for a specific agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        return {
            'agent_id': agent_id,
            'agent_name': agent.name,
            'performance': asdict(agent.performance),
            'status': agent.status,
            'current_model': agent.current_model
        }
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get overall swarm status and metrics"""
        total_tasks = sum(agent.performance.total_tasks for agent in self.agents.values())
        total_successful = sum(agent.performance.successful_tasks for agent in self.agents.values())
        
        return {
            'total_agents': len(self.agents),
            'active_agents': len([a for a in self.agents.values() if a.status != "offline"]),
            'total_tasks_processed': total_tasks,
            'overall_success_rate': (total_successful / max(total_tasks, 1)) * 100,
            'agents': [agent.to_dict() for agent in self.agents.values()]
        }
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents for testing compatibility"""
        return [agent.to_dict() for agent in self.agents.values()]
    
    def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent configuration for testing compatibility"""
        if agent_id in self.agents:
            return self.agents[agent_id].to_dict()
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status for testing compatibility"""
        return self.get_swarm_status()

# Global orchestrator instance
orchestrator = SwarmOrchestrator()

