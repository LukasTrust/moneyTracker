import { useState, useEffect, useCallback } from 'react';
import insightsService from '../services/insightsService';

/**
 * Custom Hook for Insights Management
 * 
 * Provides easy access to insights with automatic fetching, caching, and state management
 * 
 * @param {Object} options - Configuration options
 * @param {number} options.accountId - Account ID (null = all accounts + global)
 * @param {boolean} options.autoFetch - Automatically fetch on mount (default: true)
 * @param {boolean} options.autoGenerate - Automatically generate if empty (default: false)
 * @param {number} options.refreshInterval - Auto-refresh interval in ms (default: null = no auto-refresh)
 * @returns {Object} Insights state and actions
 * 
 * @example
 * const { insights, loading, error, refreshInsights, dismissInsight } = useInsights({ accountId: 1 });
 */
export function useInsights({ 
  accountId = null, 
  autoFetch = true, 
  autoGenerate = false,
  refreshInterval = null 
} = {}) {
  const [insights, setInsights] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);

  /**
   * Fetch insights from API
   */
  const fetchInsights = useCallback(async (params = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await insightsService.getInsights({
        accountId,
        ...params
      });
      
      setInsights(data.insights || []);
      return data;
    } catch (err) {
      console.error('Error fetching insights:', err);
      setError(err.response?.data?.detail || err.message || 'Fehler beim Laden der Insights');
      return null;
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  /**
   * Generate new insights
   */
  const generateInsights = useCallback(async (params = {}) => {
    setGenerating(true);
    setError(null);
    
    try {
      const result = await insightsService.generateInsights({
        accountId,
        ...params
      });
      
      // Refresh insights after generation
      if (result.success && result.insights_generated > 0) {
        await fetchInsights();
      }
      
      return result;
    } catch (err) {
      console.error('Error generating insights:', err);
      setError(err.response?.data?.detail || err.message || 'Fehler beim Generieren der Insights');
      return { success: false, message: err.message };
    } finally {
      setGenerating(false);
    }
  }, [accountId, fetchInsights]);

  /**
   * Dismiss an insight
   */
  const dismissInsight = useCallback(async (insightId) => {
    try {
      await insightsService.dismissInsight(insightId);
      
      // Optimistically update local state
      setInsights(prev => prev.filter(insight => insight.id !== insightId));
      
      return { success: true };
    } catch (err) {
      console.error('Error dismissing insight:', err);
      setError(err.response?.data?.detail || err.message || 'Fehler beim Ausblenden des Insights');
      return { success: false, message: err.message };
    }
  }, []);

  /**
   * Delete an insight permanently
   */
  const deleteInsight = useCallback(async (insightId) => {
    try {
      await insightsService.deleteInsight(insightId);
      
      // Optimistically update local state
      setInsights(prev => prev.filter(insight => insight.id !== insightId));
      
      return { success: true };
    } catch (err) {
      console.error('Error deleting insight:', err);
      setError(err.response?.data?.detail || err.message || 'Fehler beim Löschen des Insights');
      return { success: false, message: err.message };
    }
  }, []);

  /**
   * Fetch statistics
   */
  const fetchStatistics = useCallback(async () => {
    try {
      const stats = await insightsService.getStatistics(accountId);
      setStatistics(stats);
      return stats;
    } catch (err) {
      console.error('Error fetching statistics:', err);
      return null;
    }
  }, [accountId]);

  /**
   * Refresh insights (refetch from API)
   */
  const refreshInsights = useCallback(() => {
    return fetchInsights();
  }, [fetchInsights]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchInsights().then(data => {
        // Auto-generate if no insights exist and autoGenerate is enabled
        if (autoGenerate && data && data.insights.length === 0) {
          generateInsights();
        }
      });
    }
  }, [autoFetch, autoGenerate]); // eslint-disable-line react-hooks/exhaustive-deps

  // Auto-refresh interval
  useEffect(() => {
    if (refreshInterval && refreshInterval > 0) {
      const intervalId = setInterval(() => {
        fetchInsights();
      }, refreshInterval);

      return () => clearInterval(intervalId);
    }
  }, [refreshInterval, fetchInsights]);

  return {
    // State
    insights,
    statistics,
    loading,
    error,
    generating,
    
    // Computed
    hasInsights: insights.length > 0,
    activeInsights: insights.filter(i => !i.is_dismissed),
    dismissedInsights: insights.filter(i => i.is_dismissed),
    
    // Actions
    fetchInsights,
    generateInsights,
    dismissInsight,
    deleteInsight,
    refreshInsights,
    fetchStatistics
  };
}

/**
 * Simplified hook for dashboard - auto-fetches and auto-generates
 * 
 * @param {number} accountId - Account ID (null = global)
 * @returns {Object} Insights state and actions
 */
export function useDashboardInsights(accountId = null) {
  return useInsights({
    accountId,
    autoFetch: true,
    autoGenerate: true,
    refreshInterval: null // No auto-refresh to save API calls
  });
}

export default useInsights;
