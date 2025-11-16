/**
 * Import History API Service
 * 
 * Handles all API calls for import history tracking and rollback functionality
 */

import api from './api';

const IMPORT_HISTORY_BASE = '/import-history';

/**
 * Get import history for an account
 * 
 * @param {number} accountId - Account ID to filter by (optional)
 * @param {number} limit - Maximum number of records
 * @param {number} offset - Pagination offset
 * @returns {Promise} Import history list with statistics
 */
export const getImportHistory = async (accountId = null, limit = 100, offset = 0) => {
  const params = { limit, offset };
  if (accountId) {
    params.account_id = accountId;
  }
  
  const response = await api.get(`${IMPORT_HISTORY_BASE}/history`, { params });
  return response.data;
};

/**
 * Get detailed statistics for a specific import
 * 
 * @param {number} importId - Import ID
 * @returns {Promise} Import statistics
 */
export const getImportDetails = async (importId) => {
  const response = await api.get(`${IMPORT_HISTORY_BASE}/history/${importId}`);
  return response.data;
};

/**
 * Rollback an import by deleting all associated transactions
 * 
 * @param {number} importId - Import ID to rollback
 * @param {boolean} confirm - Confirmation flag (must be true)
 * @returns {Promise} Rollback result
 */
export const rollbackImport = async (importId, confirm = true) => {
  const response = await api.post(`${IMPORT_HISTORY_BASE}/rollback`, {
    import_id: importId,
    confirm: confirm,
  });
  return response.data;
};

/**
 * Delete an import history record (metadata only, not the transactions)
 * 
 * @param {number} importId - Import ID to delete
 * @returns {Promise} Success response
 */
export const deleteImportHistory = async (importId) => {
  const response = await api.delete(`${IMPORT_HISTORY_BASE}/history/${importId}`);
  return response.data;
};

export default {
  getImportHistory,
  getImportDetails,
  rollbackImport,
  deleteImportHistory,
};
