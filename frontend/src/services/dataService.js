import api from './api';
import { toApiAmount } from '../utils/amount';

/**
 * Data Service - Verwaltet Transaktionsdaten und Statistiken
 * Uses amount utilities for consistent money handling
 */

export const dataService = {
  /**
   * Transaktionen für ein Konto abrufen (mit Pagination und Filter)
   */
  async getData(accountId, params = {}) {
    const { 
      limit = 50, 
      offset = 0, 
      fromDate, 
      toDate,
      minAmount,
      maxAmount,
      recipient,
      purpose,  // Changed from description
      transactionType,
      categoryIds
    } = params;
    
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    if (fromDate) queryParams.append('from_date', fromDate);
    if (toDate) queryParams.append('to_date', toDate);
    if (minAmount !== undefined && minAmount !== null) queryParams.append('min_amount', toApiAmount(minAmount));
    if (maxAmount !== undefined && maxAmount !== null) queryParams.append('max_amount', toApiAmount(maxAmount));
    if (recipient) queryParams.append('recipient', recipient);
    if (purpose) queryParams.append('purpose', purpose);  // Changed from description
    if (transactionType && transactionType !== 'all') queryParams.append('transaction_type', transactionType);
    
    // Category Filter: Support multiple categories (comma-separated)
    if (categoryIds) {
      queryParams.append('category_ids', categoryIds);
    }

  // New RESTful path: transactions
  const response = await api.get(`/accounts/${accountId}/transactions?${queryParams}`);
    return response.data;
  },

  /**
  * Zusammenfassung für ein Konto (Einnahmen, Ausgaben, Aktueller Kontostand)
   */
  async getSummary(accountId, params = {}) {
    const { fromDate, toDate, categoryIds, minAmount, maxAmount, recipient, purpose, transactionType } = params;
    
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

    const response = await api.get(
      // New RESTful summary path under transactions
      `/accounts/${accountId}/transactions/summary?${queryParams}`
    );
    return response.data;
  },

  /**
   * Statistiken für Charts (gruppiert nach Tag/Monat/Jahr)
   */
  async getStatistics(accountId, groupBy = 'month', params = {}) {
    const { fromDate, toDate, categoryIds, minAmount, maxAmount, recipient, purpose, transactionType } = params;
    
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

    const response = await api.get(
      `/accounts/${accountId}/transactions/statistics?${queryParams}`
    );
    return response.data;
  },

  /**
   * Top Empfänger/Absender abrufen (mit Filter nach Typ)
   * 
   * @param {number} accountId - Konto-ID
   * @param {object} params - Query-Parameter (fromDate, toDate, limit, transactionType, categoryIds, minAmount, maxAmount, recipient, purpose)
   * @returns {Promise<Array>} Array von { recipient, total_amount, transaction_count, percentage, category_id, category_name }
   * 
   * BACKEND-ROUTE:
   * GET /api/v1/accounts/{id}/recipients-data?from_date=&to_date=&limit=10&transaction_type=all&category_ids=&min_amount=&max_amount=&recipient=&purpose=
   * 
   * Transaction Types:
   * - 'all': Alle Transaktionen
   * - 'expense': Nur Ausgaben (negative Beträge, Empfänger)
   * - 'income': Nur Einnahmen (positive Beträge, Absender)
   * 
   * Response Format:
   * [
   *   { recipient: "REWE", total_amount: -850.50, transaction_count: 15, percentage: 25.5, category_id: 1, category_name: "Lebensmittel" },
   *   { recipient: "Arbeitgeber GmbH", total_amount: 3200.00, transaction_count: 1, percentage: 60.2, category_id: 5, category_name: "Gehalt" }
   * ]
   */
  async getRecipients(accountId, params = {}) {
    const { 
      fromDate, 
      toDate, 
      limit = 10, 
      transactionType = 'all', 
      categoryIds,
      minAmount,
      maxAmount,
      recipient,
      purpose
    } = params;
    
    const queryParams = new URLSearchParams({
      limit: limit.toString(),
      transaction_type: transactionType,
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

    const response = await api.get(
      `/accounts/${accountId}/transactions/recipients?${queryParams}`
    );
    return response.data;
  },
};

export default dataService;
