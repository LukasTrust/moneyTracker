/**
 * Recurring Transaction (Verträge) Service
 * API calls for managing recurring transactions
 */
import api from './api';

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
export const detectRecurringForAccount = async (accountId) => {
  const response = await api.post(`/accounts/${accountId}/recurring-transactions/detect`);
  return response.data;
};

/**
 * Trigger recurring transaction detection for all accounts
 * @returns {Promise} - Promise resolving to detection statistics
 */
export const detectAllRecurring = async () => {
  const response = await api.post('/accounts/recurring-transactions/detect-all');
  return response.data;
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
  deleteRecurring
};
