import api from './api';
import { toApiAmount } from '../utils/amount';

/**
 * Dashboard Service - Aggregierte Daten über alle Accounts
 * Uses amount utilities for consistent money handling
 * 
 * API-ROUTEN (Backend muss implementiert werden):
 * - GET /dashboard/summary              → KPIs (income, expenses, balance, count)
 * - GET /dashboard/categories           → Aggregierte Kategoriedaten
 * - GET /dashboard/balance-history      → Historische Entwicklung des Aktuellen Kontostands
 * 
 * VERWENDUNG:
 * - Alle Daten sind über ALLE Accounts aggregiert
 * - Filterung nach Datum möglich
 * - Wiederverwendet dieselbe Logik wie Account-spezifische Routen
 */

export const dashboardService = {
  /**
   * Gesamt-Zusammenfassung über alle Accounts
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, categoryIds, minAmount, maxAmount, recipient, purpose, transactionType }
   * @returns {Promise<object>} { income, expenses, balance, transactionCount }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/summary?from_date=2024-01-01&to_date=2024-12-31&category_ids=1,2&min_amount=&max_amount=&recipient=&purpose=&transaction_type=
   * 
  * Response Format:
  * {
  *   "total_income": 15000.00,
  *   "total_expenses": -8500.00,
  *   "current_balance": 7700.00,
  *   "transaction_count": 342,
  *   "account_count": 3
  * }
   */
  async getSummary(params = {}) {
    const { 
      fromDate, 
      toDate, 
      categoryIds,
      minAmount,
      maxAmount,
      recipient,
      purpose,
      transactionType
    } = params;
    
    const queryParams = new URLSearchParams();
    
    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend now supports multiple category_ids
    if (categoryIds) {
      queryParams.append('category_ids', categoryIds);
    }
    
    // Advanced filters
    if (minAmount !== undefined && minAmount !== null) queryParams.append('min_amount', toApiAmount(minAmount));
    if (maxAmount !== undefined && maxAmount !== null) queryParams.append('max_amount', toApiAmount(maxAmount));
    if (recipient) queryParams.append('recipient', recipient);
    if (purpose) queryParams.append('purpose', purpose);
    if (transactionType && transactionType !== 'all') queryParams.append('transaction_type', transactionType);

    const response = await api.get(`/dashboard/summary?${queryParams}`);
    return response.data;
  },

  /**
   * Aggregierte Kategoriedaten über alle Accounts
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, limit, categoryIds, minAmount, maxAmount, recipient, purpose, transactionType }
   * @returns {Promise<Array>} Array von { category_id, category_name, total_amount, count, percentage }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/categories?from_date=&to_date=&limit=10&category_ids=1,2&min_amount=&max_amount=&recipient=&purpose=&transaction_type=
   * 
   * Response Format:
   * [
   *   {
   *     "category_id": 2,
   *     "category_name": "Lebensmittel",
   *     "color": "#10b981",
   *     "icon": "🛒",
   *     "total_amount": -1850.00,
   *     "transaction_count": 45,
   *     "percentage": 35.2
   *   }
   * ]
   */
  async getCategoriesData(params = {}) {
    const { 
      fromDate, 
      toDate, 
      limit = 10, 
      categoryIds,
      minAmount,
      maxAmount,
      recipient,
      purpose,
      transactionType
    } = params;
    
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend now supports multiple category_ids
    if (categoryIds) {
      queryParams.append('category_ids', categoryIds);
    }
    
    // Advanced filters
    if (minAmount !== undefined && minAmount !== null) queryParams.append('min_amount', toApiAmount(minAmount));
    if (maxAmount !== undefined && maxAmount !== null) queryParams.append('max_amount', toApiAmount(maxAmount));
    if (recipient) queryParams.append('recipient', recipient);
    if (purpose) queryParams.append('purpose', purpose);
    if (transactionType && transactionType !== 'all') queryParams.append('transaction_type', transactionType);

    const response = await api.get(`/dashboard/categories?${queryParams}`);
    return response.data;
  },

  /**
  * Historische Entwicklung des Aktuellen Kontostands über alle Accounts
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, groupBy, categoryIds, minAmount, maxAmount, recipient, purpose, transactionType }
   * @returns {Promise<object>} { labels, income, expenses, balance }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/balance-history?from_date=&to_date=&group_by=month&category_ids=1,2&min_amount=&max_amount=&recipient=&purpose=&transaction_type=
   * 
   * Response Format:
   * {
   *   "labels": ["Jan 2024", "Feb 2024", "Mär 2024"],
   *   "income": [3500, 3200, 3800],
   *   "expenses": [-2100, -1950, -2300],
   *   "balance": [1400, 2650, 4150]  // Kumuliert
   * }
   */
  async getBalanceHistory(params = {}) {
    const { 
      fromDate, 
      toDate, 
      groupBy = 'month', 
      categoryIds,
      minAmount,
      maxAmount,
      recipient,
      purpose,
      transactionType
    } = params;
    
    const queryParams = new URLSearchParams({
      group_by: groupBy,
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend now supports multiple category_ids
    if (categoryIds) {
      queryParams.append('category_ids', categoryIds);
    }
    
    // Advanced filters
    if (minAmount !== undefined && minAmount !== null) queryParams.append('min_amount', toApiAmount(minAmount));
    if (maxAmount !== undefined && maxAmount !== null) queryParams.append('max_amount', toApiAmount(maxAmount));
    if (recipient) queryParams.append('recipient', recipient);
    if (purpose) queryParams.append('purpose', purpose);
    if (transactionType && transactionType !== 'all') queryParams.append('transaction_type', transactionType);

    const response = await api.get(`/dashboard/balance-history?${queryParams}`);
    return response.data;
  },

  /**
   * Transaktionen über alle Accounts (für Drilldown)
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, categoryIds, limit, offset, minAmount, maxAmount, recipient, purpose, transactionType }
   * @returns {Promise<object>} { data, total, page, pages }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/transactions?category_ids=2,3&from_date=&to_date=&limit=50&offset=0&min_amount=&max_amount=&recipient=&purpose=&transaction_type=
   * 
   * Response Format:
   * {
   *   "data": [
   *     {
   *       "id": 123,
   *       "account_id": 1,
   *       "account_name": "Girokonto",
   *       "date": "2024-11-15",
   *       "amount": -42.50,
   *       "description": "REWE Einkauf",
   *       "recipient": "REWE Markt",
   *       "category_id": 2,
   *       "category_name": "Lebensmittel"
   *     }
   *   ],
   *   "total": 45,
   *   "page": 1,
   *   "pages": 1
   * }
   */
  async getTransactions(params = {}) {
    const { 
      fromDate, 
      toDate, 
      categoryIds, 
      limit = 50, 
      offset = 0,
      minAmount,
      maxAmount,
      recipient,
      purpose,
      transactionType
    } = params;
    
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend now supports multiple category_ids
    if (categoryIds) {
      queryParams.append('category_ids', categoryIds);
    }
    
    // Advanced filters
    if (minAmount !== undefined && minAmount !== null) queryParams.append('min_amount', toApiAmount(minAmount));
    if (maxAmount !== undefined && maxAmount !== null) queryParams.append('max_amount', toApiAmount(maxAmount));
    if (recipient) queryParams.append('recipient', recipient);
    if (purpose) queryParams.append('purpose', purpose);
    if (transactionType && transactionType !== 'all') queryParams.append('transaction_type', transactionType);

    const response = await api.get(`/dashboard/transactions?${queryParams}`);
    return response.data;
  },

  /**
   * Aggregierte Empfänger/Absender-Daten über alle Accounts
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, transactionType, limit, categoryIds, minAmount, maxAmount, recipient, purpose }
   * @returns {Promise<Array>} Array von { recipient, total_amount, transaction_count, percentage }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/recipients-data?transaction_type=expense&from_date=&to_date=&limit=10&category_ids=1,2&min_amount=&max_amount=&recipient=&purpose=
   * 
   * Response Format:
   * [
   *   {
   *     "recipient": "REWE Markt",
   *     "total_amount": -1850.00,
   *     "transaction_count": 45,
   *     "percentage": 35.2,
   *     "category_id": 2,
   *     "category_name": "Lebensmittel"
   *   }
   * ]
   */
  async getRecipientsData(params = {}) {
    const { 
      fromDate, 
      toDate, 
      transactionType = 'expense', 
      limit = 10, 
      categoryIds,
      minAmount,
      maxAmount,
      recipient,
      purpose
    } = params;
    
    const queryParams = new URLSearchParams({
      transaction_type: transactionType,
      limit: limit.toString(),
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend now supports multiple category_ids
    if (categoryIds) {
      queryParams.append('category_ids', categoryIds);
    }
    
    // Advanced filters
    if (minAmount !== undefined && minAmount !== null) queryParams.append('min_amount', toApiAmount(minAmount));
    if (maxAmount !== undefined && maxAmount !== null) queryParams.append('max_amount', toApiAmount(maxAmount));
    if (recipient) queryParams.append('recipient', recipient);
    if (purpose) queryParams.append('purpose', purpose);

    const response = await api.get(`/dashboard/recipients-data?${queryParams}`);
    return response.data;
  },

  /**
   * Money Flow Daten über alle Accounts
   * Zeigt wie Einnahmen in Ausgaben-Kategorien fließen
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, categoryIds, minAmount, maxAmount, recipient, purpose, transactionType }
   * @returns {Promise<object>} { total_income, total_expenses, income_categories, expense_categories, period }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/money-flow?from_date=&to_date=&category_ids=&min_amount=&max_amount=&recipient=&purpose=&transaction_type=
   * 
   * Response Format:
   * {
   *   "total_income": 5000.00,
   *   "total_expenses": 3500.00,
   *   "income_categories": [
   *     {
   *       "id": 1,
   *       "name": "Gehalt",
   *       "value": 4500.00,
   *       "color": "#10b981",
   *       "icon": "💰",
   *       "count": 1
   *     }
   *   ],
   *   "expense_categories": [
   *     {
   *       "id": 2,
   *       "name": "Lebensmittel",
   *       "value": 800.00,
   *       "color": "#ef4444",
   *       "icon": "🛒",
   *       "count": 25
   *     }
   *   ],
   *   "period": {
   *     "from_date": "2024-01-01",
   *     "to_date": "2024-12-31"
   *   }
   * }
   */
  async getMoneyFlow(params = {}) {
    const { 
      fromDate, 
      toDate, 
      categoryIds,
      minAmount,
      maxAmount,
      recipient,
      purpose,
      transactionType
    } = params;
    
    const queryParams = new URLSearchParams();
    
    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    if (categoryIds) {
      queryParams.append('category_ids', categoryIds);
    }
    
    if (minAmount !== undefined && minAmount !== null) queryParams.append('min_amount', toApiAmount(minAmount));
    if (maxAmount !== undefined && maxAmount !== null) queryParams.append('max_amount', toApiAmount(maxAmount));
    if (recipient) queryParams.append('recipient', recipient);
    if (purpose) queryParams.append('purpose', purpose);
    if (transactionType && transactionType !== 'all') queryParams.append('transaction_type', transactionType);

    const response = await api.get(`/dashboard/money-flow?${queryParams}`);
    return response.data;
  },
};

export default dashboardService;