import api from './api';

/**
 * Budget Service - Verwaltet Budgets und deren Fortschritt
 * 
 * API-ROUTEN (Backend):
 * - GET    /budgets                    → Alle Budgets
 * - GET    /budgets/progress           → Alle Budgets mit Fortschritt
 * - GET    /budgets/summary            → Budget-Zusammenfassung
 * - GET    /budgets/{id}               → Einzelnes Budget
 * - GET    /budgets/{id}/progress      → Einzelnes Budget mit Fortschritt
 * - POST   /budgets                    → Neues Budget erstellen
 * - PUT    /budgets/{id}               → Budget bearbeiten
 * - DELETE /budgets/{id}               → Budget löschen
 */

const budgetService = {
  /**
   * Alle Budgets abrufen
   * @param {Object} params - Query-Parameter
   * @param {boolean} params.activeOnly - Nur aktive Budgets
   * @param {number} params.categoryId - Filter nach Kategorie
   * @returns {Promise<Array>}
   */
  async getBudgets({ activeOnly = false, categoryId = null } = {}) {
    const params = new URLSearchParams();
    if (activeOnly) params.append('active_only', 'true');
    if (categoryId) params.append('category_id', categoryId);
    
    const response = await api.get(`/budgets?${params}`);
    return response.data;
  },

  /**
   * Alle Budgets mit Fortschritts-Information abrufen
   * @param {Object} params - Query-Parameter
   * @param {boolean} params.activeOnly - Nur aktive Budgets
   * @param {number} params.accountId - Filter nach Account
   * @returns {Promise<Array>}
   */
  async getBudgetsWithProgress({ activeOnly = true, accountId = null } = {}) {
    const params = new URLSearchParams();
    if (activeOnly) params.append('active_only', 'true');
    if (accountId) params.append('account_id', accountId);
    
    const response = await api.get(`/budgets/progress?${params}`);
    return response.data;
  },

  /**
   * Budget-Zusammenfassung abrufen (Statistiken)
   * @param {Object} params - Query-Parameter
   * @param {boolean} params.activeOnly - Nur aktive Budgets
   * @param {number} params.accountId - Filter nach Account
   * @returns {Promise<Object>}
   */
  async getBudgetSummary({ activeOnly = true, accountId = null } = {}) {
    const params = new URLSearchParams();
    if (activeOnly) params.append('active_only', 'true');
    if (accountId) params.append('account_id', accountId);
    
    const response = await api.get(`/budgets/summary?${params}`);
    return response.data;
  },

  /**
   * Einzelnes Budget abrufen
   * @param {number} budgetId - Budget-ID
   * @returns {Promise<Object>}
   */
  async getBudget(budgetId) {
    const response = await api.get(`/budgets/${budgetId}`);
    return response.data;
  },

  /**
   * Einzelnes Budget mit Fortschritt abrufen
   * @param {number} budgetId - Budget-ID
   * @param {number} accountId - Optional: Filter nach Account
   * @returns {Promise<Object>}
   */
  async getBudgetWithProgress(budgetId, accountId = null) {
    const params = new URLSearchParams();
    if (accountId) params.append('account_id', accountId);
    
    const response = await api.get(`/budgets/${budgetId}/progress?${params}`);
    return response.data;
  },

  /**
   * Neues Budget erstellen
   * @param {Object} budgetData - Budget-Daten
   * @param {number} budgetData.category_id - Kategorie-ID
   * @param {string} budgetData.period - Periode (monthly, yearly, quarterly, custom)
   * @param {number} budgetData.amount - Budget-Betrag
   * @param {string} budgetData.start_date - Start-Datum (YYYY-MM-DD)
   * @param {string} budgetData.end_date - End-Datum (YYYY-MM-DD)
   * @param {string} budgetData.description - Optional: Beschreibung
   * @returns {Promise<Object>}
   */
  async createBudget(budgetData) {
    const response = await api.post('/budgets', budgetData);
    return response.data;
  },

  /**
   * Budget aktualisieren
   * @param {number} budgetId - Budget-ID
   * @param {Object} budgetData - Zu aktualisierende Daten
   * @returns {Promise<Object>}
   */
  async updateBudget(budgetId, budgetData) {
    const response = await api.put(`/budgets/${budgetId}`, budgetData);
    return response.data;
  },

  /**
   * Budget löschen
   * @param {number} budgetId - Budget-ID
   * @returns {Promise<void>}
   */
  async deleteBudget(budgetId) {
    await api.delete(`/budgets/${budgetId}`);
  },

  /**
   * Helper: Erstelle monatliches Budget für aktuellen Monat
   * @param {number} categoryId - Kategorie-ID
   * @param {number} amount - Budget-Betrag
   * @param {string} description - Optional: Beschreibung
   * @returns {Promise<Object>}
   */
  async createMonthlyBudget(categoryId, amount, description = null) {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();
    
    const startDate = new Date(year, month, 1);
    const endDate = new Date(year, month + 1, 0); // Last day of month
    
    return this.createBudget({
      category_id: categoryId,
      period: 'monthly',
      amount: amount,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      description: description
    });
  },

  /**
   * Helper: Erstelle jährliches Budget für aktuelles Jahr
   * @param {number} categoryId - Kategorie-ID
   * @param {number} amount - Budget-Betrag
   * @param {string} description - Optional: Beschreibung
   * @returns {Promise<Object>}
   */
  async createYearlyBudget(categoryId, amount, description = null) {
    const year = new Date().getFullYear();
    
    return this.createBudget({
      category_id: categoryId,
      period: 'yearly',
      amount: amount,
      start_date: `${year}-01-01`,
      end_date: `${year}-12-31`,
      description: description
    });
  }
};

export default budgetService;
