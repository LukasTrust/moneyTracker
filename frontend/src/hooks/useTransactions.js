import { useState, useEffect, useCallback } from 'react';
import dataService from '../services/dataService';
import { useFilterStore } from '../store';

/**
 * Custom Hook for Transaction Data with Filtering
 * 
 * Automatically reacts to filter changes and fetches data accordingly
 * 
 * @param {number} accountId - Account ID (null for all accounts)
 * @param {object} options - { enableFilters: boolean, limit: number, offset: number }
 * @returns {object} { data, total, loading, error, refetch }
 * 
 * @example
 * const { data, loading, error, refetch } = useTransactions(accountId);
 */
export function useTransactions(accountId = null, options = {}) {
  const { enableFilters = true, limit = 100, offset = 0 } = options;

  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get filter params
  const getQueryParams = useFilterStore((state) => state.getQueryParams);
  const filterParams = enableFilters ? getQueryParams() : {};

  const fetchData = useCallback(async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const params = {
        ...filterParams,
        limit,
        offset,
      };

      const response = await dataService.getData(accountId, params);
      setData(response.data || response.transactions || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Transaktionen');
    } finally {
      setLoading(false);
    }
  }, [accountId, JSON.stringify(filterParams), limit, offset]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    data, 
    total, 
    loading, 
    error, 
    refetch: fetchData 
  };
}

/**
 * Custom Hook for Summary/KPI Data
 * 
 * Fetches aggregated summary data (income, expenses, balance, etc.)
 * 
 * @param {number} accountId - Account ID (null for all accounts)
 * @param {boolean} enableFilters - Use filter store (default: true)
 * @returns {object} { summary, loading, error, refetch }
 * 
 * @example
 * const { summary, loading } = useSummary(accountId);
 */
export function useSummary(accountId = null, enableFilters = true) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getQueryParams = useFilterStore((state) => state.getQueryParams);
  const filterParams = enableFilters ? getQueryParams() : {};

  const fetchSummary = useCallback(async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getSummary(accountId, filterParams);
      setSummary(response);
    } catch (err) {
      console.error('Error fetching summary:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Zusammenfassung');
    } finally {
      setLoading(false);
    }
  }, [accountId, JSON.stringify(filterParams)]);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  return { 
    summary, 
    loading, 
    error, 
    refetch: fetchSummary 
  };
}

/**
 * Custom Hook for Category Distribution
 * 
 * Fetches data grouped by categories for pie charts
 * 
 * @param {number} accountId - Account ID
 * @param {boolean} enableFilters - Use filter store (default: true)
 * @returns {object} { data, loading, error, refetch }
 */
export function useCategoryDistribution(accountId, enableFilters = true) {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getQueryParams = useFilterStore((state) => state.getQueryParams);
  const filterParams = enableFilters ? getQueryParams() : {};

  const fetchData = useCallback(async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getCategoryDistribution(accountId, filterParams);
      setData(response.categories || response);
    } catch (err) {
      console.error('Error fetching category distribution:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Kategorieverteilung');
    } finally {
      setLoading(false);
    }
  }, [accountId, JSON.stringify(filterParams)]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    data, 
    loading, 
    error, 
    refetch: fetchData 
  };
}

/**
 * Custom Hook for Recipient List
 * 
 * Fetches unique recipients with transaction counts
 * 
 * @param {number} accountId - Account ID
 * @param {boolean} enableFilters - Use filter store (default: true)
 * @returns {object} { recipients, loading, error, refetch }
 */
export function useRecipients(accountId, enableFilters = true) {
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const getQueryParams = useFilterStore((state) => state.getQueryParams);
  const filterParams = enableFilters ? getQueryParams() : {};

  const fetchData = useCallback(async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getRecipients(accountId, filterParams);
      setRecipients(response.recipients || response);
    } catch (err) {
      console.error('Error fetching recipients:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Empfänger');
    } finally {
      setLoading(false);
    }
  }, [accountId, JSON.stringify(filterParams)]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { 
    recipients, 
    loading, 
    error, 
    refetch: fetchData 
  };
}
