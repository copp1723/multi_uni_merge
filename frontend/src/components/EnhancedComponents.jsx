// 🎨 ENHANCED USER EXPERIENCE COMPONENTS
// Advanced chat interface with optimized workflows

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { Send, Bot, User, Settings, Zap, Brain, Search, Filter, Star, Clock, CheckCircle, AlertCircle, Loader, Plus, X, ChevronDown, ChevronUp, MessageSquare, Users, FileText, Mail, Database, Code, Lightbulb, BarChart3, Mic, MicOff, Volume2, VolumeX, Copy, Download, Share, Bookmark, Tag, Archive, Trash2, MoreHorizontal, Maximize2, Minimize2, RefreshCw, Eye, EyeOff, Heart, ThumbsUp, ThumbsDown, Flag, Shield, Zap as ZapIcon, Sparkles, Target, Rocket, Crown, Award, TrendingUp, Activity, Monitor, Cpu, HardDrive, Wifi, WifiOff, Signal, Battery, BatteryLow, Sun, Moon, Palette, Layout, Grid, List, Columns, Sidebar, Menu, Home, Inbox, Calendar, Bell, BellOff, Info, ExternalLink, Link, Unlink, Lock, Unlock, Key, UserCheck, UserX, UserPlus, UserMinus } from 'lucide-react';
import { io } from 'socket.io-client';

