import { useState, useEffect, useMemo, useCallback } from 'react';
import dataService from '../services/dataService';

/**
 * Custom Hook für Transaktionsdaten mit automatischem Reload
 * 
 * @param {number} accountId - Konto-ID
 * @param {object} params - Query-Parameter (limit, offset, fromDate, toDate, categoryIds)
 * @returns {object} { data, loading, error, refetch }
 */
export function useTransactionData(accountId, params = {}) {
  const [data, setData] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getData(accountId, params);
      // Guard against undefined/null responses (some tests/mocks reset implementations)
      if (!response) {
        // ensure callers/tests see an error state instead of silently passing empty values
        setData([]);
        setTotal(0);
        setError('No response from data service');
        return;
      }

      setData(response?.data || []);
      setTotal(response?.total || 0);
    } catch (err) {
      console.error('Error fetching transactions:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Daten');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [accountId, params.limit, params.offset, params.fromDate, params.toDate, params.categoryIds, params.minAmount, params.maxAmount, params.recipient, params.purpose, params.transactionType, params._refreshKey]);

  return { data, total, loading, error, refetch: fetchData };
}

/**
 * Custom Hook für Summary-Daten (Einnahmen/Ausgaben/Aktueller Kontostand)
 * 
 * @param {number} accountId - Konto-ID
 * @param {object} params - { fromDate, toDate, categoryIds }
 * @returns {object} { summary, loading, error, refetch }
 */
export function useSummaryData(accountId, params = {}) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSummary = async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getSummary(accountId, params);
      setSummary(response);
    } catch (err) {
      console.error('Error fetching summary:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Zusammenfassung');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, [accountId, params.fromDate, params.toDate, params.categoryIds, params.minAmount, params.maxAmount, params.recipient, params.purpose, params.transactionType, params._refreshKey]);

  return { summary, loading, error, refetch: fetchSummary };
}

/**
 * Custom Hook für Chart-Statistiken
 * 
 * @param {number} accountId - Konto-ID
 * @param {string} groupBy - Gruppierung ('day', 'month', 'year')
 * @param {object} params - { fromDate, toDate, categoryIds }
 * @returns {object} { chartData, loading, error, refetch }
 */
export function useChartData(accountId, groupBy = 'month', params = {}) {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchChartData = async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getStatistics(accountId, groupBy, params);
      
      // Transform data for Recharts
      const transformed = response.labels?.map((label, index) => ({
        label,
        income: response.income?.[index] || 0,
        expenses: Math.abs(response.expenses?.[index] || 0),
        balance: response.balance?.[index] || 0,
      })) || [];
      
      setChartData(transformed);
    } catch (err) {
      console.error('Error fetching chart data:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Chart-Daten');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChartData();
  }, [accountId, groupBy, params.fromDate, params.toDate, params.categoryIds, params.minAmount, params.maxAmount, params.recipient, params.purpose, params.transactionType, params._refreshKey]);

  return { chartData, loading, error, refetch: fetchChartData };
}

/**
 * Custom Hook für Empfänger/Absender-Daten
 * 
 * @param {number} accountId - Konto-ID
 * @param {object} params - Query-Parameter (fromDate, toDate, limit, transactionType, categoryId)
 * @returns {object} { recipients, loading, error, refetch }
 * 
 * VERWENDUNG:
 * // Nur Empfänger (Ausgaben)
 * const { recipients, loading } = useRecipientData(accountId, {
 *   fromDate: '2024-01-01',
 *   toDate: '2024-12-31',
 *   limit: 10,
 *   transactionType: 'expense'
 * });
 * 
 * // Nur Absender (Einnahmen)
 * const { recipients: senders, loading } = useRecipientData(accountId, {
 *   transactionType: 'income'
 * });
 * 
 * // Mit Kategorie-Filter
 * const { recipients, loading } = useRecipientData(accountId, {
 *   categoryId: 5
 * });
 */
