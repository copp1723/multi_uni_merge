import React, { useState, useEffect } from 'react';
import ConversationHistory from './ConversationHistory'; // Assuming ConversationHistory is in the same directory
import EnhancedMessageInput from './EnhancedMessageInput'; // Assuming EnhancedMessageInput is in the same directory
import useWebSocket from '../hooks/useWebSocket'; // Adjust path as needed

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
      setMessages([]); // Clear messages when agent changes
    }
  }, [agent, requestHistory]); // Added requestHistory to dependencies

  const handleSend = (msg) => {
    sendMessage({ ...msg, agent_id: agent.id });
  };

  if (!agent) {
    return <div className="flex items-center justify-center h-full text-gray-500">Select an agent to start chatting.</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-2 border-b">
        <span className="text-sm font-medium">{agent.name}</span>
        <span className="text-xs text-gray-500 capitalize">{status}</span>
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <ConversationHistory messages={messages} currentUser="user" /> {/* Assuming a currentUser prop is needed */}
      </div>
      <EnhancedMessageInput
        onSendMessage={handleSend}
        agents={[agent]} // EnhancedMessageInput might expect an array of agents
        placeholder={`Message ${agent.name}...`}
      />
    </div>
  );
};

export default AgentChatWindow;
