import React from 'react';
import EnhancedMessage from './EnhancedMessage'; // Assuming EnhancedMessage is in the same directory or adjust path

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

export default ConversationHistory;
