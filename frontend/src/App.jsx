import React, { useState, useEffect } from 'react';
import { 
  Layers, Settings, Cpu, CheckCircle, AlertTriangle, 
  MessageSquare, Mail, Code, Calendar, Wrench, Smile,
  ChevronDown, Sun, Send
} from 'lucide-react';

// Dynamically determine API URL based on current location
const API_BASE_URL = (() => {
  // If VITE_API_URL is set, use it
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // In production, use the same origin as the frontend
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return window.location.origin;
  }
  
  // In development, use localhost:5000
  return 'http://localhost:5000';
})();

function App() {
  // Core State
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [message, setMessage] = useState('');
  const [notifications, setNotifications] = useState([]);
  const [selectedModel, setSelectedModel] = useState('GPT-4o');
  const [showModelDropdown, setShowModelDropdown] = useState(false);
  const [modelOptions, setModelOptions] = useState([]);
  const [transformText, setTransformText] = useState('');
  const [isTransforming, setIsTransforming] = useState(false);

  // Load agents on mount
  useEffect(() => {
    loadAgents();
    loadModels();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      fetchAgentConfig(selectedAgent.id);
    }
  }, [selectedAgent]);

  const loadAgents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents`);
      const data = await response.json();
      setAgents(data.data || []);
    } catch (error) {
      console.error('Error loading agents:', error);
      addNotification('Failed to load agents', 'error');
    }
  };

  const loadModels = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/models`);
      const data = await response.json();
      setModelOptions(data.data || []);
    } catch (error) {
      console.error('Error loading models:', error);
    }
  };

  const fetchAgentConfig = async (id) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents/${id}/config`);
      const data = await response.json();
      if (data.data && data.data.current_model) {
        setSelectedModel(data.data.current_model);
      }
    } catch (error) {
      console.error('Error fetching agent config:', error);
    }
  };

  const addNotification = (message, type = 'info') => {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    setNotifications(prev => [...prev, notification]);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const handleSendMessage = () => {
    if (message.trim()) {
      console.log('Sending message:', message);
      setMessage('');
      addNotification('Message sent!', 'success');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const getAgentIcon = (agentName) => {
    const iconMap = {
      'Communication Agent': MessageSquare,
      'Cathy': Smile,
      'DataMiner': Cpu,
      'Coder': Code,
      'Creative': Mail,
      'Researcher': CheckCircle
    };
    return iconMap[agentName] || MessageSquare;
  };

  const handleTransform = async () => {
    if (!transformText.trim()) {
      addNotification('Please enter text to transform', 'error');
      return;
    }

    if (!selectedAgent) {
      addNotification('Please select an agent first', 'error');
      return;
    }

    setIsTransforming(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/transform`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: transformText,
          agent_id: selectedAgent.id
        })
      });

      const data = await response.json();
      
      if (response.ok && data.data) {
        // Copy transformed text to clipboard
        navigator.clipboard.writeText(data.data.transformed_text);
        addNotification('Transformed text copied to clipboard!', 'success');
        
        // Clear the transform input
        setTransformText('');
        
        // Optionally, show the transformed text in the chat area
        setMessage(data.data.transformed_text);
      } else {
        throw new Error(data.error?.message || 'Transform failed');
      }
    } catch (error) {
      console.error('Transform error:', error);
      addNotification(error.message || 'Failed to transform text', 'error');
    } finally {
      setIsTransforming(false);
    }
  };


  return (
    <div className="flex h-screen bg-white">
      {/* Professional Sidebar */}
      <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-center gap-3 mb-1">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white">
              <Layers className="w-5 h-5" />
            </div>
            <div className="text-lg font-semibold text-gray-900">Swarm</div>
          </div>
          <span className="inline-flex items-center px-2 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded mt-2">
            Version 2.0
          </span>
        </div>

        {/* System Status */}
        <div className="p-4 bg-gray-100 border-b border-gray-200">
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Cpu className="w-3.5 h-3.5" />
                <span>System Status</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-medium text-green-600">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                <span>Connected</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <CheckCircle className="w-3.5 h-3.5" />
                <span>File Access</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-medium text-green-600">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                <span>Available</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Settings className="w-3.5 h-3.5" />
                <span>Memory</span>
              </div>
              <div className="flex items-center gap-1.5 text-xs font-medium text-yellow-600">
                <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full"></div>
                <span>Limited</span>
              </div>
            </div>
          </div>
        </div>

        {/* Available Agents */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Available Agents
            </h3>
          </div>
          <div className="space-y-2">
            {agents.length > 0 ? (
              agents.map((agent) => {
                const IconComponent = getAgentIcon(agent.name);
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
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center mr-3.5 ${
                      isSelected ? 'bg-white/20' : 'bg-gray-100'
                    }`}>
                      <IconComponent className={`w-5 h-5 ${
                        isSelected ? 'text-white' : 'text-gray-600'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`text-sm font-semibold ${
                        isSelected ? 'text-white' : 'text-gray-900'
                      }`}>
                        {agent.name}
                      </div>
                      <div className={`text-xs ${
                        isSelected ? 'text-white/80' : 'text-gray-500'
                      } truncate`}>
                        {agent.role}
                      </div>
                    </div>
                    <div className={`w-2 h-2 rounded-full ${
                      agent.status === 'idle' ? 'bg-green-400' : 'bg-yellow-400'
                    } ${isSelected ? '' : 'opacity-60'}`}></div>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-gray-500 py-8">
                <Cpu className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p className="text-sm">Loading agents...</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Quick Transform Bar */}
        <div className="p-4 bg-gray-100 border-b border-gray-200 flex gap-3 items-center">
          <input
            type="text"
            value={transformText}
            onChange={(e) => setTransformText(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey && !isTransforming) {
                e.preventDefault();
                handleTransform();
              }
            }}
            placeholder="Paste text here for quick transformation..."
            className="flex-1 px-4 py-2.5 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-blue-500 transition-colors"
            disabled={isTransforming}
          />
          <button 
            onClick={handleTransform}
            disabled={isTransforming || !selectedAgent}
            className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
              isTransforming || !selectedAgent
                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            <Settings className={`w-4 h-4 ${isTransforming ? 'animate-spin' : ''}`} />
            {isTransforming ? 'Transforming...' : 'Transform'}
          </button>
        </div>

        {/* Chat Header */}
        <div className="p-5 bg-white border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-gray-900">
              {selectedAgent ? selectedAgent.name : 'Welcome to Swarm'}
            </h2>
            {selectedAgent && (
              <div className="flex items-center gap-1.5 px-3 py-1 bg-gray-100 rounded-full text-xs text-gray-600">
                <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                <span>Active</span>
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            {/* Model Selector */}
            <div className="relative">
              <button
                onClick={() => setShowModelDropdown(!showModelDropdown)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-100 border border-gray-200 rounded-lg text-sm hover:border-blue-500 transition-colors"
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>{selectedModel}</span>
                <ChevronDown className="w-3 h-3" />
              </button>
              {showModelDropdown && (
                <div className="absolute top-full right-0 mt-2 w-70 bg-white border border-gray-200 rounded-lg shadow-lg z-50">
                  {modelOptions.map((model) => (
                    <div
                      key={model.id || model.name}
                      className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                      onClick={() => {
                        setSelectedModel(model.id || model.name);
                        setShowModelDropdown(false);
                      }}
                    >
                      <div className="text-sm font-medium text-gray-900">{model.name}</div>
                      <div className="text-xs text-gray-500">{model.description}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <button className="w-9 h-9 border border-gray-200 bg-white rounded-lg flex items-center justify-center hover:bg-gray-50 hover:border-blue-500 transition-colors">
              <Sun className="w-4 h-4 text-gray-600" />
            </button>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 flex items-center justify-center bg-white">
          {!selectedAgent ? (
            <div className="text-center max-w-4xl mx-auto px-12">
              <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Layers className="w-12 h-12 text-blue-500" />
              </div>
              <h1 className="text-3xl font-bold text-gray-900 mb-3">Welcome to Swarm</h1>
              <p className="text-gray-600 mb-12 text-lg leading-relaxed">
                Your intelligent multi-agent collaboration platform. Select an agent to begin, or use @mentions to collaborate with multiple agents simultaneously.
              </p>
              <div className="grid grid-cols-3 gap-4 max-w-3xl mx-auto">
                <div className="p-6 bg-gray-50 border border-gray-100 rounded-xl hover:bg-gray-100 hover:border-blue-200 hover:-translate-y-1 transition-all duration-200 cursor-pointer">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4">
                    <MessageSquare className="w-6 h-6 text-blue-500" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Communications</h3>
                  <p className="text-sm text-gray-600">Transform text into clear, professional communication</p>
                </div>
                <div className="p-6 bg-gray-50 border border-gray-100 rounded-xl hover:bg-gray-100 hover:border-blue-200 hover:-translate-y-1 transition-all duration-200 cursor-pointer">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4">
                    <Mail className="w-6 h-6 text-blue-500" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Email Assistant</h3>
                  <p className="text-sm text-gray-600">Professional email composition and strategy</p>
                </div>
                <div className="p-6 bg-gray-50 border border-gray-100 rounded-xl hover:bg-gray-100 hover:border-blue-200 hover:-translate-y-1 transition-all duration-200 cursor-pointer">
                  <div className="w-12 h-12 bg-white rounded-xl flex items-center justify-center mb-4">
                    <Code className="w-6 h-6 text-blue-500" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">Code Assistant</h3>
                  <p className="text-sm text-gray-600">Clean code generation and technical solutions</p>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-xl flex items-center justify-center mx-auto mb-4">
                {React.createElement(getAgentIcon(selectedAgent.name), { 
                  className: "w-8 h-8 text-gray-400" 
                })}
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready to collaborate!</h3>
              <p className="text-gray-500 mb-4">Start a conversation with {selectedAgent.name}.</p>
              <p className="text-sm text-gray-400">💡 Tip: Use @mentions to bring specific agents into the conversation</p>
            </div>
          )}
        </div>

        {/* Message Input */}
        {selectedAgent && (
          <div className="p-5 bg-white border-t border-gray-200">
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Type your message... Use @ to mention other agents"
                  className="w-full min-h-[44px] max-h-[120px] px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl resize-none focus:outline-none focus:border-blue-500 focus:bg-white transition-colors text-sm"
                  rows="1"
                />
              </div>
              <button
                onClick={handleSendMessage}
                className="w-11 h-11 bg-blue-500 text-white rounded-xl flex items-center justify-center hover:bg-blue-600 hover:-translate-y-0.5 transition-all duration-200 shadow-md"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}

        {/* Notifications */}
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
    </div>
  );
}

export default App;

