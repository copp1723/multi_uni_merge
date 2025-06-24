import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, FileText, Plus, X, Mic, MicOff, Loader } from 'lucide-react';

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

export default EnhancedMessageInput;
