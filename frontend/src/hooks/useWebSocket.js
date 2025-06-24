import { useEffect, useRef } from 'react';
import { io } from 'socket.io-client';

// WebSocket helper hook
const useWebSocket = (onMessage, onHistory, onStatus) => {
import { WS_BASE_URL } from '../utils/config'; // Import centralized WS_BASE_URL

// WebSocket helper hook
const useWebSocket = (onMessage, onHistory, onStatus) => {
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = io(`${WS_BASE_URL}/swarm`, { // Use WS_BASE_URL
      transports: ['websocket', 'polling']
    });

    socketRef.current.on('connect', () => onStatus?.('connected'));
    socketRef.current.on('disconnect', () => onStatus?.('disconnected'));
    socketRef.current.on('message_response', (data) => onMessage?.(data));
    socketRef.current.on('conversation_history', (data) => onHistory?.(data));

    return () => {
      socketRef.current?.disconnect();
    };
  }, [onMessage, onHistory, onStatus]); // Added dependencies to useEffect

  const sendMessage = (payload) => {
    socketRef.current?.emit('user_message', payload);
  };

  const requestHistory = (agentId) => {
    socketRef.current?.emit('history_request', { agent_id: agentId });
  };

  return { sendMessage, requestHistory };
};

export default useWebSocket;
