"""
Multi-Agent System - Clean Architecture
Core Features: MCP Filesystem, Multi-Agent Orchestration, 1v1 Chat, OpenRouter, Supermemory
NO WEBSOCKETS - Simple HTTP API only for reliability
"""

import os
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global storage for simplicity (will be replaced with proper DB later)
agents_store = {}
conversations_store = {}
memory_store = {}

def create_app():
    """Create Flask application with core functionality"""
    app = Flask(__name__)
    CORS(app)
    
    # Initialize default agents
    initialize_default_agents()
    
    # Clean, functional UI template
    HTML_TEMPLATE = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Multi-Agent System</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #f8fafc; 
                color: #1a202c;
            }
            .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
            .header { 
                background: white; 
                padding: 24px; 
                border-radius: 12px; 
                margin-bottom: 24px; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
            }
            .header h1 { color: #2d3748; margin-bottom: 8px; }
            .header p { color: #718096; }
            
            .main-grid { display: grid; grid-template-columns: 300px 1fr; gap: 24px; }
            
            .agents-panel { 
                background: white; 
                padding: 20px; 
                border-radius: 12px; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
                height: fit-content;
            }
            .agents-panel h3 { margin-bottom: 16px; color: #2d3748; }
            
            .agent-card { 
                padding: 16px; 
                border: 1px solid #e2e8f0; 
                border-radius: 8px; 
                margin-bottom: 12px; 
                cursor: pointer;
                transition: all 0.2s;
            }
            .agent-card:hover { border-color: #3182ce; background: #f7fafc; }
            .agent-card.active { border-color: #3182ce; background: #ebf8ff; }
            .agent-card h4 { color: #2d3748; margin-bottom: 4px; }
            .agent-card p { color: #718096; font-size: 14px; margin-bottom: 8px; }
            .agent-status { 
                display: inline-block; 
                padding: 2px 8px; 
                border-radius: 12px; 
                font-size: 12px; 
                font-weight: 500;
            }
            .status-online { background: #c6f6d5; color: #22543d; }
            .status-offline { background: #fed7d7; color: #742a2a; }
            
            .chat-panel { 
                background: white; 
                border-radius: 12px; 
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                border: 1px solid #e2e8f0;
                display: flex;
                flex-direction: column;
                height: 600px;
            }
            .chat-header { 
                padding: 20px; 
                border-bottom: 1px solid #e2e8f0; 
                background: #f8fafc;
                border-radius: 12px 12px 0 0;
            }
            .chat-header h3 { color: #2d3748; }
            
            .messages-container { 
                flex: 1; 
                overflow-y: auto; 
                padding: 20px; 
                background: white;
            }
            .message { 
                margin-bottom: 16px; 
                padding: 12px 16px; 
                border-radius: 8px; 
                max-width: 80%;
            }
            .message.user { 
                background: #3182ce; 
                color: white; 
                margin-left: auto; 
                text-align: right;
            }
            .message.agent { 
                background: #f7fafc; 
                border: 1px solid #e2e8f0;
            }
            .message-meta { 
                font-size: 12px; 
                opacity: 0.7; 
                margin-bottom: 4px; 
            }
            
            .chat-input { 
                padding: 20px; 
                border-top: 1px solid #e2e8f0; 
                background: #f8fafc;
                border-radius: 0 0 12px 12px;
            }
            .input-group { display: flex; gap: 12px; align-items: center; }
            .input-group input { 
                flex: 1; 
                padding: 12px 16px; 
                border: 1px solid #e2e8f0; 
                border-radius: 8px; 
                font-size: 14px;
            }
            .input-group input:focus { 
                outline: none; 
                border-color: #3182ce; 
                box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
            }
            .btn { 
                padding: 12px 24px; 
                background: #3182ce; 
                color: white; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-weight: 500;
                transition: background 0.2s;
            }
            .btn:hover { background: #2c5aa0; }
            .btn:disabled { background: #a0aec0; cursor: not-allowed; }
            
            .empty-state { 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                height: 100%; 
                color: #718096; 
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Multi-Agent System</h1>
                <p>MCP Filesystem • Multi-Agent Orchestration • 1v1 Chat • OpenRouter • Supermemory</p>
            </div>
            
            <div class="main-grid">
                <div class="agents-panel">
                    <h3>Available Agents</h3>
                    <div id="agents-list">
                        <!-- Agents will be loaded here -->
                    </div>
                </div>
                
                <div class="chat-panel">
                    <div class="chat-header">
                        <h3 id="chat-title">Select an agent to start chatting</h3>
                    </div>
                    
                    <div class="messages-container" id="messages-container">
                        <div class="empty-state">
                            <div>
                                <h4>Welcome to Multi-Agent System</h4>
                                <p>Select an agent from the left panel to start a conversation</p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="chat-input">
                        <div class="input-group">
                            <input type="text" id="message-input" placeholder="Type your message..." disabled>
                            <button class="btn" id="send-btn" onclick="sendMessage()" disabled>Send</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let currentAgent = null;
            let agents = {};

            // Load agents on page load
            async function loadAgents() {
                try {
                    const response = await fetch('/api/agents');
                    agents = await response.json();
                    renderAgents();
                } catch (error) {
                    console.error('Error loading agents:', error);
                }
            }

            function renderAgents() {
                const container = document.getElementById('agents-list');
                container.innerHTML = Object.entries(agents).map(([id, agent]) => `
                    <div class="agent-card" onclick="selectAgent('${id}')">
                        <h4>${agent.name}</h4>
                        <p>${agent.description}</p>
                        <span class="agent-status status-${agent.status}">${agent.status}</span>
                    </div>
                `).join('');
            }

            function selectAgent(agentId) {
                currentAgent = agentId;
                
                // Update UI
                document.querySelectorAll('.agent-card').forEach(card => card.classList.remove('active'));
                event.target.closest('.agent-card').classList.add('active');
                
                document.getElementById('chat-title').textContent = `Chat with ${agents[agentId].name}`;
                document.getElementById('message-input').disabled = false;
                document.getElementById('send-btn').disabled = false;
                
                loadMessages();
            }

            async function loadMessages() {
                if (!currentAgent) return;
                
                try {
                    const response = await fetch(`/api/conversations/${currentAgent}`);
                    const messages = await response.json();
                    renderMessages(messages);
                } catch (error) {
                    console.error('Error loading messages:', error);
                }
            }

            function renderMessages(messages) {
                const container = document.getElementById('messages-container');
                
                if (messages.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <div>
                                <h4>Start a conversation</h4>
                                <p>Send a message to ${agents[currentAgent].name}</p>
                            </div>
                        </div>
                    `;
                    return;
                }
                
                container.innerHTML = messages.map(msg => `
                    <div class="message ${msg.role}">
                        <div class="message-meta">${msg.role} • ${new Date(msg.timestamp).toLocaleTimeString()}</div>
                        <div>${msg.content}</div>
                    </div>
                `).join('');
                
                container.scrollTop = container.scrollHeight;
            }

            async function sendMessage() {
                const input = document.getElementById('message-input');
                const message = input.value.trim();
                
                if (!message || !currentAgent) return;
                
                const sendBtn = document.getElementById('send-btn');
                sendBtn.disabled = true;
                sendBtn.textContent = 'Sending...';
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ 
                            agent_id: currentAgent, 
                            message: message 
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        input.value = '';
                        loadMessages();
                    } else {
                        alert('Error: ' + result.error);
                    }
                } catch (error) {
                    console.error('Error sending message:', error);
                    alert('Failed to send message');
                } finally {
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                }
            }

            // Handle Enter key in input
            document.getElementById('message-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });

            // Initialize
            loadAgents();
        </script>
    </body>
    </html>
    """
    
    @app.route('/')
    def index():
        """Serve the main UI"""
        return render_template_string(HTML_TEMPLATE)
    
    @app.route('/api/agents')
    def get_agents():
        """Get all available agents"""
        return jsonify(agents_store)
    
    @app.route('/api/conversations/<agent_id>')
    def get_conversation(agent_id):
        """Get conversation history with an agent"""
        if agent_id not in conversations_store:
            conversations_store[agent_id] = []
        return jsonify(conversations_store[agent_id])
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Send message to agent and get response"""
        try:
            data = request.json
            agent_id = data.get('agent_id')
            message = data.get('message')
            
            if not agent_id or not message:
                return jsonify({"success": False, "error": "Missing agent_id or message"}), 400
            
            if agent_id not in agents_store:
                return jsonify({"success": False, "error": "Agent not found"}), 404
            
            # Initialize conversation if needed
            if agent_id not in conversations_store:
                conversations_store[agent_id] = []
            
            # Add user message
            user_msg = {
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            }
            conversations_store[agent_id].append(user_msg)
            
            # Generate agent response (mock for now - will integrate OpenRouter)
            agent_response = generate_agent_response(agent_id, message)
            
            agent_msg = {
                "role": "agent",
                "content": agent_response,
                "timestamp": datetime.now().isoformat()
            }
            conversations_store[agent_id].append(agent_msg)
            
            # Store in memory (Supermemory integration point)
            store_in_memory(agent_id, user_msg, agent_msg)
            
            return jsonify({"success": True, "response": agent_response})
            
        except Exception as e:
            logger.error(f"Error in chat endpoint: {e}")
            return jsonify({"success": False, "error": str(e)}), 500
    
    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "agents": len(agents_store),
                "conversations": len(conversations_store),
                "memory_entries": len(memory_store)
            }
        })
    
    @app.route('/api/filesystem/<path:file_path>')
    def filesystem_access(file_path):
        """MCP Filesystem access endpoint"""
        # This will integrate with the MCP filesystem service
        return jsonify({
            "path": file_path,
            "status": "MCP filesystem integration pending",
            "message": "This endpoint will provide secure file access via MCP"
        })
    
    return app

def initialize_default_agents():
    """Initialize default agents"""
    global agents_store
    agents_store = {
        "research_agent": {
            "name": "Research Agent",
            "description": "Specializes in research, data gathering, and analysis",
            "status": "online",
            "model": "gpt-4",
            "capabilities": ["research", "analysis", "web_search", "data_processing"]
        },
        "code_agent": {
            "name": "Code Agent", 
            "description": "Expert in programming, debugging, and technical solutions",
            "status": "online",
            "model": "claude-3-sonnet",
            "capabilities": ["coding", "debugging", "architecture", "code_review"]
        },
        "writing_agent": {
            "name": "Writing Agent",
            "description": "Handles content creation, editing, and communication",
            "status": "online", 
            "model": "gpt-3.5-turbo",
            "capabilities": ["writing", "editing", "communication", "content_creation"]
        }
    }

def generate_agent_response(agent_id, message):
    """Generate agent response (will integrate with OpenRouter)"""
    agent = agents_store.get(agent_id, {})
    agent_name = agent.get("name", "Agent")
    
    # Mock responses based on agent type
    if "research" in agent_id:
        return f"As the Research Agent, I'll help you investigate '{message}'. I can access various data sources and provide comprehensive analysis. This response will be powered by OpenRouter API integration."
    elif "code" in agent_id:
        return f"As the Code Agent, I can assist with '{message}'. I specialize in programming solutions and technical implementation. OpenRouter integration will provide advanced coding capabilities."
    elif "writing" in agent_id:
        return f"As the Writing Agent, I'll help you with '{message}'. I can create, edit, and refine content to meet your needs. Enhanced by OpenRouter's language models."
    else:
        return f"Hello! I'm {agent_name}. I received your message: '{message}'. I'm ready to help you with my specialized capabilities."

def store_in_memory(agent_id, user_msg, agent_msg):
    """Store conversation in memory (Supermemory integration point)"""
    global memory_store
    
    memory_key = f"{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    memory_store[memory_key] = {
        "agent_id": agent_id,
        "user_message": user_msg,
        "agent_response": agent_msg,
        "timestamp": datetime.now().isoformat(),
        "context": "1v1_chat"
    }

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Multi-Agent System on {host}:{port}")
    app.run(host=host, port=port, debug=debug)

