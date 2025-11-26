import axios from 'axios';

// API Basis-Konfiguration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 Sekunden
});

// Request Interceptor für Logging (optional)
api.interceptors.request.use(
  (config) => {
    // Only log requests in development to avoid leaking information in production
    if (import.meta.env.DEV) {
      // use console.debug which is easier to filter
      console.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }
    // Attach Authorization header if a token is present (simple client-side JWT handling)
    try {
      const token = localStorage.getItem('token') || null;
      if (token) {
        // Do not log the token value
        if (import.meta.env.DEV) console.debug('API Request: attaching Authorization header (masked)');
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (err) {
      // localStorage may throw in some environments; fail gracefully
      if (import.meta.env.DEV) console.warn('Could not read token from localStorage', err);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response Interceptor für Error Handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Log errors; minimize noise in production
    if (import.meta.env.DEV) {
      if (error.response) {
        console.error('API Error:', error.response.status, error.response.data);
      } else if (error.request) {
        console.error('Network Error:', error.message);
      } else {
        console.error('Error:', error.message);
      }
    }
    return Promise.reject(error);
  }
);

export default api;
