import { create } from 'zustand';
import budgetService from '../services/budgetService';
import { callApi, invalidateKey, runOptimistic } from '../hooks/useApi';

/**
 * Zustand Store für Budget Management
 * 
 * Verwaltet Budgets, deren Fortschritt und Zusammenfassung
 * 
 * FEATURES:
 * - Fetch, Create, Update, Delete Budgets
 * - Budget-Fortschritt mit Visualisierung
 * - Optimistic Updates
 * - Error Handling
 * - Cache-Management
 */
export const useBudgetStore = create((set, get) => ({
  // State
  budgets: [],
  budgetsWithProgress: [],
  summary: null,
  loading: false,
  error: null,
  lastFetch: null,

  // Actions

  /**
   * Budgets laden (ohne Fortschritt)
   * @param {Object} options - Query-Optionen
   * @param {boolean} options.activeOnly - Nur aktive Budgets
   * @param {number} options.categoryId - Filter nach Kategorie
   * @param {boolean} options.force - Cache ignorieren
   */
  fetchBudgets: async ({ activeOnly = false, categoryId = null, force = false } = {}) => {
    const state = get();

    // Cache: Nur alle 2 Minuten neu laden
    if (!force && state.lastFetch && Date.now() - state.lastFetch < 120000) {
      return;
    }

    set({ loading: true, error: null });
    try {
      const data = await callApi('budgets', () => budgetService.getBudgets({ activeOnly, categoryId }), { cacheTTL: 120000 });
      set({
        budgets: data,
        loading: false,
        lastFetch: Date.now()
      });
    } catch (error) {
      console.error('Error fetching budgets:', error);
      set({
        error: error.response?.data?.detail || 'Failed to fetch budgets',
        loading: false
      });
      throw error;
    }
  },

  /**
   * Budgets mit Fortschritt laden
   * @param {Object} options - Query-Optionen
   * @param {boolean} options.activeOnly - Nur aktive Budgets
   * @param {number} options.accountId - Filter nach Account
   * @param {boolean} options.force - Cache ignorieren
   */
  fetchBudgetsWithProgress: async ({ activeOnly = true, accountId = null, force = false } = {}) => {
    const state = get();

    // Cache: Nur alle 1 Minute neu laden (Fortschritt ändert sich häufig)
    if (!force && state.lastFetch && Date.now() - state.lastFetch < 60000) {
      return;
    }

    set({ loading: true, error: null });
    try {
      const key = `budgets_progress_${accountId || 'all'}`;
      const data = await callApi(key, () => budgetService.getBudgetsWithProgress({ activeOnly, accountId }), { cacheTTL: 60000 });
      set({
        budgetsWithProgress: data,
        loading: false,
        lastFetch: Date.now()
      });
    } catch (error) {
      console.error('Error fetching budgets with progress:', error);
      set({
        error: error.response?.data?.detail || 'Failed to fetch budget progress',
        loading: false
      });
      throw error;
    }
  },

  /**
   * Budget-Zusammenfassung laden
   * @param {Object} options - Query-Optionen
   * @param {boolean} options.activeOnly - Nur aktive Budgets
   * @param {number} options.accountId - Filter nach Account
   */
  fetchBudgetSummary: async ({ activeOnly = true, accountId = null } = {}) => {
    set({ loading: true, error: null });
    try {
      const key = `budget_summary_${accountId || 'all'}_${activeOnly}`;
      const data = await callApi(key, () => budgetService.getBudgetSummary({ activeOnly, accountId }), { cacheTTL: 60000 });
      set({
        summary: data,
        loading: false
      });
    } catch (error) {
      console.error('Error fetching budget summary:', error);
      set({
        error: error.response?.data?.detail || 'Failed to fetch budget summary',
        loading: false
      });
      throw error;
    }
  },

  /**
   * Einzelnes Budget abrufen
   * @param {number} budgetId - Budget-ID
   * @returns {Promise<Object>}
   */
  fetchBudget: async (budgetId) => {
    set({ loading: true, error: null });
    try {
      const data = await callApi(`budget_${budgetId}`, () => budgetService.getBudget(budgetId), { cacheTTL: 300000 });
      set({ loading: false });
      return data;
    } catch (error) {
      console.error('Error fetching budget:', error);
      set({
        error: error.response?.data?.detail || 'Failed to fetch budget',
        loading: false
      });
      throw error;
    }
  },

  /**
   * Neues Budget erstellen
   * @param {Object} budgetData - Budget-Daten
   * @returns {Promise<Object>}
   */
  createBudget: async (budgetData) => {
    set({ loading: true, error: null });
    try {
      // generate a stable temporary id so we can replace it after the server returns
      const tempId = 'tmp_' + Date.now();
      const doLocal = () => set((state) => ({ budgets: [...state.budgets, { ...budgetData, id: tempId }], loading: false, lastFetch: null }));
      const remote = async () => {
        const created = await budgetService.createBudget(budgetData);
        return created;
      };

      // Use optimistic helper: add local preview, then replace with server result
      const createdBudget = await runOptimistic(doLocal, remote, async () => {
        // rollback: re-fetch budgets
        await get().fetchBudgets(true);
      });

      // Replace temp entry with server result (by tempId)
      set((state) => ({
        budgets: state.budgets.map((b) => (b.id === tempId ? createdBudget : b)),
      }));

      // Invalidate budgets cache so lists refresh
      invalidateKey('budgets');
      return createdBudget;
    } catch (error) {
      console.error('Error creating budget:', error);
      set({
        error: error.response?.data?.detail || 'Failed to create budget',
        loading: false
      });
      throw error;
    }
  },

  /**
   * Budget aktualisieren
   * @param {number} budgetId - Budget-ID
   * @param {Object} budgetData - Zu aktualisierende Daten
   * @returns {Promise<Object>}
   */
  updateBudget: async (budgetId, budgetData) => {
    set({ loading: true, error: null });

    const prevBudgets = get().budgets;
    const doLocal = () => set((state) => ({ budgets: state.budgets.map((b) => (b.id === budgetId ? { ...b, ...budgetData } : b)) }));
    const rollback = () => set({ budgets: prevBudgets });

    try {
      const updated = await runOptimistic(doLocal, () => budgetService.updateBudget(budgetId, budgetData), rollback);
      set((state) => ({
        budgets: state.budgets.map((b) => (b.id === budgetId ? updated : b)),
        loading: false,
        lastFetch: null,
      }));
      invalidateKey('budgets');
      return updated;
    } catch (error) {
      console.error('Error updating budget:', error);
      set({
        error: error.response?.data?.detail || 'Failed to update budget',
        loading: false
      });
      throw error;
    }
  },

  /**
   * Budget löschen
   * @param {number} budgetId - Budget-ID
   */
  deleteBudget: async (budgetId) => {
    set({ loading: true, error: null });

    const prevBudgets = get().budgets;
    const doLocal = () => set((state) => ({ budgets: state.budgets.filter((b) => b.id !== budgetId) }));
    const rollback = () => set({ budgets: prevBudgets });

    try {
      await runOptimistic(doLocal, () => budgetService.deleteBudget(budgetId), rollback);
      set({ loading: false, lastFetch: null });
      invalidateKey('budgets');
    } catch (error) {
      console.error('Error deleting budget:', error);
      set({
        error: error.response?.data?.detail || 'Failed to delete budget',
        loading: false
      });
      throw error;
    }
  },

  /**
   * Monatliches Budget erstellen (Helper)
   * @param {number} categoryId - Kategorie-ID
   * @param {number} amount - Budget-Betrag
   * @param {string} description - Optional: Beschreibung
   */
  createMonthlyBudget: async (categoryId, amount, description = null) => {
    return get().createBudget({
      category_id: categoryId,
      period: 'monthly',
      amount: amount,
      start_date: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
        .toISOString()
        .split('T')[0],
      end_date: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0)
        .toISOString()
        .split('T')[0],
      description: description
    });
  },

  /**
   * Fehler zurücksetzen
   */
  clearError: () => set({ error: null }),

  /**
   * Cache invalidieren (erzwingt Neuladen beim nächsten Fetch)
   */
  invalidateCache: () => set({ lastFetch: null })
}));

export default useBudgetStore;