export function useRecipientData(accountId, params = {}) {
  const [recipients, setRecipients] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Destructure params to use as dependencies
  const { fromDate, toDate, limit, transactionType, categoryId, minAmount, maxAmount, recipient, purpose, categoryIds } = params;

  // Memoize params object to prevent infinite loops
  const apiParams = useMemo(() => {
    const p = {};
    if (fromDate) p.fromDate = fromDate;
    if (toDate) p.toDate = toDate;
    if (limit) p.limit = limit;
    if (transactionType) p.transactionType = transactionType;
    if (categoryId !== undefined && categoryId !== null) p.categoryId = categoryId;
    if (categoryIds) p.categoryIds = categoryIds;
    if (minAmount !== undefined && minAmount !== null) p.minAmount = minAmount;
    if (maxAmount !== undefined && maxAmount !== null) p.maxAmount = maxAmount;
    if (recipient) p.recipient = recipient;
    if (purpose) p.purpose = purpose;
    return p;
  }, [fromDate, toDate, limit, transactionType, categoryId, categoryIds, minAmount, maxAmount, recipient, purpose]);

  // Wrap fetch in useCallback
  const fetchRecipients = useCallback(async () => {
    if (!accountId) {
      console.log('useRecipientData: No accountId provided');
      return;
    }

    console.log('useRecipientData: Fetching with params:', apiParams);
    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getRecipients(accountId, apiParams);
      console.log('useRecipientData: Received data:', response);
      // Handle both array and object {items: [], total: 0} formats
      const recipientsData = Array.isArray(response) ? response : (response?.items || []);
      setRecipients(recipientsData);
      setError(null); // Clear error on success
    } catch (err) {
      console.error('useRecipientData: Error fetching recipients:', err);
      // Check if it's a 404 or "no data" error - treat as empty data, not error
      const status = err.response?.status;
      const message = err.response?.data?.message || err.message || '';
      
      if (status === 404 || message.toLowerCase().includes('keine') || message.toLowerCase().includes('not found')) {
        console.log('useRecipientData: No data found, treating as empty array');
        setRecipients([]);
        setError(null);
      } else {
        setError(message || 'Fehler beim Laden der Daten');
        setRecipients([]);
      }
    } finally {
      setLoading(false);
    }
  }, [accountId, apiParams]);

  useEffect(() => {
    fetchRecipients();
  }, [fetchRecipients]);

  return { recipients, loading, error, refetch: fetchRecipients };
}

/**
 * Custom Hook für Absender-Daten (Einnahmen)
 * 
 * @param {number} accountId - Konto-ID
 * @param {object} params - Query-Parameter (fromDate, toDate, limit, categoryId)
 * @returns {object} { senders, loading, error, refetch }
 * 
 * VERWENDUNG:
 * const { senders, loading } = useSenderData(accountId, {
 *   fromDate: '2024-01-01',
 *   toDate: '2024-12-31',
 *   limit: 10
 * });
 */
