import React, { useState } from 'react';
import { User, BarChart3, Code, Lightbulb, Search, Bot, ChevronDown, ChevronUp } from 'lucide-react';

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
            {typeof capability === 'string' ? capability : capability.name || capability.description || 'Capability'}
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
                  {typeof capability === 'string' ? capability : capability.name || capability.description || 'Capability'}
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

export default EnhancedAgentCard;
