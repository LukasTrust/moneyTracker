/**
 * CSV Import API Service
 * 
 * Handles all API calls for the new combined CSV Import & Mapping feature
 */

import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

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
 * Import CSV file with custom mapping
 * 
 * @param {number} accountId - Target account ID
 * @param {Object} mapping - Mapping configuration
 * @param {File} file - CSV file to import
 * @returns {Promise} Import results with statistics
 */
export const importCsv = async (accountId, mapping, file) => {
  const formData = new FormData();
  formData.append('account_id', accountId.toString());
  formData.append('mapping_json', JSON.stringify(mapping));
  formData.append('file', file);

  const response = await api.post('/csv-import/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Validate mapping configuration
 * 
 * @param {Object} mapping - Mapping configuration to validate
 * @returns {Object} Validation result with errors
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

export default {
  previewCsv,
  suggestMapping,
  importCsv,
  validateMapping,
  getFieldLabel,
  getFieldIcon,
};
