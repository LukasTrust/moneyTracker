/**
 * Comparison Service - API calls for period comparison
 */
import api from './api';

/**
 * Get period comparison data
 * @param {number} accountId - Account ID
 * @param {string} comparisonType - 'month' or 'year'
 * @param {string} period1 - First period (YYYY-MM or YYYY)
 * @param {string} period2 - Second period (YYYY-MM or YYYY)
 * @param {number} topLimit - Number of top recipients (default: 5)
 * @returns {Promise} Comparison data
 */
export const getComparison = async (accountId, comparisonType, period1, period2, topLimit = 5) => {
  const response = await api.get(`/comparison/${accountId}`, {
    params: {
      comparison_type: comparisonType,
      period1,
      period2,
      top_limit: topLimit,
    },
  });
  return response.data;
};

/**
 * Get quick comparison with preset
 * @param {number} accountId - Account ID
 * @param {string} compareTo - Preset type ('last_month', 'last_year', 'month_yoy', 'year_yoy')
 * @param {string} referencePeriod - Reference period (optional)
 * @param {number} topLimit - Number of top recipients (default: 5)
 * @returns {Promise} Comparison data
 */
export const getQuickComparison = async (accountId, compareTo, referencePeriod = null, topLimit = 5) => {
  const params = {
    compare_to: compareTo,
    top_limit: topLimit,
  };
  
  if (referencePeriod) {
    params.reference_period = referencePeriod;
  }
  
  const response = await api.get(`/comparison/${accountId}/quick-compare`, { params });
  return response.data;
};

export default {
  getComparison,
  getQuickComparison,
};
