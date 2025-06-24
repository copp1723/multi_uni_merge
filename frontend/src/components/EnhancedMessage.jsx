import React, { useState } from 'react';
import { Bot, FileText, Heart, Bookmark, Copy, MessageSquare } from 'lucide-react';

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

export default EnhancedMessage;
