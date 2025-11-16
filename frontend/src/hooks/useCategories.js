import { useEffect } from 'react';
import { useCategoryStore } from '../store';

/**
 * Custom Hook for Category Management
 * 
 * Provides easy access to category store with automatic fetching and caching
 * 
 * @param {boolean} autoFetch - Automatically fetch categories on mount (default: true)
 * @returns {object} Category store state and actions
 * 
 * @example
 * const { categories, loading, error, createCategory } = useCategories();
 */
export function useCategories(autoFetch = true) {
  const store = useCategoryStore();

  useEffect(() => {
    if (autoFetch) {
      store.fetchCategories();
    }
  }, [autoFetch]);

  return store;
}

/**
 * Custom Hook for Category Mappings
 * 
 * Fetches and manages category mappings for a specific account
 * 
 * @param {number} accountId - Account ID
 * @returns {object} { mappings, loading, error, updateMapping, bulkUpdateMappings }
 * 
 * @example
 * const { mappings, updateMapping } = useCategoryMappings(accountId);
 */
export function useCategoryMappings(accountId) {
  const { mappings, loading, error, fetchMappings, updateMapping, bulkUpdateMappings } = useCategoryStore();

  useEffect(() => {
    if (accountId) {
      fetchMappings(accountId);
    }
  }, [accountId]);

  return {
    mappings: mappings[accountId] || {},
    loading,
    error,
    updateMapping: (recipient, categoryId) => updateMapping(accountId, recipient, categoryId),
    bulkUpdateMappings: (newMappings) => bulkUpdateMappings(accountId, newMappings),
    refetch: () => fetchMappings(accountId),
  };
}
