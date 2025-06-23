import React, { useState, useEffect } from 'react';
import { 
  Bot, User, Send, Settings, Search, Filter, 
  Sidebar, Menu, Home, Inbox, Calendar, FileText, BarChart3,
  Wifi, WifiOff, Signal, Battery, Monitor, Cpu, HardDrive, Mic
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

function App() {
  // Core State
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [message, setMessage] = useState('');
  const [notifications, setNotifications] = useState([]);

  // Load agents on mount
  useEffect(() => {
    loadAgents();
  }, []);

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

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <Bot className="w-8 h-8 text-blue-500" />
            <div>
              <h1 className="text-lg font-semibold text-gray-900">Swarm Agents</h1>
              <p className="text-sm text-gray-500">Multi-Agent AI System</p>
            </div>
          </div>
        </div>

        {/* System Status */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">System Status</span>
            <div className="flex items-center space-x-2">
              <Wifi className="w-4 h-4 text-green-500" />
              <span className="text-sm text-green-600">Connected</span>
            </div>
          </div>
        </div>

        {/* Agent Search */}
        <div className="p-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search agents..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Agent Filter */}
        <div className="px-4 pb-4">
          <select className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent">
            <option>All Agents</option>
            <option>Available</option>
            <option>Busy</option>
            <option>Offline</option>
          </select>
        </div>

        {/* Agents List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {agents.length > 0 ? (
            agents.map((agent) => (
              <div
                key={agent.id}
                className="p-3 border border-gray-200 rounded-lg hover:border-blue-300 cursor-pointer transition-colors"
                onClick={() => {
                  if (selectedAgents.includes(agent.id)) {
                    setSelectedAgents(prev => prev.filter(id => id !== agent.id));
                  } else {
                    setSelectedAgents(prev => [...prev, agent.id]);
                  }
                }}
              >
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Bot className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{agent.name}</h3>
                    <p className="text-sm text-gray-500">{agent.role}</p>
                  </div>
                  <div className={`w-3 h-3 rounded-full ${
                    agent.status === 'idle' ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                </div>
              </div>
            ))
          ) : (
            <div className="text-center text-gray-500 py-8">
              <Bot className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p>Loading agents...</p>
            </div>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">New Conversation</h2>
              <p className="text-sm text-gray-500">Select agents to start collaborating</p>
            </div>
            {notifications.map((notification) => (
              <div
                key={notification.id}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  notification.type === 'error' 
                    ? 'bg-red-100 text-red-800' 
                    : notification.type === 'success'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-blue-100 text-blue-800'
                }`}
              >
                {notification.message}
              </div>
            ))}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex items-center justify-center bg-gray-50">
          <div className="text-center">
            <div className="w-24 h-24 mx-auto mb-6 bg-gray-200 rounded-full flex items-center justify-center">
              <Bot className="w-12 h-12 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready to collaborate!</h3>
            <p className="text-gray-500 mb-4">Select agents from the sidebar and start a conversation.</p>
            <p className="text-sm text-gray-400">💡 Tip: Use @mentions to bring specific agents into the conversation</p>
          </div>
        </div>

        {/* Message Input */}
        <div className="bg-white border-t border-gray-200 p-4">
          <div className="flex items-center space-x-3">
            <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <FileText className="w-5 h-5" />
            </button>
            <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <Mic className="w-5 h-5" />
            </button>
            <div className="flex-1">
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Select agents and start typing..."
                className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows="1"
              />
            </div>
            <button
              onClick={handleSendMessage}
              className="p-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;

