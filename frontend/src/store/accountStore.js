import { create } from 'zustand';
import accountService from '../services/accountService';

/**
 * Zustand Store für Account Management
 */
export const useAccountStore = create((set, get) => ({
  // State
  accounts: [],
  currentAccount: null,
  loading: false,
  error: null,

  // Actions
  fetchAccounts: async () => {
    set({ loading: true, error: null });
    try {
      const data = await accountService.getAccounts();
      set({ accounts: data.accounts || data, loading: false });
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Laden der Konten',
        loading: false 
      });
    }
  },

  fetchAccount: async (id) => {
    set({ loading: true, error: null });
    try {
      const data = await accountService.getAccount(id);
      set({ currentAccount: data.account || data, loading: false });
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Laden des Kontos',
        loading: false 
      });
    }
  },

  createAccount: async (accountData) => {
    set({ loading: true, error: null });
    try {
      const data = await accountService.createAccount(accountData);
      set((state) => ({
        accounts: [...state.accounts, data.account || data],
        loading: false,
      }));
      return data.account || data;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Erstellen des Kontos',
        loading: false 
      });
      throw error;
    }
  },

  /**
   * Account aktualisieren
   * Mit optionalem optimistischem Update
   * 
   * @param {number} id - Account-ID
   * @param {object} accountData - Zu aktualisierende Daten
   * @param {boolean} optimistic - Wenn true, Update sofort im State (Standard: false)
   */
  updateAccount: async (id, accountData, optimistic = false) => {
    // Optimistisches Update: State sofort ändern
    if (optimistic) {
      set((state) => ({
        accounts: state.accounts.map((acc) =>
          acc.id === id ? { ...acc, ...accountData } : acc
        ),
        currentAccount: state.currentAccount?.id === id 
          ? { ...state.currentAccount, ...accountData }
          : state.currentAccount,
      }));
    } else {
      set({ loading: true, error: null });
    }

    try {
      const data = await accountService.updateAccount(id, accountData);
      
      // Update mit Server-Response (falls nicht optimistisch)
      if (!optimistic) {
        set((state) => ({
          accounts: state.accounts.map((acc) =>
            acc.id === id ? { ...acc, ...(data.account || data) } : acc
          ),
          currentAccount: state.currentAccount?.id === id 
            ? { ...state.currentAccount, ...(data.account || data) }
            : state.currentAccount,
          loading: false,
        }));
      }
      
      return data.account || data;
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Aktualisieren des Kontos',
        loading: false 
      });
      throw error;
    }
  },

  /**
   * Account löschen
   * 
   * @param {number} id - Account-ID
   */
  deleteAccount: async (id) => {
    set({ loading: true, error: null });
    try {
      await accountService.deleteAccount(id);
      set((state) => ({
        accounts: state.accounts.filter((acc) => acc.id !== id),
        currentAccount: state.currentAccount?.id === id ? null : state.currentAccount,
        loading: false,
      }));
    } catch (error) {
      set({ 
        error: error.response?.data?.message || 'Fehler beim Löschen des Kontos',
        loading: false 
      });
      throw error;
    }
  },

  setCurrentAccount: (account) => {
    set({ currentAccount: account });
  },

  clearError: () => {
    set({ error: null });
  },
}));

export default useAccountStore;
