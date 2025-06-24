// Configuration utility for API and WebSocket URLs

const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL.replace(/\/$/, ''); // Remove trailing slash
  }
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return window.location.origin;
  }
  return 'http://localhost:5000';
};

const getWsBaseUrl = () => {
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL.replace(/\/$/, ''); // Remove trailing slash
  }
  // If WS_URL is not set, try to derive from API_URL or current location
  // This assumes WebSocket might be served from the same base path or a known relative path.
  // For this project, WS is at the root of the API base.
  const apiBase = getApiBaseUrl();
  // If API base is http, ws should be ws. If https, wss.
  if (apiBase.startsWith('https://')) {
    return apiBase.replace(/^https:/, 'wss:');
  }
  return apiBase.replace(/^http:/, 'ws:');
};

export const API_BASE_URL = getApiBaseUrl();
export const WS_BASE_URL = getWsBaseUrl(); // This will be like 'ws://localhost:5000' or 'wss://yourdomain.com'
