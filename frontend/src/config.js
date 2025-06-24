// Frontend configuration
// This file ensures the frontend always uses the correct API URL

export const getApiUrl = () => {
  // Always use the current origin in production
  // This prevents hardcoded URLs from breaking deployments
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return window.location.origin;
  }
  
  // Local development
  return import.meta.env.VITE_API_URL || 'http://localhost:5000';
};

export const API_BASE_URL = getApiUrl();
export const SOCKET_URL = `${API_BASE_URL}/swarm`;