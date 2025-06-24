import { useState, useEffect, useRef } from 'react';
import { io } from 'socket.io-client';
import { EnhancedAgentCard, EnhancedMessage, EnhancedMessageInput } from './components/EnhancedComponents';
import { 
  Bot, Users, MessageSquare, Settings, Search, Filter, Star, 
  Clock, Activity, TrendingUp, Zap, Brain, Target, Crown,
  Bell, BellOff, Sun, Moon, Maximize2, Minimize2, RefreshCw,
  Sidebar, Menu, Home, Inbox, Calendar, FileText, BarChart3,
  Wifi, WifiOff, Signal, Battery, Monitor, Cpu, HardDrive
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

function App() {
  // Core State
  const [agents, setAgents] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // UI State
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [systemStats, setSystemStats] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  
  // Performance State
  const [agentPerformance, setAgentPerformance] = useState({});
  const [systemHealth, setSystemHealth] = useState(null);
  const [responseTime, setResponseTime] = useState(0);
  
  // Refs
  const socketRef = useRef(null);
  const messagesEndRef = useRef(null);
  const performanceIntervalRef = useRef(null);

  // Initialize socket connection
  useEffect(() => {
    // Use polling for production compatibility
    socketRef.current = io(API_BASE_URL, {
      transports: ['polling', 'websocket'],
      upgrade: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000
    });

    socketRef.current.on('connect', () => {
      setConnectionStatus('connected');
      console.log('Connected to server');
    });

    socketRef.current.on('disconnect', () => {
      setConnectionStatus('disconnected');
      console.log('Disconnected from server');
    });

    socketRef.current.on('message_response', (data) => {
      setMessages(prev => [...prev, data.message]);
      setIsLoading(false);
    });

    socketRef.current.on('agent_status_update', (data) => {
      setAgents(prev => prev.map(agent => 
        agent.id === data.agent_id 
          ? { ...agent, status: data.status }
          : agent
      ));
    });

    socketRef.current.on('performance_update', (data) => {
      setAgentPerformance(prev => ({
        ...prev,
        [data.agent_id]: data.metrics
      }));
    });

    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, []);

  // Load initial data
  useEffect(() => {
    loadAgents();
    loadConversations();
    startPerformanceMonitoring();
  }, []);

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Performance monitoring
  const startPerformanceMonitoring = () => {
    performanceIntervalRef.current = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/monitoring/health`);
        const health = await response.json();
        setSystemHealth(health);
        
        const metricsResponse = await fetch(`${API_BASE_URL}/api/monitoring/metrics`);
        const metrics = await metricsResponse.json();
        setResponseTime(metrics.performance.avg_response_time);
      } catch (error) {
        console.error('Performance monitoring error:', error);
      }
    }, 10000); // Update every 10 seconds

    return () => {
      if (performanceIntervalRef.current) {
        clearInterval(performanceIntervalRef.current);
      }
    };
  };

  const loadAgents = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/agents`);
      const data = await response.json();
      setAgents(data.data || []); // API returns data in 'data' field, not 'agents'
    } catch (error) {
      console.error('Error loading agents:', error);
      addNotification('Failed to load agents', 'error');
    }
  };

  const loadConversations = async () => {
    // Conversations endpoint not implemented yet, using empty array
    setConversations([]);
  };

  const loadMessages = async (conversationId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}/messages`);
      const data = await response.json();
      setMessages(data.messages || []);
    } catch (error) {
      console.error('Error loading messages:', error);
      addNotification('Failed to load messages', 'error');
    }
  };

  const createNewConversation = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `New Conversation ${new Date().toLocaleString()}`,
          agent_ids: selectedAgents.map(agent => agent.id)
        })
      });
      
      const data = await response.json();
      const newConversation = data.conversation;
      
      setConversations(prev => [newConversation, ...prev]);
      setCurrentConversation(newConversation);
      setMessages([]);
      
      addNotification('New conversation created', 'success');
    } catch (error) {
      console.error('Error creating conversation:', error);
      addNotification('Failed to create conversation', 'error');
    }
  };

  const sendMessage = async (messageData) => {
    if (!currentConversation) {
      await createNewConversation();
      return;
    }

    const userMessage = {
      id: Date.now(),
      content: messageData.content,
      sender_type: 'user',
      timestamp: new Date().toISOString(),
      mentions: messageData.mentions || [],
      attachments: messageData.attachments || []
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const startTime = Date.now();
      
      const response = await fetch(`${API_BASE_URL}/api/conversations/${currentConversation.id}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: messageData.content,
          mentions: messageData.mentions,
          attachments: messageData.attachments,
          agent_ids: selectedAgents.map(agent => agent.id)
        })
      });

      const responseTime = Date.now() - startTime;
      setResponseTime(responseTime);

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();
      
      // Add agent responses
      if (data.responses) {
        data.responses.forEach(agentResponse => {
          setMessages(prev => [...prev, {
            id: Date.now() + Math.random(),
            content: agentResponse.content,
            sender_type: 'agent',
            agent_name: agentResponse.agent_name,
            timestamp: new Date().toISOString(),
            model_used: agentResponse.model_used
          }]);
        });
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      addNotification('Failed to send message', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const addNotification = (message, type = 'info') => {
    const notification = {
      id: Date.now(),
      message,
      type,
      timestamp: new Date()
    };
    
    setNotifications(prev => [notification, ...prev.slice(0, 4)]);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, 5000);
  };

  const toggleAgentSelection = (agent) => {
    setSelectedAgents(prev => {
      const isSelected = prev.find(a => a.id === agent.id);
      if (isSelected) {
        return prev.filter(a => a.id !== agent.id);
      } else {
        return [...prev, agent];
      }
    });
  };

  const selectConversation = (conversation) => {
    setCurrentConversation(conversation);
    loadMessages(conversation.id);
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      default: return 'text-red-500';
    }
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <Wifi className="w-4 h-4" />;
      case 'connecting': return <Signal className="w-4 h-4" />;
      default: return <WifiOff className="w-4 h-4" />;
    }
  };

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         agent.role.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesFilter = filterStatus === 'all' || agent.status === filterStatus;
    return matchesSearch && matchesFilter;
  });

  return (
    <div className={`h-screen flex ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      
      {/* Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-16' : 'w-80'} bg-white border-r border-gray-200 flex flex-col transition-all duration-300`}>
        
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            {!sidebarCollapsed && (
              <div>
                <h1 className="text-xl font-bold text-gray-900">🤖 Swarm Agents</h1>
                <p className="text-sm text-gray-500">Multi-Agent AI System</p>
              </div>
            )}
            <button
              onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* System Status */}
        {!sidebarCollapsed && (
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">System Status</span>
              <div className={`flex items-center space-x-1 ${getConnectionStatusColor()}`}>
                {getConnectionStatusIcon()}
                <span className="text-xs capitalize">{connectionStatus}</span>
              </div>
            </div>
            
            {systemHealth && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>CPU</span>
                  <span>{systemHealth.system?.cpu_percent?.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Memory</span>
                  <span>{systemHealth.system?.memory_percent?.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Response Time</span>
                  <span>{responseTime}ms</span>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Agent Search and Filter */}
        {!sidebarCollapsed && (
          <div className="p-4 border-b border-gray-200">
            <div className="relative mb-3">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search agents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Agents</option>
              <option value="idle">Available</option>
              <option value="busy">Busy</option>
              <option value="offline">Offline</option>
            </select>
          </div>
        )}

        {/* Agents List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {filteredAgents.map(agent => (
            <EnhancedAgentCard
              key={agent.id}
              agent={agent}
              isSelected={selectedAgents.find(a => a.id === agent.id)}
              onSelect={() => toggleAgentSelection(agent)}
              performance={agentPerformance[agent.id]}
              isOnline={agent.status !== 'offline'}
            />
          ))}
        </div>

        {/* Selected Agents Summary */}
        {!sidebarCollapsed && selectedAgents.length > 0 && (
          <div className="p-4 border-t border-gray-200 bg-blue-50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-900">
                Selected Agents ({selectedAgents.length})
              </span>
              <button
                onClick={() => setSelectedAgents([])}
                className="text-xs text-blue-600 hover:text-blue-800"
              >
                Clear All
              </button>
            </div>
            <div className="flex flex-wrap gap-1">
              {selectedAgents.map(agent => (
                <span key={agent.id} className="px-2 py-1 bg-blue-200 text-blue-800 text-xs rounded-full">
                  {agent.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {currentConversation ? currentConversation.title : 'New Conversation'}
              </h2>
              <p className="text-sm text-gray-500">
                {selectedAgents.length > 0 
                  ? `Collaborating with ${selectedAgents.map(a => a.name).join(', ')}`
                  : 'Select agents to start collaborating'
                }
              </p>
            </div>
            
            <div className="flex items-center space-x-3">
              {/* Performance Indicator */}
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Activity className="w-4 h-4" />
                <span>{responseTime}ms</span>
              </div>
              
              {/* Notifications */}
              <div className="relative">
                <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
                  <Bell className="w-5 h-5 text-gray-600" />
                  {notifications.length > 0 && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
                  )}
                </button>
              </div>
              
              {/* Settings */}
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <Settings className="w-5 h-5 text-gray-600" />
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to collaborate!</h3>
              <p className="text-gray-500 mb-4">
                Select agents from the sidebar and start a conversation.
              </p>
              {selectedAgents.length === 0 && (
                <p className="text-sm text-gray-400">
                  💡 Tip: Use @mentions to bring specific agents into the conversation
                </p>
              )}
            </div>
          ) : (
            <>
              {messages.map((message, index) => (
                <EnhancedMessage
                  key={message.id || index}
                  message={message}
                  onReact={(messageId, emoji) => console.log('React:', messageId, emoji)}
                  onBookmark={(messageId, bookmarked) => console.log('Bookmark:', messageId, bookmarked)}
                  onCopy={(messageId) => addNotification('Message copied to clipboard', 'success')}
                  onReply={(message) => console.log('Reply to:', message)}
                />
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Message Input */}
        <EnhancedMessageInput
          onSendMessage={sendMessage}
          agents={agents}
          isLoading={isLoading}
          placeholder={
            selectedAgents.length > 0
              ? `Message ${selectedAgents.map(a => a.name).join(', ')}...`
              : "Select agents and start typing..."
          }
        />
      </div>

      {/* Notifications */}
      {notifications.length > 0 && (
        <div className="fixed top-4 right-4 space-y-2 z-50">
          {notifications.map(notification => (
            <div
              key={notification.id}
              className={`px-4 py-3 rounded-lg shadow-lg ${
                notification.type === 'error' ? 'bg-red-500 text-white' :
                notification.type === 'success' ? 'bg-green-500 text-white' :
                'bg-blue-500 text-white'
              }`}
            >
              {notification.message}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;
