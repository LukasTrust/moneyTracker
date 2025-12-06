import axios from 'axios';
import { useUIStore } from '../store';

// API Basis-Konfiguration
// In production, API requests go through Nginx proxy at /api/v1
// In development, use VITE_API_URL environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 Sekunden
});

/**
 * Normalize list responses to consistent shape: { items, total }
 * Audit reference: 09_frontend_action_plan.md - P1 API normalizer
 * 
 * Handles various backend response shapes:
 * - Direct arrays: [item1, item2] -> { items: [...], total: N }
 * - Already normalized: { items: [...], total: N } -> unchanged
 * - Paginated: { items, total, limit, offset } -> { items, total }
 */
function normalizeListResponse(data) {
  // Already in correct shape
  if (data && typeof data === 'object' && Array.isArray(data.items)) {
    return {
      items: data.items,
      total: data.total ?? data.items.length
    };
  }
  
  // Direct array
  if (Array.isArray(data)) {
    return {
      items: data,
      total: data.length
    };
  }
  
  // Other shapes - return as-is
  return data;
}

/**
 * Normalize error responses to consistent shape
 * { error: { status, code, message, details } }
 */
function normalizeErrorResponse(error) {
  const data = error.response?.data;
  let message = error.message || 'Serverfehler';
  let code = null;
  let details = null;

  if (data) {
    // New standardized shape: { success: false, error: { status, code, message, details } }
    if (data.success === false && data.error) {
      message = data.error.message || message;
      code = data.error.code;
      details = data.error.details;
    } else if (data.message) {
      // Legacy or simple shape
      message = data.message;
    } else if (data.detail) {
      // FastAPI default error shape
      message = data.detail;
    }
  }

  return {
    success: false,
    status: error.response?.status || null,
    error: {
      code: code || error.response?.status || 'unknown_error',
      message,
      details,
    },
  };
}

// Request Interceptor für Logging (optional)
api.interceptors.request.use(
  (config) => {
    // Only log requests in development to avoid leaking information in production
    if (import.meta.env.DEV) {
      console.debug(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    }

    // Attach Authorization header if a token is present (simple client-side JWT handling)
    try {
      const token = localStorage.getItem('token') || null;
      if (token) {
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

// Response Interceptor for normalization and error handling
// Audit reference: 09_frontend_action_plan.md - P1 API normalizer
api.interceptors.response.use(
  (response) => {
    // Normalize list responses if they look like lists
    // Only apply to GET requests to avoid breaking POST/PUT/DELETE responses
    if (response.config.method === 'get' && response.data) {
      const normalized = normalizeListResponse(response.data);
      
      // Only replace if we actually normalized something
      if (normalized !== response.data) {
        response.data = normalized;
      }
    }
    
    return response;
  },
  (error) => {
    // Normalize and surface standardized backend errors
    const normalized = normalizeErrorResponse(error);
    
    // Try to show a toast using the UI store (safe when used outside React)
    try {
      const ui = useUIStore && useUIStore.getState ? useUIStore.getState() : null;
      if (ui && ui.showError) {
        ui.showError(normalized.error.message);
      }
    } catch (e) {
      if (import.meta.env.DEV) console.warn('Failed to show toast from api interceptor', e);
    }

    // Attach normalized error info for callers that want structured data
    error.normalized = normalized;

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
