import React, { useState, useEffect, useRef } from 'react'; // Added useRef
import { 
  Layers, Settings, Cpu, CheckCircle, AlertTriangle, 
  MessageSquare, Mail, Code, Calendar, Wrench, Smile,
  ChevronDown, Sun, Send, Users // Added Users icon for swarm
} from 'lucide-react';
import io from 'socket.io-client'; // Import socket.io-client

// Dynamically determine API URL and WebSocket URL
const API_BASE_URL = (() => {
  if (import.meta.env.VITE_API_URL) return import.meta.env.VITE_API_URL;
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') return window.location.origin;
  return 'http://localhost:5000';
})();

const WEBSOCKET_URL = (() => {
  if (import.meta.env.VITE_WEBSOCKET_URL) return import.meta.env.VITE_WEBSOCKET_URL;
  // For WebSocket, derive from API_BASE_URL if not explicitly set
  // This assumes WebSocket is served from the same host/port as API, adjust if different
  const url = new URL(API_BASE_URL);
  const protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${url.host}`;
})();


function App() {
  // Core State
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null); // Can be an agent object or a special "swarm" identifier
  const [message, setMessage] = useState('');
  const [chatMessages, setChatMessages] = useState([]); // To store and display chat messages
  const [notifications, setNotifications] = useState([]);
  const [selectedModel, setSelectedModel] = useState('anthropic/claude-3.5-sonnet'); // Default model
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [modelOptions, setModelOptions] = useState([]); // Loaded from API
  const [transformText, setTransformText] = useState('');
  const [isTransforming, setIsTransforming] = useState(false);
  const [socket, setSocket] = useState(null); // WebSocket instance
  const [currentConversationId, setCurrentConversationId] = useState(null); // For swarm messages

  const chatEndRef = useRef(null); // For scrolling to the bottom of chat

  // --- Effects ---
  useEffect(() => { // Load initial data
    loadAgents();
    loadModels();
  }, []);

  useEffect(() => { // WebSocket Connection Setup
    // Placeholder for authentication token - replace with actual auth logic
    const authToken = "your_jwt_token_or_api_key"; // Replace with actual token retrieval

    // Connect to WebSocket server, namespace /swarm
    const newSocket = io(`${WEBSOCKET_URL}/swarm`, {
      query: { token: authToken, user_id: "frontend_user_123" }, // Example user_id
      transports: ['websocket'] // Prefer WebSocket transport
    });
    setSocket(newSocket);

    newSocket.on('connect', () => {
      addNotification('WebSocket connected to /swarm', 'success');
    });
    newSocket.on('disconnect', (reason) => {
      addNotification(`WebSocket disconnected: ${reason}`, 'error');
    });
    newSocket.on('connect_error', (err) => {
      addNotification(`WebSocket connection error: ${err.message}`, 'error');
      console.error('WebSocket connection error:', err);
    });
    newSocket.on('error', (err) => { // General errors from server
      addNotification(`Server error: ${err.message || JSON.stringify(err)}`, 'error');
      console.error('Server error via WebSocket:', err);
    });

    // Handler for single agent streaming responses (chunks)
    newSocket.on('response_stream_chunk', (data) => {
      setChatMessages(prev => {
        const lastMsg = prev[prev.length - 1];
        if (lastMsg && lastMsg.id === data.session_id && lastMsg.type === 'agent_response_stream') {
          return prev.map(msg =>
            msg.id === data.session_id ? { ...msg, text: msg.text + data.chunk } : msg
          );
        } else {
          // This case should ideally be preceded by response_stream_start
          // For robustness, create a new message if no stream start was caught or if structure differs
          return [...prev, {
            id: data.session_id, // Use session_id as message ID for streaming
            type: 'agent_response_stream',
            sender: data.agent_id,
            text: data.chunk,
            timestamp: new Date(data.timestamp || Date.now())
          }];
        }
      });
    });

    newSocket.on('response_stream_start', (data) => {
      // Create a new message placeholder for the incoming stream
      setChatMessages(prev => [...prev, {
        id: data.session_id, // Use session_id as the unique ID for this message
        type: 'agent_response_stream', // A new type to indicate it's a streaming response
        sender: data.agent_id, // The agent sending the response
        text: '', // Start with empty text, chunks will append to this
        timestamp: new Date(data.timestamp || Date.now())
      }]);
    });

    newSocket.on('response_stream_end', (data) => {
      // Finalize the streamed message, maybe update its status or full text if needed
      setChatMessages(prev => prev.map(msg =>
        msg.id === data.session_id ? { ...msg, text: data.full_response, isStreaming: false } : msg
      ));
    });

    // Handler for swarm (multi-agent) responses
    newSocket.on('swarm_responses', (data) => {
      addNotification(`Received swarm responses for conversation ${data.conversation_id}`, 'info');
      console.log('Swarm responses:', data);
      // Create a new chat message for each response in the swarm
      const swarmResponseMessages = data.responses.map(res => ({
        id: `${data.conversation_id}-${res.agent_id}-${Date.now()}`, // Unique ID for each part of swarm response
        type: res.status === 'success' ? 'agent_response' : 'agent_error',
        sender: res.agent_name || res.agent_id,
        text: res.status === 'success' ? res.response.content : `Error: ${res.error}`,
        modelUsed: res.status === 'success' ? res.response.model_used : null,
        timestamp: new Date(res.response?.timestamp || Date.now())
      }));
      setChatMessages(prev => [...prev, ...swarmResponseMessages]);
    });

    return () => {
      newSocket.close();
    };
  }, []); // Empty dependency array means this runs once on mount and cleans up on unmount

  useEffect(() => { // Scroll to bottom when chatMessages change
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  useEffect(() => { // Update selected model if agent has a preferred one
    if (selectedAgent && selectedAgent.id !== 'swarm' && selectedAgent.current_model) {
      setSelectedModel(selectedAgent.current_model);
    } else if (!selectedAgent || selectedAgent.id === 'swarm') {
      // Reset to a general default or keep user's choice for swarm/no selection
      setSelectedModel('anthropic/claude-3.5-sonnet');
    }
  }, [selectedAgent]);


  // --- Data Loading ---
  const loadAgents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents`); // Assuming this endpoint exists
      if (!response.ok) throw new Error(`Failed to fetch agents: ${response.status}`);
      const data = await response.json();
      setAgents(data.data || []); // data.data is based on current API structure
    } catch (error) {
      console.error('Error loading agents:', error);
      addNotification(error.message, 'error');
    }
  };

  const loadModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`); // Assuming this endpoint exists
      if (!response.ok) throw new Error(`Failed to fetch models: ${response.status}`);
      const data = await response.json();

      let allModels = data.data || [];

      // Ensure QWEN CODER and DEEPSEEK are present
      const requiredModelNames = ["QWEN CODER", "DEEPSEEK"];
      let topModels = [];
      let otherModels = [];

      // Separate required models and other models
      allModels.forEach(model => {
        if (requiredModelNames.includes(model.name)) {
          topModels.push(model);
        } else {
          otherModels.push(model);
        }
      });

      // Take top N models from the remaining, ensuring not to duplicate
      const remainingSlots = 15 - topModels.length;
      if (remainingSlots > 0) {
        topModels = [...topModels, ...otherModels.slice(0, remainingSlots)];
      }

      // Remove duplicates if any model was in both required and top N from otherModels
      const uniqueModelNames = new Set();
      const finalModels = [];
      for (const model of topModels) {
        if (!uniqueModelNames.has(model.name)) {
          finalModels.push(model);
          uniqueModelNames.add(model.name);
        }
      }

      // Ensure the two specific models are at the top of the list if they exist
      const qwenModel = finalModels.find(m => m.name === "QWEN CODER");
      const deepseekModel = finalModels.find(m => m.name === "DEEPSEEK");

      let sortedModels = finalModels.filter(
        m => m.name !== "QWEN CODER" && m.name !== "DEEPSEEK"
      );

      if (deepseekModel) {
        sortedModels.unshift(deepseekModel);
      }
      if (qwenModel) {
        sortedModels.unshift(qwenModel);
      }

      // Ensure the list does not exceed 15 models
      setModelOptions(sortedModels.slice(0, 15));

      if (sortedModels.length > 0 && !selectedModel) {
        // setSelectedModel(sortedModels[0].id); // Set a default model if none selected
      }
    } catch (error) {
      console.error('Error loading models:', error);
      // Optionally set to empty or default models in case of error
      setModelOptions([]);
    }
  };

  // --- Event Handlers ---
  const addNotification = (msg, type = 'info', duration = 5000) => {
    const newNotification = { id: Date.now(), message: msg, type };
    setNotifications(prev => [...prev, newNotification]);
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== newNotification.id));
    }, duration);
  };

  const handleSendMessage = () => {
    if (!message.trim() || !socket) {
      addNotification('Cannot send empty message or WebSocket not connected.', 'error');
      return;
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      type: 'user_message',
      sender: 'User',
      text: message,
      timestamp: new Date()
    };
    setChatMessages(prev => [...prev, userMessage]);

    const mentions = message.match(/@\w+/g) || [];
    // Swarm mode if: @mentions are present, OR "Swarm Mode" is selected, OR no specific agent is selected.
    // For this implementation, we'll assume "Swarm Mode" is represented by selectedAgent.id === 'swarm'
    // or if there are mentions.
    const isSwarmIntended = mentions.length > 0 || (selectedAgent && selectedAgent.id === 'swarm');

    if (isSwarmIntended) {
      const newConvId = currentConversationId || `conv-${Date.now()}`;
      if (!currentConversationId) setCurrentConversationId(newConvId);

      socket.emit('swarm_message', {
        message: message,
        // agent_ids: explicitly_selected_agent_ids_for_swarm, // If UI allows picking multiple agents
        conversation_id: newConvId
      });
      addNotification('Swarm message sent!', 'success');
    } else if (selectedAgent && selectedAgent.id !== 'swarm') { // Single agent message (streaming)
      socket.emit('agent_message', {
        agent_id: selectedAgent.id,
        message: message,
        model: selectedModel
      });
      addNotification(`Message sent to ${selectedAgent.name || selectedAgent.id}!`, 'success');
    } else {
      // Fallback: if no agent selected and not explicitly swarm, treat as swarm by default or error
      // For now, let's treat as a general swarm message if no agent selected.
      const newConvId = currentConversationId || `conv-${Date.now()}`;
      if (!currentConversationId) setCurrentConversationId(newConvId);
      socket.emit('swarm_message', { message: message, conversation_id: newConvId });
      addNotification('Message sent to swarm (default)!', 'success');
    }
    setMessage(''); // Clear input after sending
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && message.trim()) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getAgentIcon = (agentIdOrName) => {
    // Find agent by ID or Name to get the correct name for icon mapping if needed
    const agent = agents.find(a => a.id === agentIdOrName || a.name === agentIdOrName);
    const nameToLookup = agent ? agent.name : agentIdOrName;

    // Define specific icons for agents by name
    const iconMap = {
      'User': Smile, // For user messages
      'Communication Agent': MessageSquare,
      'Cathy': Smile, // Cathy can keep Smile or get a specific one
      'DataMiner': Cpu,
      'Coder': Code,
      'Creative': Mail, // Or a more "creative" icon like Brush or Wand
      'Researcher': CheckCircle, // Or Search icon
      'Swarm Mode': Users, // Icon for when Swarm Mode is selected
      'Default': Layers // Fallback icon
    };
    return iconMap[nameToLookup] || iconMap['Default'];
  };

  const handleTransform = async () => { // Quick Transform Bar logic
    if (!transformText.trim()) {
      addNotification('Please enter text to transform', 'error');
      return;
    }
    // Determine which agent to use for transformation.
    // If an agent is selected, use it. Otherwise, use a default (e.g., 'comms' agent).
    const agentForTransform = (selectedAgent && selectedAgent.id !== 'swarm') ? selectedAgent.id : 'comms';

    setIsTransforming(true);
    try {
      // This assumes a /api/transform endpoint exists and is handled by an agent.
      // For now, this is more of a placeholder unless such an endpoint is fully implemented.
      // A more robust way would be to send a specific type of message via WebSocket.
      addNotification(`Transforming text with ${agentForTransform}... (Placeholder - not fully implemented)`, 'info');
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      const mockTransformedText = `Transformed: ${transformText} (by ${agentForTransform})`;
      navigator.clipboard.writeText(mockTransformedText);
      addNotification('Mock transformed text copied to clipboard!', 'success');
      setTransformText('');
      // Optionally, add to chat:
      // setChatMessages(prev => [...prev, { id: Date.now(), type: 'system', text: `Original: ${transformText}\nTransformed (mock): ${mockTransformedText}` }]);
    } catch (error) {
      console.error('Transform error:', error);
      addNotification(error.message || 'Failed to transform text', 'error');
    } finally {
      setIsTransforming(false);
    }
  };

  const formatTimestamp = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };


  // --- Render ---
  return (
    <div className="flex h-screen bg-white font-sans">
      {/* Sidebar */}
      <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-100"> {/* Header */}
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white"><Layers className="w-5 h-5" /></div>
            <div className="text-lg font-semibold text-gray-900">Swarm UI</div>
          </div>
          <span className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded mt-2">v2.1 Multi-Agent</span>
        </div>

        {/* System Status (Simplified) */}
        <div className="p-4 bg-gray-100 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm text-gray-600"><Cpu className="w-3.5 h-3.5" /><span>System Status</span></div>
            <div className={`flex items-center gap-1.5 text-xs font-medium ${socket && socket.connected ? 'text-green-600' : 'text-red-600'}`}>
              <div className={`w-1.5 h-1.5 rounded-full ${socket && socket.connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <span>{socket && socket.connected ? 'Connected' : 'Offline'}</span>
            </div>
          </div>
        </div>

        {/* Agent List + Swarm Mode */}
        <div className="flex-1 overflow-y-auto p-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Modes & Agents</h3>
          <div className="space-y-2">
            {/* Swarm Mode Selector */}
            <div
              className={`flex items-center p-3.5 rounded-lg cursor-pointer transition-all duration-200 border ${
                selectedAgent?.id === 'swarm'
                  ? 'bg-purple-500 border-purple-500 text-white shadow-md'
                  : 'bg-white border-gray-100 hover:border-purple-200 hover:shadow-sm hover:-translate-y-0.5'
              }`}
              onClick={() => setSelectedAgent({ id: 'swarm', name: 'Swarm Mode', role: 'Collaborate with multiple agents' })}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-3.5 ${selectedAgent?.id === 'swarm' ? 'bg-white/20' : 'bg-gray-100'}`}>
                <Users className={`w-5 h-5 ${selectedAgent?.id === 'swarm' ? 'text-white' : 'text-gray-600'}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className={`text-sm font-semibold ${selectedAgent?.id === 'swarm' ? 'text-white' : 'text-gray-900'}`}>Swarm Mode</div>
                <div className={`text-xs ${selectedAgent?.id === 'swarm' ? 'text-white/80' : 'text-gray-500'} truncate`}>Use @mentions or auto-select</div>
              </div>
            </div>

            {/* Individual Agents */}
            {agents.map((agent) => {
              const Icon = getAgentIcon(agent.name);
              const isSelected = selectedAgent?.id === agent.id;
              return (
                <div
                  key={agent.id}
                  className={`flex items-center p-3.5 rounded-lg cursor-pointer transition-all duration-200 border ${
                    isSelected
                      ? 'bg-blue-500 border-blue-500 text-white shadow-md'
                      : 'bg-white border-gray-100 hover:border-blue-200 hover:shadow-sm hover:-translate-y-0.5'
                  }`}
                  onClick={() => setSelectedAgent(agent)}
                >
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-3.5 ${isSelected ? 'bg-white/20' : 'bg-gray-100'}`}>
                    <Icon className={`w-5 h-5 ${isSelected ? 'text-white' : 'text-gray-600'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-sm font-semibold ${isSelected ? 'text-white' : 'text-gray-900'}`}>{agent.name}</div>
                    <div className={`text-xs ${isSelected ? 'text-white/80' : 'text-gray-500'} truncate`}>{agent.role}</div>
                  </div>
                  {/* Agent status indicator (can be fetched or hardcoded for now) */}
                  <div className={`w-2 h-2 rounded-full ${agent.status === 'idle' ? 'bg-green-400' : (agent.status === 'busy' ? 'bg-yellow-400' : 'bg-red-400')} ${isSelected ? '' : 'opacity-60'}`}></div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col bg-gray-100">
        {/* Chat Header */}
        <div className="p-5 bg-white border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-xl font-semibold text-gray-900">
            {selectedAgent ? selectedAgent.name : 'Select Agent or Swarm Mode'}
          </h2>
          {/* Model Selector (simplified) */}
          <div className="relative">
            <button onClick={() => setShowModelDropdown(!showModelDropdown)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 border border-gray-200 rounded-lg text-sm hover:border-blue-500">
              <MessageSquare className="w-3.5 h-3.5" />
              <span>{modelOptions.find(m => m.id === selectedModel)?.name || selectedModel}</span>
              <ChevronDown className="w-3 h-3" />
            </button>
            {showModelDropdown && modelOptions.length > 0 && (
              <div className="absolute top-full right-0 mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-xl z-50 max-h-80 overflow-y-auto">
                {modelOptions.map(model => (
                  <div key={model.id} onClick={() => { setSelectedModel(model.id); setShowModelDropdown(false); }}
                    className="p-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0">
                    <div className="text-sm font-medium text-gray-800">{model.name}</div>
                    <div className="text-xs text-gray-500 truncate">{model.description || "LLM"}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-white">
          {chatMessages.map((msg, index) => (
            <div key={msg.id || index} className={`flex ${msg.type === 'user_message' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xl p-3 rounded-xl shadow-sm ${
                msg.type === 'user_message'
                  ? 'bg-blue-500 text-white'
                  : (msg.type === 'agent_error' ? 'bg-red-100 text-red-700 border border-red-200' : 'bg-gray-100 text-gray-800')
              }`}>
                <div className="flex items-center mb-1">
                  {React.createElement(getAgentIcon(msg.sender), { className: `w-4 h-4 mr-2 ${msg.type === 'user_message' ? 'text-white/80' : 'text-gray-500'}` })}
                  <span className="text-xs font-semibold">{msg.sender}</span>
                  {msg.modelUsed && <span className="ml-2 text-xs opacity-70">({msg.modelUsed.split('/').pop()})</span>}
                </div>
                <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
                <div className="text-xs opacity-60 mt-1 text-right">{formatTimestamp(msg.timestamp)}</div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} /> {/* For auto-scrolling */}
           {chatMessages.length === 0 && !selectedAgent && (
            <div className="text-center text-gray-500 pt-16">
              <Layers className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p className="text-lg">Welcome to Swarm!</p>
              <p>Select an agent or "Swarm Mode" to begin.</p>
            </div>
          )}
          {chatMessages.length === 0 && selectedAgent && (
            <div className="text-center text-gray-500 pt-16">
               {React.createElement(getAgentIcon(selectedAgent.name), { className: `w-16 h-16 mx-auto mb-4 text-gray-300` })}
              <p className="text-lg">Ready to chat with {selectedAgent.name}.</p>
              <p>Type your message below.</p>
            </div>
          )}
        </div>

        {/* Message Input Area */}
        <div className="p-4 bg-white border-t border-gray-200">
          <div className="flex gap-3 items-end">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={selectedAgent?.id === 'swarm' ? "Type message for swarm, use @mention..." : (selectedAgent ? `Message ${selectedAgent.name}...` : "Select an agent or mode...")}
              className="w-full min-h-[48px] max-h-[150px] px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors text-sm"
              rows="1"
              disabled={!socket || (!selectedAgent && !message.includes('@'))} // Disable if no socket or no target for message
            />
            <button onClick={handleSendMessage}
              disabled={!socket || !message.trim() || (!selectedAgent && !message.includes('@'))}
              className="w-12 h-12 bg-blue-500 text-white rounded-xl flex items-center justify-center hover:bg-blue-600 active:bg-blue-700 transition-all duration-150 shadow-md disabled:opacity-50 disabled:cursor-not-allowed">
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Notifications Area - Moved inside the main div */}
      {notifications.map((notification) => (
        <div
          key={notification.id}
          className={`fixed top-4 right-4 px-4 py-3 rounded-lg text-sm font-medium shadow-lg z-50 ${
            notification.type === 'error'
              ? 'bg-red-100 text-red-800 border border-red-200'
              : notification.type === 'success'
              ? 'bg-green-100 text-green-800 border border-green-200'
              : 'bg-blue-100 text-blue-800 border border-blue-200'
          }`}
        >
          {notification.message}
        </div>
      ))}
    </div>
  );
}

export default App;

