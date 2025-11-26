import { create } from 'zustand';
import categoryService from '../services/categoryService';
import { callApi, invalidateKey, runOptimistic } from '../hooks/useApi';

/**
 * Zustand Store für Category Management
 * 
 * Verwaltet globale Kategorien und deren Mappings
 * 
 * FEATURES:
 * - Fetch, Create, Update, Delete Categories
 * - Category Mappings (Empfänger -> Kategorie)
 * - Optimistic Updates
 * - Error Handling
 * 
 * ERWEITERBARKEIT:
 * - Kategorie-Hierarchien (Parent/Child)
 * - Kategorie-Icons/Colors
 * - Budget pro Kategorie
 */
export const useCategoryStore = create((set, get) => ({
  // State
  categories: [],
  mappings: {},
  loading: false,
  error: null,
  lastFetch: null,

  // Actions
  
  /**
   * Kategorien laden
   * @param {boolean} force - Cache ignorieren und neu laden
   */
  fetchCategories: async (force = false) => {
    set({ loading: true, error: null });
    try {
      // Use shared callApi helper with a 5-minute TTL
      const data = await callApi('categories', () => categoryService.getCategories(), { force, cacheTTL: 300000 });
      set({ 
        categories: data.categories || data,
        loading: false,
        lastFetch: Date.now()
      });
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Laden der Kategorien',
        loading: false 
      });
    }
  },

  /**
   * Neue Kategorie erstellen
   * @param {object} categoryData - { name, color?, icon? }
   */
  createCategory: async (categoryData) => {
    set({ loading: true, error: null });
    try {
      const data = await categoryService.createCategory(categoryData);
      const newCategory = data.category || data;

      // Update local state and invalidate list cache so other consumers refetch
      set((state) => ({
        categories: [...state.categories, newCategory],
        loading: false,
      }));
      invalidateKey('categories');
      return newCategory;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Erstellen der Kategorie',
        loading: false 
      });
      throw error;
    }
  },

  /**
   * Kategorie aktualisieren
   * @param {number} id - Category-ID
   * @param {object} categoryData - Zu aktualisierende Daten
   * @param {boolean} optimistic - Optimistisches Update
   */
  updateCategory: async (id, categoryData, optimistic = true) => {
    // Create local updater and rollback for optimistic flow
    const doLocalUpdate = () => {
      set((state) => ({
        categories: state.categories.map((cat) =>
          cat.id === id ? { ...cat, ...categoryData } : cat
        ),
      }));
    };

    const rollback = async () => {
      await get().fetchCategories(true);
    };

    if (optimistic) {
      // runOptimistic will show toast on error
      const res = await runOptimistic(doLocalUpdate, () => categoryService.updateCategory(id, categoryData), rollback);
      // Invalidate categories cache to keep consistency
      invalidateKey('categories');
      return res.category || res;
    }

    // Non-optimistic path
    set({ loading: true, error: null });
    try {
      const data = await categoryService.updateCategory(id, categoryData);
      set((state) => ({
        categories: state.categories.map((cat) =>
          cat.id === id ? { ...cat, ...(data.category || data) } : cat
        ),
        loading: false,
      }));
      invalidateKey('categories');
      return data.category || data;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Aktualisieren der Kategorie',
        loading: false 
      });
      throw error;
    }
  },

  /**
   * Kategorie löschen
   * @param {number} id - Category-ID
   * @param {boolean} optimistic - Optimistisches Update
   */
  deleteCategory: async (id, optimistic = true) => {
    const doLocalUpdate = () => {
      set((state) => ({
        categories: state.categories.filter((cat) => cat.id !== id),
      }));
    };

    const rollback = async () => {
      await get().fetchCategories(true);
    };

    if (optimistic) {
      const res = await runOptimistic(doLocalUpdate, () => categoryService.deleteCategory(id), rollback);
      invalidateKey('categories');
      return res;
    }

    set({ loading: true, error: null });
    try {
      await categoryService.deleteCategory(id);
      set((state) => ({
        categories: state.categories.filter((cat) => cat.id !== id),
        loading: false,
      }));
      invalidateKey('categories');
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Löschen der Kategorie',
        loading: false 
      });
      throw error;
    }
  },

  /**
   * Category Mappings für Account laden
   * @param {number} accountId - Account-ID
   */
  fetchMappings: async (accountId) => {
    set({ loading: true, error: null });
    try {
      const data = await callApi(`mappings_${accountId}`, () => categoryService.getMappings(accountId), { cacheTTL: 300000 });
      set((state) => ({
        mappings: {
          ...state.mappings,
          [accountId]: data.mappings || data,
        },
        loading: false,
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Laden der Mappings',
        loading: false 
      });
    }
  },

  /**
   * Mapping aktualisieren
   * @param {number} accountId - Account-ID
   * @param {string} recipient - Empfänger-Name
   * @param {number} categoryId - Kategorie-ID
   */
  updateMapping: async (accountId, recipient, categoryId) => {
    try {
      await categoryService.updateMapping(accountId, recipient, categoryId);
      
      // Update local state
      set((state) => ({
        mappings: {
          ...state.mappings,
          [accountId]: {
            ...state.mappings[accountId],
            [recipient]: categoryId,
          },
        },
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Aktualisieren des Mappings'
      });
      throw error;
    }
  },

  /**
   * Alle Mappings für Account aktualisieren
   * @param {number} accountId - Account-ID
   * @param {object} mappings - { recipient: categoryId }
   */
  bulkUpdateMappings: async (accountId, mappings) => {
    try {
      await categoryService.bulkUpdateMappings(accountId, mappings);
      
      set((state) => ({
        mappings: {
          ...state.mappings,
          [accountId]: mappings,
        },
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Aktualisieren der Mappings'
      });
      throw error;
    }
  },

  // Helper
  getCategoryById: (id) => {
    return get().categories.find((cat) => cat.id === id);
  },

  getCategoryByName: (name) => {
    return get().categories.find((cat) => cat.name === name);
  },

  getMappingForRecipient: (accountId, recipient) => {
    const mappings = get().mappings[accountId];
    return mappings ? mappings[recipient] : null;
  },

  clearError: () => set({ error: null }),
}));

// Keep named export only to avoid mixed default/named import patterns
// (consumers should import { useCategoryStore } from './store/categoryStore')
