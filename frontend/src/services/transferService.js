/**
 * Transfer Service
 * API calls for managing inter-account transfers
 * Uses amount utilities for consistent money handling
 */
import api from './api';
import { toApiAmount } from '../utils/amount';
import { waitForJob, startPolling } from './jobPoller';

/**
 * Get all transfers, optionally filtered by account and date range
 * @param {Object} params - Query parameters
 * @param {number} params.account_id - Filter by account ID
 * @param {string} params.date_from - Start date (ISO format)
 * @param {string} params.date_to - End date (ISO format)
 * @param {boolean} params.include_details - Include full transaction details
 * @returns {Promise} - Promise resolving to transfers list
 */
export const getAllTransfers = async (params = {}) => {
  const response = await api.get('/transfers', { params });
  return response.data;
};

/**
 * Get a specific transfer by ID with full details
 * @param {number} transferId - Transfer ID
 * @returns {Promise} - Promise resolving to transfer with details
 */
export const getTransfer = async (transferId) => {
  const response = await api.get(`/transfers/${transferId}`);
  return response.data;
};

/**
 * Manually create a transfer link between two transactions
 * @param {Object} transferData - Transfer data
 * @param {number} transferData.from_transaction_id - Source transaction ID (negative amount)
 * @param {number} transferData.to_transaction_id - Destination transaction ID (positive amount)
 * @param {number|string} transferData.amount - Transfer amount (positive)
 * @param {string} transferData.transfer_date - Transfer date (ISO format)
 * @param {string} transferData.notes - Optional notes
 * @returns {Promise} - Promise resolving to created transfer
 */
export const createTransfer = async (transferData) => {
  const payload = {
    ...transferData,
    amount: toApiAmount(transferData.amount)
  };
  const response = await api.post('/transfers', payload);
  return response.data;
};

/**
 * Update transfer notes
 * @param {number} transferId - Transfer ID
 * @param {Object} updateData - Update data
 * @param {string} updateData.notes - New notes
 * @returns {Promise} - Promise resolving to updated transfer
 */
export const updateTransfer = async (transferId, updateData) => {
  const response = await api.put(`/transfers/${transferId}`, updateData);
  return response.data;
};

/**
 * Delete a transfer (unlink two transactions)
 * @param {number} transferId - Transfer ID
 * @returns {Promise} - Promise resolving when deleted
 */
export const deleteTransfer = async (transferId) => {
  const response = await api.delete(`/transfers/${transferId}`);
  return response.data;
};

/**
 * Auto-detect potential transfers
 * @param {Object} params - Detection parameters
 * @param {Array<number>} params.account_ids - Limit to specific accounts
 * @param {string} params.date_from - Start date (ISO format)
 * @param {string} params.date_to - End date (ISO format)
 * @param {number} params.min_confidence - Minimum confidence score (0-1)
 * @param {boolean} params.auto_create - Automatically create high-confidence matches
 * @returns {Promise} - Promise resolving to detection results
 */
export const detectTransfers = async (params = {}, options = {}) => {
  const { waitForCompletion = false, onProgress } = options;
  const response = await api.post('/transfers/detect', params);
  const result = response.data;

  // Support job-based backend responses
  if (result && result.job_id) {
    if (waitForCompletion) {
      if (onProgress) {
        return new Promise((resolve, reject) => {
          startPolling(result.job_id, {
            onUpdate: (job) => {
              onProgress({ status: job.status, progress: job.progress || 0, message: job.message });
            },
            onComplete: (job) => resolve({ ...job.result, job_id: result.job_id, async: true }),
            onError: (err) => reject(err),
          });
        });
      }

      const job = await waitForJob(result.job_id);
      return { ...job.result, job_id: result.job_id, async: true };
    }

    return { job_id: result.job_id, async: true, status: 'pending' };
  }

  return result;
};

/**
 * Get transfer statistics
 * @param {number} accountId - Optional account ID filter
 * @returns {Promise} - Promise resolving to transfer statistics
 */
export const getTransferStats = async (accountId = null) => {
  const params = accountId ? { account_id: accountId } : {};
  const response = await api.get('/transfers/stats', { params });
  return response.data;
};

/**
 * Check if a transaction is part of a transfer
 * @param {number} transactionId - Transaction ID
 * @returns {Promise} - Promise resolving to transfer or null
 */
export const getTransferForTransaction = async (transactionId) => {
  const response = await api.get(`/transactions/${transactionId}/transfer`);
  return response.data;
};

/**
 * Bulk detect and create transfers for all accounts
 * @param {Object} params - Detection parameters
 * @param {number} params.min_confidence - Minimum confidence (default 0.85)
 * @returns {Promise} - Promise resolving to detection results
 */
export const bulkDetectAndCreate = async (params = { auto_create: true, min_confidence: 0.85 }, options = {}) => {
  const { waitForCompletion = false, onProgress } = options;
  const response = await api.post('/transfers/detect', params);
  const result = response.data;

  if (result && result.job_id) {
    if (waitForCompletion) {
      if (onProgress) {
        return new Promise((resolve, reject) => {
          startPolling(result.job_id, {
            onUpdate: (job) => onProgress({ status: job.status, progress: job.progress || 0, message: job.message }),
            onComplete: (job) => resolve({ ...job.result, job_id: result.job_id, async: true }),
            onError: (err) => reject(err),
          });
        });
      }

      const job = await waitForJob(result.job_id);
      return { ...job.result, job_id: result.job_id, async: true };
    }

    return { job_id: result.job_id, async: true, status: 'pending' };
  }

  return result;
};

export default {
  getAllTransfers,
  getTransfer,
  createTransfer,
  updateTransfer,
  deleteTransfer,
  detectTransfers,
  getTransferStats,
  getTransferForTransaction,
  bulkDetectAndCreate
};
