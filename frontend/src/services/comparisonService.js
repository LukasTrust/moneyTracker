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

/**
 * Get multi-year comparison
 * @param {number} accountId - Account ID
 * @param {Array<number>} years - Array of years to compare
 * @param {number} topLimit - Number of top recipients (default: 5)
 * @returns {Promise} Multi-year comparison data
 */
export const getMultiYearComparison = async (accountId, years, topLimit = 5) => {
  const response = await api.get(`/comparison/${accountId}/multi-year`, {
    params: {
      years: years.join(','),
      top_limit: topLimit,
    },
  });
  return response.data;
};

/**
 * Get quarterly comparison
 * @param {number} accountId - Account ID
 * @param {number} year - Year for quarterly comparison
 * @param {boolean} compareToPreviousYear - Compare to previous year's quarters
 * @returns {Promise} Quarterly comparison data
 */
export const getQuarterlyComparison = async (accountId, year, compareToPreviousYear = false) => {
  const response = await api.get(`/comparison/${accountId}/quarterly`, {
    params: {
      year,
      compare_to_previous_year: compareToPreviousYear,
    },
  });
  return response.data;
};

/**
 * Get benchmark analysis
 * @param {number} accountId - Account ID
 * @param {number} year - Year for benchmark (optional)
 * @param {number} month - Month for benchmark (optional, 1-12)
 * @returns {Promise} Benchmark analysis data
 */
export const getBenchmarkAnalysis = async (accountId, year = null, month = null) => {
  const params = {};
  
  if (year) {
    params.year = year;
  }
  
  if (month) {
    params.month = month;
  }
  
  const response = await api.get(`/comparison/${accountId}/benchmark`, { params });
  return response.data;
};

export default {
  getComparison,
  getQuickComparison,
  getMultiYearComparison,
  getQuarterlyComparison,
  getBenchmarkAnalysis,
};