// Enhanced Agent Card with Performance Indicators
const EnhancedAgentCard = ({ agent, isSelected, onSelect, performance, isOnline }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showPerformance, setShowPerformance] = useState(false);

  const getAgentIcon = (type) => {
    const icons = {
      'Cathy': User,
      'DataMiner': BarChart3,
      'Coder': Code,
      'Creative': Lightbulb,
      'Researcher': Search
    };
    return icons[type] || Bot;
  };

  const getPerformanceColor = (score) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const AgentIcon = getAgentIcon(agent.name);

  return (
    <div className={`relative p-4 rounded-xl border-2 transition-all duration-300 cursor-pointer group hover:shadow-lg ${
      isSelected 
        ? 'border-blue-500 bg-blue-50 shadow-md' 
        : 'border-gray-200 bg-white hover:border-gray-300'
    }`} onClick={onSelect}>
      
      {/* Online Status Indicator */}
      <div className={`absolute top-2 right-2 w-3 h-3 rounded-full ${
        isOnline ? 'bg-green-500' : 'bg-gray-400'
      } animate-pulse`} />
      
      {/* Agent Header */}
      <div className="flex items-center space-x-3 mb-3">
        <div className={`p-2 rounded-lg ${
          isSelected ? 'bg-blue-100' : 'bg-gray-100'
        } group-hover:scale-110 transition-transform`}>
          <AgentIcon className={`w-6 h-6 ${
            isSelected ? 'text-blue-600' : 'text-gray-600'
          }`} />
        </div>
        
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900">{agent.name}</h3>
          <p className="text-sm text-gray-500">{agent.role}</p>
        </div>
        
        <button
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
          className="p-1 rounded-full hover:bg-gray-200 transition-colors"
        >
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {/* Agent Status */}
      <div className="flex items-center justify-between mb-3">
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          agent.status === 'idle' ? 'bg-green-100 text-green-800' :
          agent.status === 'busy' ? 'bg-yellow-100 text-yellow-800' :
          'bg-red-100 text-red-800'
        }`}>
          {agent.status.charAt(0).toUpperCase() + agent.status.slice(1)}
        </span>
        
        {performance && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowPerformance(!showPerformance);
            }}
            className={`text-xs font-medium ${getPerformanceColor(performance.score)} hover:underline`}
          >
            {performance.score}% Performance
          </button>
        )}
      </div>

      {/* Capabilities Preview */}
      <div className="flex flex-wrap gap-1 mb-3">
        {agent.capabilities.slice(0, 3).map((capability, index) => (
          <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
            {capability}
          </span>
        ))}
        {agent.capabilities.length > 3 && (
          <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full">
            +{agent.capabilities.length - 3} more
          </span>
        )}
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200 space-y-3">
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-2">All Capabilities</h4>
            <div className="flex flex-wrap gap-1">
              {agent.capabilities.map((capability, index) => (
                <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-full">
                  {capability}
                </span>
              ))}
            </div>
          </div>
          
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-1">Collaboration Style</h4>
            <p className="text-xs text-gray-600">{agent.collaboration_style}</p>
          </div>
          
          {performance && showPerformance && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">Performance Metrics</h4>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span>Response Time</span>
                  <span>{performance.avg_response_time}ms</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Success Rate</span>
                  <span>{performance.success_rate}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span>Tasks Completed</span>
                  <span>{performance.tasks_completed}</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Enhanced Message Component with Rich Features
const EnhancedMessage = ({ message, onReact, onBookmark, onCopy, onReply, currentUser }) => {
  const [showActions, setShowActions] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(message.bookmarked || false);
  const [reactions, setReactions] = useState(message.reactions || {});
  const [showReactions, setShowReactions] = useState(false);

  const isUser = message.sender_type === 'user';
  const timestamp = new Date(message.timestamp);

  const handleReaction = (emoji) => {
    const newReactions = { ...reactions };
    if (newReactions[emoji]) {
      newReactions[emoji]++;
    } else {
      newReactions[emoji] = 1;
    }
    setReactions(newReactions);
    onReact?.(message.id, emoji);
  };

  const handleBookmark = () => {
    setIsBookmarked(!isBookmarked);
    onBookmark?.(message.id, !isBookmarked);
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    onCopy?.(message.id);
  };

  return (
    <div 
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4 group`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className={`max-w-[80%] ${isUser ? 'order-2' : 'order-1'}`}>
        
        {/* Message Header */}
        <div className={`flex items-center space-x-2 mb-1 ${isUser ? 'justify-end' : 'justify-start'}`}>
          {!isUser && (
            <div className="flex items-center space-x-2">
              <Bot className="w-4 h-4 text-blue-500" />
              <span className="text-sm font-medium text-gray-700">{message.agent_name}</span>
            </div>
          )}
          <span className="text-xs text-gray-500">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        </div>

        {/* Message Content */}
        <div className={`relative p-4 rounded-2xl ${
          isUser 
            ? 'bg-blue-500 text-white' 
            : 'bg-white border border-gray-200 text-gray-900'
        } shadow-sm`}>
          
          {/* Message Text */}
          <div className="whitespace-pre-wrap break-words">
            {message.content}
          </div>

          {/* Mentions */}
          {message.mentions && message.mentions.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <div className="flex flex-wrap gap-1">
                {message.mentions.map((mention, index) => (
                  <span key={index} className={`px-2 py-1 rounded-full text-xs ${
                    isUser ? 'bg-blue-400 text-white' : 'bg-blue-100 text-blue-700'
                  }`}>
                    @{mention}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="mt-2 pt-2 border-t border-gray-200">
              <div className="space-y-1">
                {message.attachments.map((attachment, index) => (
                  <div key={index} className="flex items-center space-x-2 text-xs">
                    <FileText className="w-3 h-3" />
                    <span>{attachment.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Reactions */}
        {Object.keys(reactions).length > 0 && (
          <div className="flex flex-wrap gap-1 mt-2">
            {Object.entries(reactions).map(([emoji, count]) => (
              <button
                key={emoji}
                onClick={() => handleReaction(emoji)}
                className="px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded-full text-xs transition-colors"
              >
                {emoji} {count}
              </button>
            ))}
          </div>
        )}

        {/* Message Actions */}
        {showActions && (
          <div className={`flex items-center space-x-2 mt-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
            <button
              onClick={() => setShowReactions(!showReactions)}
              className="p-1 rounded-full hover:bg-gray-200 transition-colors"
              title="React"
            >
              <Heart className="w-4 h-4 text-gray-500" />
            </button>
            
            <button
              onClick={handleBookmark}
              className="p-1 rounded-full hover:bg-gray-200 transition-colors"
              title="Bookmark"
            >
              <Bookmark className={`w-4 h-4 ${isBookmarked ? 'text-yellow-500 fill-current' : 'text-gray-500'}`} />
            </button>
            
            <button
              onClick={handleCopy}
              className="p-1 rounded-full hover:bg-gray-200 transition-colors"
              title="Copy"
            >
              <Copy className="w-4 h-4 text-gray-500" />
            </button>
            
            <button
              onClick={() => onReply?.(message)}
              className="p-1 rounded-full hover:bg-gray-200 transition-colors"
              title="Reply"
            >
              <MessageSquare className="w-4 h-4 text-gray-500" />
            </button>
          </div>
        )}

        {/* Reaction Picker */}
        {showReactions && (
          <div className="flex space-x-1 mt-2 p-2 bg-white border border-gray-200 rounded-lg shadow-lg">
            {['👍', '❤️', '😊', '🎉', '🤔', '👎'].map((emoji) => (
              <button
                key={emoji}
                onClick={() => {
                  handleReaction(emoji);
                  setShowReactions(false);
                }}
                className="p-1 hover:bg-gray-100 rounded transition-colors"
              >
                {emoji}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Input Component with Advanced Features
const EnhancedMessageInput = ({ onSendMessage, agents, isLoading, placeholder }) => {
  const [message, setMessage] = useState('');
  const [mentions, setMentions] = useState([]);
  const [showMentions, setShowMentions] = useState(false);
  const [mentionQuery, setMentionQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [attachments, setAttachments] = useState([]);
  const [showCommands, setShowCommands] = useState(false);
  
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [message]);

  // Handle @ mentions
  const handleInputChange = (e) => {
    const value = e.target.value;
    setMessage(value);

    // Check for @ mentions
    const lastAtIndex = value.lastIndexOf('@');
    if (lastAtIndex !== -1) {
      const afterAt = value.slice(lastAtIndex + 1);
      if (!afterAt.includes(' ') && afterAt.length <= 20) {
        setMentionQuery(afterAt.toLowerCase());
        setShowMentions(true);
      } else {
        setShowMentions(false);
      }
    } else {
      setShowMentions(false);
    }

    // Check for / commands
    if (value.startsWith('/')) {
      setShowCommands(true);
    } else {
      setShowCommands(false);
    }
  };

  const handleMentionSelect = (agentName) => {
    const lastAtIndex = message.lastIndexOf('@');
    const beforeAt = message.slice(0, lastAtIndex);
    const afterMention = message.slice(lastAtIndex + 1).replace(/^\S*/, '');
    
    setMessage(beforeAt + '@' + agentName + ' ' + afterMention);
    setMentions([...mentions, agentName]);
    setShowMentions(false);
    textareaRef.current?.focus();
  };

  const handleSend = () => {
    if (message.trim() || attachments.length > 0) {
      onSendMessage({
        content: message.trim(),
        mentions: mentions,
        attachments: attachments
      });
      setMessage('');
      setMentions([]);
      setAttachments([]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setAttachments([...attachments, ...files]);
  };

  const removeAttachment = (index) => {
    setAttachments(attachments.filter((_, i) => i !== index));
  };

  const filteredAgents = agents.filter(agent =>
    agent.name.toLowerCase().includes(mentionQuery)
  );

  const commands = [
    { command: '/help', description: 'Show available commands' },
    { command: '/clear', description: 'Clear conversation' },
    { command: '/agents', description: 'List all agents' },
    { command: '/status', description: 'Show system status' },
    { command: '/export', description: 'Export conversation' }
  ];

  const filteredCommands = commands.filter(cmd =>
    cmd.command.includes(message.toLowerCase())
  );

  return (
    <div className="relative">
      
      {/* Mentions Dropdown */}
      {showMentions && filteredAgents.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-40 overflow-y-auto z-10">
          {filteredAgents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => handleMentionSelect(agent.name)}
              className="w-full px-4 py-2 text-left hover:bg-gray-100 flex items-center space-x-2"
            >
              <Bot className="w-4 h-4 text-blue-500" />
              <span className="font-medium">{agent.name}</span>
              <span className="text-sm text-gray-500">{agent.role}</span>
            </button>
          ))}
        </div>
      )}

      {/* Commands Dropdown */}
      {showCommands && filteredCommands.length > 0 && (
        <div className="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg max-h-40 overflow-y-auto z-10">
          {filteredCommands.map((cmd) => (
            <button
              key={cmd.command}
              onClick={() => setMessage(cmd.command + ' ')}
              className="w-full px-4 py-2 text-left hover:bg-gray-100"
            >
              <div className="font-medium text-blue-600">{cmd.command}</div>
              <div className="text-sm text-gray-500">{cmd.description}</div>
            </button>
          ))}
        </div>
      )}

      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="mb-2 p-2 bg-gray-50 rounded-lg">
          <div className="flex flex-wrap gap-2">
            {attachments.map((file, index) => (
              <div key={index} className="flex items-center space-x-2 bg-white px-3 py-1 rounded-full border">
                <FileText className="w-4 h-4 text-gray-500" />
                <span className="text-sm text-gray-700">{file.name}</span>
                <button
                  onClick={() => removeAttachment(index)}
                  className="text-gray-400 hover:text-red-500"
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Container */}
      <div className="flex items-end space-x-2 p-4 bg-white border-t border-gray-200">
        
        {/* File Upload */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
        
        <button
          onClick={() => fileInputRef.current?.click()}
          className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors"
          title="Attach files"
        >
          <Plus className="w-5 h-5" />
        </button>

        {/* Voice Recording */}
        <button
          onClick={() => setIsRecording(!isRecording)}
          className={`p-2 rounded-full transition-colors ${
            isRecording 
              ? 'text-red-500 bg-red-100 hover:bg-red-200' 
              : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
          }`}
          title={isRecording ? 'Stop recording' : 'Start voice recording'}
        >
          {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>

        {/* Message Input */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder={placeholder || "Type your message... Use @ to mention agents or / for commands"}
            className="w-full px-4 py-3 border border-gray-300 rounded-2xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent max-h-32"
            rows={1}
            disabled={isLoading}
          />
          
          {/* Character Count */}
          <div className="absolute bottom-1 right-2 text-xs text-gray-400">
            {message.length}/2000
          </div>
        </div>

        {/* Send Button */}
        <button
          onClick={handleSend}
          disabled={(!message.trim() && attachments.length === 0) || isLoading}
          className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          title="Send message"
        >
          {isLoading ? (
            <Loader className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
    </div>
  );
};

// WebSocket helper hook
const useWebSocket = (onMessage, onHistory, onStatus) => {
  const socketRef = useRef(null);

  useEffect(() => {
    const base = import.meta.env.VITE_WS_URL || import.meta.env.VITE_API_URL || 'http://localhost:5000';
    socketRef.current = io(base + '/swarm', {
      transports: ['websocket', 'polling']
    });

    socketRef.current.on('connect', () => onStatus?.('connected'));
    socketRef.current.on('disconnect', () => onStatus?.('disconnected'));
    socketRef.current.on('message_response', (data) => onMessage?.(data));
    socketRef.current.on('conversation_history', (data) => onHistory?.(data));

    return () => {
      socketRef.current?.disconnect();
    };
  }, []);

  const sendMessage = (payload) => {
    socketRef.current?.emit('user_message', payload);
  };

  const requestHistory = (agentId) => {
    socketRef.current?.emit('history_request', { agent_id: agentId });
  };

  return { sendMessage, requestHistory };
};

// Conversation history component
const ConversationHistory = ({ messages, currentUser }) => (
  <div className="space-y-4">
    {messages.map((msg) => (
      <EnhancedMessage
        key={msg.id}
        message={msg}
        currentUser={currentUser}
      />
    ))}
  </div>
);

// Per-agent chat window
const AgentChatWindow = ({ agent }) => {
  const [messages, setMessages] = useState([]);
  const [status, setStatus] = useState('connecting');
  const { sendMessage, requestHistory } = useWebSocket(
    (data) => setMessages((prev) => [...prev, data.message]),
    (data) => setMessages(data.messages || []),
    setStatus
  );

  useEffect(() => {
    if (agent) {
      requestHistory(agent.id);
    }
  }, [agent]);

  const handleSend = (msg) => {
    sendMessage({ ...msg, agent_id: agent.id });
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-2 border-b">
        <span className="text-sm font-medium">{agent.name}</span>
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <ConversationHistory messages={messages} />
      </div>
      <EnhancedMessageInput onSendMessage={handleSend} agents={[agent]} />
    </div>
  );
};

export {
  EnhancedAgentCard,
  EnhancedMessage,
  EnhancedMessageInput,
  AgentChatWindow,
  ConversationHistory,
  useWebSocket
};

