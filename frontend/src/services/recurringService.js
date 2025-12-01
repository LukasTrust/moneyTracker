/**
 * Recurring Transaction (Verträge) Service
 * API calls for managing recurring transactions
 */
import api from './api';
import { waitForJob, startPolling } from './jobPoller';

/**
 * Get all recurring transactions for a specific account
 * @param {number} accountId - Account ID
 * @param {boolean} includeInactive - Include inactive recurring transactions
 * @returns {Promise} - Promise resolving to recurring transactions list
 */
export const getRecurringForAccount = async (accountId, includeInactive = false) => {
  const response = await api.get(`/accounts/${accountId}/recurring-transactions`, {
    params: { include_inactive: includeInactive }
  });
  return response.data;
};

/**
 * Get all recurring transactions across all accounts
 * @param {boolean} includeInactive - Include inactive recurring transactions
 * @returns {Promise} - Promise resolving to recurring transactions list
 */
export const getAllRecurring = async (includeInactive = false) => {
  const response = await api.get('/accounts/recurring-transactions', {
    params: { include_inactive: includeInactive }
  });
  return response.data;
};

/**
 * Get recurring transaction statistics for an account
 * @param {number} accountId - Account ID
 * @returns {Promise} - Promise resolving to statistics
 */
export const getRecurringStatsForAccount = async (accountId) => {
  const response = await api.get(`/accounts/${accountId}/recurring-transactions/stats`);
  return response.data;
};

/**
 * Get recurring transaction statistics across all accounts
 * @returns {Promise} - Promise resolving to statistics
 */
export const getAllRecurringStats = async () => {
  const response = await api.get('/accounts/recurring-transactions/stats');
  return response.data;
};

/**
 * Manually trigger recurring transaction detection for an account
 * @param {number} accountId - Account ID
 * @returns {Promise} - Promise resolving to detection statistics
 */
export const detectRecurringForAccount = async (accountId, options = {}) => {
  const { waitForCompletion = false, onProgress } = options;
  const response = await api.post(`/accounts/${accountId}/recurring-transactions/detect`);
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

/**
 * Trigger recurring transaction detection for all accounts
 * @returns {Promise} - Promise resolving to detection statistics
 */
export const detectAllRecurring = async (options = {}) => {
  const { waitForCompletion = false, onProgress } = options;
  const response = await api.post('/accounts/recurring-transactions/detect-all');
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

/**
 * Update a recurring transaction (notes, category, active status)
 * @param {number} recurringId - Recurring transaction ID
 * @param {Object} updateData - Update data (notes, is_active, category_id)
 * @returns {Promise} - Promise resolving to updated recurring transaction
 */
export const updateRecurring = async (recurringId, updateData) => {
  const response = await api.patch(`/accounts/recurring-transactions/${recurringId}`, updateData);
  return response.data;
};

/**
 * Toggle recurring status (mark/unmark as recurring)
 * @param {number} recurringId - Recurring transaction ID
 * @param {boolean} isRecurring - True to mark as recurring, false to unmark
 * @returns {Promise} - Promise resolving to updated recurring transaction
 */
export const toggleRecurringStatus = async (recurringId, isRecurring) => {
  const response = await api.post(`/accounts/recurring-transactions/${recurringId}/toggle`, {
    is_recurring: isRecurring
  });
  return response.data;
};

/**
 * Get detailed information about a specific recurring transaction
 * @param {number} recurringId - Recurring transaction ID
 * @returns {Promise} - Promise resolving to detailed recurring transaction
 */
export const getRecurringDetails = async (recurringId) => {
  const response = await api.get(`/accounts/recurring-transactions/${recurringId}`);
  return response.data;
};

/**
 * Delete a recurring transaction
 * @param {number} recurringId - Recurring transaction ID
 * @returns {Promise} - Promise resolving to void
 */
export const deleteRecurring = async (recurringId) => {
  const response = await api.delete(`/accounts/recurring-transactions/${recurringId}`);
  return response.data;
};

export default {
  getRecurringForAccount,
  getAllRecurring,
  getRecurringStatsForAccount,
  getAllRecurringStats,
  detectRecurringForAccount,
  detectAllRecurring,
  updateRecurring,
  toggleRecurringStatus,
  deleteRecurring,
  getRecurringDetails
};
