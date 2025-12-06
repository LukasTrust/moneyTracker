/**
 * CSV Import API Service
 * 
 * Handles all API calls for the new combined CSV Import & Mapping feature
 * Supports both synchronous and asynchronous (job-based) imports
 * 
 * Audit reference: 09_frontend_action_plan.md - P0 CSV import async
 */

import axios from 'axios';
import { waitForJob, startPolling } from './jobPoller';

// Use relative URL for production (goes through Nginx proxy)
// or VITE_API_URL for development
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Preview CSV file without importing
 * 
 * @param {File} file - CSV file to preview
 * @returns {Promise} Preview data with headers, sample rows, and delimiter
 */
export const previewCsv = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/csv-import/preview', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Get intelligent mapping suggestions for CSV headers
 * 
 * @param {File} file - CSV file to analyze
 * @returns {Promise} Mapping suggestions with confidence scores
 */
export const suggestMapping = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/csv-import/suggest-mapping', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Validate saved mappings against CSV file
 * 
 * @param {number} accountId - Account ID with saved mappings
 * @param {File} file - CSV file to validate against
 * @returns {Promise} Validation result with missing/valid headers
 */
export const validateSavedMapping = async (accountId, file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post(`/csv-import/validate-mapping/${accountId}`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Import CSV file with custom mapping
 * Supports both sync and async (job-based) imports
 * 
 * @param {number} accountId - Target account ID
 * @param {Object} mapping - Mapping configuration
 * @param {File} file - CSV file to import
 * @param {Object} options - Import options
 * @param {boolean} options.waitForCompletion - If true, waits for async jobs to complete
 * @param {Function} options.onProgress - Progress callback for async jobs
 * @returns {Promise} Import results or job info
 */
export const importCsv = async (accountId, mapping, file, options = {}) => {
  const { waitForCompletion = false, onProgress } = options;
  
  const formData = new FormData();
  formData.append('account_id', accountId.toString());
  formData.append('mapping_json', JSON.stringify(mapping));
  formData.append('file', file);

  const response = await api.post('/csv-import/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  const result = response.data;
  
  // Check if backend returned a job_id (async import)
  if (result.job_id) {
    // If caller wants to wait, poll the job
    if (waitForCompletion) {
      // Use job poller with progress callback
      if (onProgress) {
        return new Promise((resolve, reject) => {
          startPolling(result.job_id, {
            onUpdate: (job) => {
              if (onProgress) {
                onProgress({
                  status: job.status,
                  progress: job.progress || 0,
                  message: job.message
                });
              }
            },
            onComplete: (job) => {
              resolve({
                ...job.result,
                job_id: result.job_id,
                async: true
              });
            },
            onError: (error) => reject(error)
          });
        });
      } else {
        // Simple wait without progress
        const job = await waitForJob(result.job_id);
        return {
          ...job.result,
          job_id: result.job_id,
          async: true
        };
      }
    }
    
    // Return job info immediately (caller will poll separately)
    return {
      job_id: result.job_id,
      async: true,
      status: 'pending'
    };
  }
  
  // Synchronous import - return results directly
  return {
    ...result,
    async: false
  };
};

/**
 * Get import job status
 * 
 * @param {string|number} jobId - Job ID to check
 * @returns {Promise} Job status and results
 */
export const getImportJobStatus = async (jobId) => {
  const response = await api.get(`/jobs/${jobId}`);
  return response.data;
};

/**
 * Validate mapping configuration
 * 
 * @param {Object} mapping - Mapping configuration
 * @returns {Object} { isValid: boolean, errors: string[] }
 */
export const validateMapping = (mapping) => {
  const errors = [];
  const required = ['date', 'amount', 'recipient'];
  const optional = ['purpose'];
  const allFields = [...required, ...optional];

  // Check required fields
  required.forEach((field) => {
    if (!mapping[field]) {
      errors.push(`${field} ist ein Pflichtfeld und muss gemappt werden`);
    }
  });

  // Check for duplicate mappings (only non-empty values)
  const usedHeaders = new Set();
  Object.entries(mapping).forEach(([field, header]) => {
    if (header && usedHeaders.has(header)) {
      errors.push(`CSV-Header "${header}" ist mehrfach zugeordnet`);
    }
    if (header) {
      usedHeaders.add(header);
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
  };
};

/**
 * Get field label in German
 * 
 * @param {string} fieldName - Field name (date, amount, recipient, purpose)
 * @returns {string} German label
 */
export const getFieldLabel = (fieldName) => {
  const labels = {
    date: 'Datum',
    amount: 'Betrag',
    recipient: 'Empfänger/Absender',
    purpose: 'Verwendungszweck',
  };
  return labels[fieldName] || fieldName;
};

/**
 * Get field icon
 * 
 * @param {string} fieldName - Field name
 * @returns {string} Icon emoji
 */
export const getFieldIcon = (fieldName) => {
  const icons = {
    date: '📅',
    amount: '💰',
    recipient: '👤',
    purpose: '📝',
  };
  return icons[fieldName] || '📋';
};

/**
 * Import multiple CSV files with the same mapping (bulk import)
 * 
 * @param {number} accountId - Target account ID
 * @param {Object} mapping - Mapping configuration
 * @param {File[]} files - Array of CSV files to import
 * @param {Object} options - Import options
 * @param {Function} options.onProgress - Progress callback for each file
 * @returns {Promise} Bulk import results
 */
export const bulkImportCsv = async (accountId, mapping, files, options = {}) => {
  const { onProgress } = options;
  
  const formData = new FormData();
  formData.append('account_id', accountId.toString());
  formData.append('mapping_json', JSON.stringify(mapping));
  
  // Append all files
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await api.post('/csv-import/bulk-import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress) {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress({
          status: 'uploading',
          progress: percentCompleted,
          message: `Uploading files... ${percentCompleted}%`
        });
      }
    }
  });

  return response.data;
};

export default {
  previewCsv,
  suggestMapping,
  validateSavedMapping,
  importCsv,
  bulkImportCsv,
  validateMapping,
  getFieldLabel,
  getFieldIcon,
};
