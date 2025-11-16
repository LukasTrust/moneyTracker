import api from './api';

/**
 * Dashboard Service - Aggregierte Daten über alle Accounts
 * 
 * API-ROUTEN (Backend muss implementiert werden):
 * - GET /dashboard/summary              → KPIs (income, expenses, balance, count)
 * - GET /dashboard/categories           → Aggregierte Kategoriedaten
 * - GET /dashboard/balance-history      → Historische Saldoentwicklung
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
   * @param {object} params - Query-Parameter { fromDate, toDate, categoryIds }
   * @returns {Promise<object>} { income, expenses, balance, transactionCount }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/summary?from_date=2024-01-01&to_date=2024-12-31&category_id=1
   * 
   * Response Format:
   * {
   *   "total_income": 15000.00,
   *   "total_expenses": -8500.00,
   *   "net_balance": 6500.00,
   *   "transaction_count": 342,
   *   "account_count": 3
   * }
   */
  async getSummary(params = {}) {
    const { fromDate, toDate, categoryIds } = params;
    const queryParams = new URLSearchParams();
    
    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend expects single category_id
    if (categoryIds) {
      const categoryId = categoryIds.split(',')[0]; // Take first category if multiple
      queryParams.append('category_id', categoryId);
    }

    console.debug('[DashboardService] getSummary:', { params, queryParams: queryParams.toString() });
    const response = await api.get(`/dashboard/summary?${queryParams}`);
    return response.data;
  },

  /**
   * Aggregierte Kategoriedaten über alle Accounts
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, limit, categoryIds }
   * @returns {Promise<Array>} Array von { category_id, category_name, total_amount, count, percentage }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/categories?from_date=&to_date=&limit=10&category_id=1
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
    const { fromDate, toDate, limit = 10, categoryIds } = params;
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend expects single category_id
    if (categoryIds) {
      const categoryId = categoryIds.split(',')[0]; // Take first category if multiple
      queryParams.append('category_id', categoryId);
    }

    console.debug('[DashboardService] getCategoriesData:', { params, queryParams: queryParams.toString() });
    const response = await api.get(`/dashboard/categories?${queryParams}`);
    return response.data;
  },

  /**
   * Historische Saldoentwicklung über alle Accounts
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, groupBy, categoryIds }
   * @returns {Promise<object>} { labels, income, expenses, balance }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/balance-history?from_date=&to_date=&group_by=month&category_id=1
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
    const { fromDate, toDate, groupBy = 'month', categoryIds } = params;
    const queryParams = new URLSearchParams({
      group_by: groupBy,
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend expects single category_id
    if (categoryIds) {
      const categoryId = categoryIds.split(',')[0]; // Take first category if multiple
      queryParams.append('category_id', categoryId);
    }

    console.debug('[DashboardService] getBalanceHistory:', { params, queryParams: queryParams.toString() });
    const response = await api.get(`/dashboard/balance-history?${queryParams}`);
    return response.data;
  },

  /**
   * Transaktionen über alle Accounts (für Drilldown)
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, categoryId, limit, offset }
   * @returns {Promise<object>} { data, total, page, pages }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/transactions?category_id=2&from_date=&to_date=&limit=50&offset=0
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
    const { fromDate, toDate, categoryId, limit = 50, offset = 0 } = params;
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    if (categoryId) queryParams.append('category_id', categoryId.toString());

    const response = await api.get(`/dashboard/transactions?${queryParams}`);
    return response.data;
  },

  /**
   * Aggregierte Empfänger/Absender-Daten über alle Accounts
   * 
   * @param {object} params - Query-Parameter { fromDate, toDate, transactionType, limit, categoryIds }
   * @returns {Promise<Array>} Array von { recipient, total_amount, transaction_count, percentage }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/dashboard/recipients-data?transaction_type=expense&from_date=&to_date=&limit=10&category_id=1
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
    const { fromDate, toDate, transactionType = 'expense', limit = 10, categoryIds } = params;
    const queryParams = new URLSearchParams({
      transaction_type: transactionType,
      limit: limit.toString(),
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    
    // Category Filter: Backend expects single category_id
    if (categoryIds) {
      const categoryId = categoryIds.split(',')[0]; // Take first category if multiple
      queryParams.append('category_id', categoryId);
    }

    console.debug('[DashboardService] getRecipientsData:', { params, queryParams: queryParams.toString() });
    const response = await api.get(`/dashboard/recipients-data?${queryParams}`);
    return response.data;
  },
};

export default dashboardService;
