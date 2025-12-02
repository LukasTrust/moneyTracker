/**
 * useRecurring Hook
 * Custom hook for managing recurring transactions (Verträge)
 */
import { useState, useEffect, useCallback } from 'react';
import {
  getAllRecurring,
  getRecurringForAccount,
  getAllRecurringStats,
  getRecurringStatsForAccount,
  detectRecurringForAccount,
  detectAllRecurring,
  updateRecurring,
  toggleRecurringStatus,
  deleteRecurring
} from '../services/recurringService';

/**
 * Hook for managing recurring transactions
 * @param {number|null} accountId - Optional account ID to filter by
 * @returns {Object} - Recurring transactions state and methods
 */
export const useRecurring = (accountId = null) => {
  const [recurring, setRecurring] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Fetch recurring transactions
   */
  const fetchRecurring = useCallback(async (includeInactive = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = accountId 
        ? await getRecurringForAccount(accountId, includeInactive)
        : await getAllRecurring(includeInactive);
      
      setRecurring(data.recurring_transactions || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch recurring transactions');
      console.error('Error fetching recurring:', err);
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  /**
   * Fetch statistics
   */
  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = accountId
        ? await getRecurringStatsForAccount(accountId)
        : await getAllRecurringStats();
      
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch recurring statistics');
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  /**
   * Initial data fetch on mount and when accountId changes
   * Only fetch active contracts for widget display
   */
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        await Promise.all([
          fetchRecurring(false), // Only active contracts
          fetchStats()
        ]);
      } catch (err) {
        console.error('Error fetching initial data:', err);
      }
    };
    
    fetchData();
  }, [fetchRecurring, fetchStats]);

  /**
   * Trigger detection
   */
  const triggerDetection = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = accountId
        ? await detectRecurringForAccount(accountId)
        : await detectAllRecurring();
      
      // Refresh data after detection
      await fetchRecurring();
      await fetchStats();
      
      return result;
    } catch (err) {
      setError(err.message || 'Failed to detect recurring transactions');
      console.error('Error detecting recurring:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [accountId, fetchRecurring, fetchStats]);

  /**
   * Update recurring transaction
   */
  const update = useCallback(async (recurringId, updateData) => {
    setLoading(true);
    setError(null);
    
    try {
      const updated = await updateRecurring(recurringId, updateData);
      
      // Update local state
      setRecurring(prev => 
        prev.map(r => r.id === recurringId ? updated : r)
      );
      
      // Refresh stats
      await fetchStats();
      
      return updated;
    } catch (err) {
      setError(err.message || 'Failed to update recurring transaction');
      console.error('Error updating recurring:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchStats]);

  /**
   * Toggle recurring status
   */
  const toggle = useCallback(async (recurringId, isRecurring) => {
    setLoading(true);
    setError(null);
    
    try {
      const updated = await toggleRecurringStatus(recurringId, isRecurring);
      
      // Update local state
      setRecurring(prev => 
        prev.map(r => r.id === recurringId ? updated : r)
      );
      
      // Refresh stats
      await fetchStats();
      
      return updated;
    } catch (err) {
      setError(err.message || 'Failed to toggle recurring status');
      console.error('Error toggling recurring:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchStats]);

  /**
   * Delete recurring transaction
   */
  const remove = useCallback(async (recurringId) => {
    setLoading(true);
    setError(null);
    
    try {
      await deleteRecurring(recurringId);
      
      // Update local state
      setRecurring(prev => prev.filter(r => r.id !== recurringId));
      
      // Refresh stats
      await fetchStats();
    } catch (err) {
      setError(err.message || 'Failed to delete recurring transaction');
      console.error('Error deleting recurring:', err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchStats]);

  return {
    recurring,
    stats,
    loading,
    error,
    refresh: fetchRecurring,
    refreshStats: fetchStats,
    triggerDetection,
    update,
    toggle,
    remove
  };
};

export default useRecurring;