export function useSenderData(accountId, params = {}) {
  const [senders, setSenders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Destructure params to use as dependencies
  const { fromDate, toDate, limit, categoryId, minAmount, maxAmount, recipient, purpose, categoryIds } = params;

  // Memoize params object with transactionType='income'
  const apiParams = useMemo(() => {
    const p = { transactionType: 'income' };
    if (fromDate) p.fromDate = fromDate;
    if (toDate) p.toDate = toDate;
    if (limit) p.limit = limit;
    if (categoryId !== undefined && categoryId !== null) p.categoryId = categoryId;
    if (categoryIds) p.categoryIds = categoryIds;
    if (minAmount !== undefined && minAmount !== null) p.minAmount = minAmount;
    if (maxAmount !== undefined && maxAmount !== null) p.maxAmount = maxAmount;
    if (recipient) p.recipient = recipient;
    if (purpose) p.purpose = purpose;
    return p;
  }, [fromDate, toDate, limit, categoryId, categoryIds, minAmount, maxAmount, recipient, purpose]);

  // Wrap fetch in useCallback
  const fetchSenders = useCallback(async () => {
    if (!accountId) {
      console.log('useSenderData: No accountId provided');
      return;
    }

    console.log('useSenderData: Fetching with params:', apiParams);
    setLoading(true);
    setError(null);

    try {
      const response = await dataService.getRecipients(accountId, apiParams);
      console.log('useSenderData: Received data:', response);
      // Handle both array and object {items: [], total: 0} formats
      const sendersData = Array.isArray(response) ? response : (response?.items || []);
      setSenders(sendersData);
      setError(null); // Clear error on success
    } catch (err) {
      console.error('useSenderData: Error fetching senders:', err);
      // Check if it's a 404 or "no data" error - treat as empty data, not error
      const status = err.response?.status;
      const message = err.response?.data?.message || err.message || '';
      
      if (status === 404 || message.toLowerCase().includes('keine') || message.toLowerCase().includes('not found')) {
        console.log('useSenderData: No data found, treating as empty array');
        setSenders([]);
        setError(null);
      } else {
        setError(message || 'Fehler beim Laden der Absender');
        setSenders([]);
      }
    } finally {
      setLoading(false);
    }
  }, [accountId, apiParams]);

  useEffect(() => {
    fetchSenders();
  }, [fetchSenders]);

  return { 
    senders, 
    loading, 
    error, 
    refetch: fetchSenders 
  };
}

/**
 * Custom Hook für Kategorien-Daten
 * 
 * @returns {object} { categories, loading, error, refetch }
 * 
 * VERWENDUNG:
 * const { categories, loading } = useCategoryData();
 */
export function useCategoryData() {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCategories = async () => {
    setLoading(true);
    setError(null);

    try {
      // Import inline to avoid circular dependencies
      const { categoryService } = await import('../services/categoryService');
      const response = await categoryService.getCategories();
      console.log('[useCategoryData] Raw response:', response);
      console.log('[useCategoryData] Response type:', Array.isArray(response) ? 'array' : typeof response);
      console.log('[useCategoryData] Response length:', response?.length);
      
      // Handle both array and wrapped object responses
      const categoriesArray = Array.isArray(response) ? response : (response?.data || response?.categories || []);
      console.log('[useCategoryData] Final categories:', categoriesArray);
      
      setCategories(categoriesArray);
    } catch (err) {
      console.error('[useCategoryData] Error fetching categories:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Kategorien');
      setCategories([]); // Ensure categories is empty array on error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  return { categories, loading, error, refetch: fetchCategories };
}

/**
 * Custom Hook für Kategorie-Statistiken eines Kontos
 * 
 * @param {number} accountId - Konto-ID
 * @param {object} params - Query-Parameter (fromDate, toDate)
 * @returns {object} { categoryData, loading, error, refetch }
 * 
 * VERWENDUNG:
 * const { categoryData, loading } = useCategoryStatistics(accountId, {
 *   fromDate: '2024-01-01',
 *   toDate: '2024-12-31'
 * });
 * 
 * BACKEND-ANFORDERUNG:
 * Backend muss Transaktionen anhand der Kategorie-Mappings aggregieren
 * und für jede Kategorie folgende Daten zurückgeben:
 * - category_id, category_name, color, icon
 * - total_amount (Summe aller Transaktionen)
 * - transaction_count (Anzahl Transaktionen)
 * - percentage (Anteil am Gesamtvolumen)
 */
export function useCategoryStatistics(accountId, params = {}) {
  const [categoryData, setCategoryData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchCategoryData = async () => {
    if (!accountId) return;

    setLoading(true);
    setError(null);

    try {
      const { categoryService } = await import('../services/categoryService');
      
      // Lade sowohl Transaktionsdaten als auch alle Kategorien
      const [transactionCategoryData, allCategories] = await Promise.all([
        categoryService.getCategoryData(accountId, params),
        categoryService.getCategories()
      ]);
      
      // Wenn keine Transaktionsdaten vorhanden, zeige alle Kategorien mit 0-Werten
      let finalCategoryData = transactionCategoryData || [];
      if ((!transactionCategoryData || transactionCategoryData.length === 0) && allCategories && allCategories.length > 0) {
        finalCategoryData = allCategories.map(cat => ({
          category_id: cat.id,
          category_name: cat.name,
          color: cat.color,
          icon: cat.icon,
          total_amount: 0,
          transaction_count: 0,
          percentage: 0
        }));
      }
      
      setCategoryData(finalCategoryData);
      setError(null); // Clear error on success
    } catch (err) {
      console.error('Error fetching category statistics:', err);
      // Check if it's a 404 or "no data" error - treat as empty data, not error
      const status = err.response?.status;
      const message = err.response?.data?.message || err.message || '';
      
      if (status === 404 || message.toLowerCase().includes('keine') || message.toLowerCase().includes('not found')) {
        console.log('useCategoryStatistics: No data found, loading all categories with 0 values');
        // Lade alle Kategorien mit 0-Werten
        try {
          const { categoryService } = await import('../services/categoryService');
          const allCategories = await categoryService.getCategories();
          if (allCategories && allCategories.length > 0) {
            setCategoryData(allCategories.map(cat => ({
              category_id: cat.id,
              category_name: cat.name,
              color: cat.color,
              icon: cat.icon,
              total_amount: 0,
              transaction_count: 0,
              percentage: 0
            })));
          } else {
            setCategoryData([]);
          }
        } catch {
          setCategoryData([]);
        }
        setError(null);
      } else {
        setError(message || 'Fehler beim Laden der Kategorie-Statistiken');
        setCategoryData([]);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCategoryData();
  }, [accountId, params.fromDate, params.toDate, params.categoryIds, params.minAmount, params.maxAmount, params.recipient, params.purpose, params.transactionType, params._refreshKey]);

  return { categoryData, loading, error, refetch: fetchCategoryData };
}

/**
 * Custom Hook für Dashboard-Gesamt-Daten (über alle Accounts)
 * 
 * @param {object} params - Query-Parameter (fromDate, toDate)
 * @returns {object} { 
 *   summary: { total_income, total_expenses, current_balance, transaction_count, account_count },
 *   categories: [ { category_id, category_name, total_amount, ... } ],
 *   balanceHistory: { labels, income, expenses, balance },
 *   recipients: [ { recipient, total_amount, transaction_count, ... } ],
 *   senders: [ { recipient, total_amount, transaction_count, ... } ],
 *   loading,
 *   error,
 *   refetch
 * }
 * 
 * VERWENDUNG:
 * const { summary, categories, balanceHistory, recipients, senders, loading } = useDashboardData({
 *   fromDate: '2024-01-01',
 *   toDate: '2024-12-31'
 * });
 */
export function useDashboardData(params = {}) {
  const [summary, setSummary] = useState(null);
  const [categories, setCategories] = useState([]);
  const [balanceHistory, setBalanceHistory] = useState(null);
  const [recipients, setRecipients] = useState([]);
  const [senders, setSenders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Dynamischer Import um zirkuläre Dependencies zu vermeiden
      const { default: dashboardService } = await import('../services/dashboardService');
      const { categoryService } = await import('../services/categoryService');
      
      // Parallel alle Daten laden, inklusive globale Kategorien
      const [summaryData, categoriesData, historyData, recipientsData, sendersData, allCategories] = await Promise.all([
        dashboardService.getSummary(params),
        dashboardService.getCategoriesData({ ...params, limit: 10 }),
        dashboardService.getBalanceHistory({ ...params, groupBy: 'month' }),
        dashboardService.getRecipientsData({ ...params, transactionType: 'expense', limit: 10 }),
        dashboardService.getRecipientsData({ ...params, transactionType: 'income', limit: 10 }),
        categoryService.getCategories()
      ]);

      // Wenn keine Transaktionsdaten vorhanden, zeige alle Kategorien mit 0-Werten
      let finalCategories = categoriesData || [];
      if ((!categoriesData || categoriesData.length === 0) && allCategories && allCategories.length > 0) {
        finalCategories = allCategories.map(cat => ({
          category_id: cat.id,
          category_name: cat.name,
          color: cat.color,
          icon: cat.icon,
          total_amount: 0,
          transaction_count: 0
        }));
      }

      setSummary(summaryData);
      setCategories(finalCategories);
      setBalanceHistory(historyData);
      setRecipients(recipientsData || []);
      setSenders(sendersData || []);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      setError(err.response?.data?.message || 'Fehler beim Laden der Dashboard-Daten');
    } finally {
      setLoading(false);
    }
  };

  // Re-fetch whenever any of the params change (not just dates)
  useEffect(() => {
    fetchDashboardData();
  }, [JSON.stringify(params)]);

  return { 
    summary, 
    categories, 
    balanceHistory, 
    recipients,
    senders,
    loading, 
    error, 
    refetch: fetchDashboardData 
  };
}

export default {
  useTransactionData,
  useSummaryData,
  useChartData,
  useRecipientData,
  useSenderData,
  useCategoryData,
  useCategoryStatistics,
  useDashboardData,
};
