import { create } from 'zustand';
import accountService from '../services/accountService';
import { callApi, invalidateKey, runOptimistic } from '../hooks/useApi';

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
      const data = await callApi('accounts', () => accountService.getAccounts(), { cacheTTL: 300000 });
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
      const data = await callApi(`account_${id}`, () => accountService.getAccount(id), { cacheTTL: 300000 });
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
      const newAccount = data.account || data;
      set((state) => ({
        accounts: [...state.accounts, newAccount],
        loading: false,
      }));
      // invalidate list cache
      invalidateKey('accounts');
      return newAccount;
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
    const doLocalUpdate = () => {
      set((state) => ({
        accounts: state.accounts.map((acc) =>
          acc.id === id ? { ...acc, ...accountData } : acc
        ),
        currentAccount: state.currentAccount?.id === id 
          ? { ...state.currentAccount, ...accountData }
          : state.currentAccount,
      }));
    };

    const rollback = async () => {
      await get().fetchAccounts(true);
      await get().fetchAccount(id);
    };

    if (optimistic) {
      const res = await runOptimistic(doLocalUpdate, () => accountService.updateAccount(id, accountData), rollback);
      invalidateKey('accounts');
      invalidateKey(`account_${id}`);
      return res.account || res;
    }

    set({ loading: true, error: null });
    try {
      const data = await accountService.updateAccount(id, accountData);
      set((state) => ({
        accounts: state.accounts.map((acc) =>
          acc.id === id ? { ...acc, ...(data.account || data) } : acc
        ),
        currentAccount: state.currentAccount?.id === id 
          ? { ...state.currentAccount, ...(data.account || data) }
          : state.currentAccount,
        loading: false,
      }));
      invalidateKey('accounts');
      invalidateKey(`account_${id}`);
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
      invalidateKey('accounts');
      invalidateKey(`account_${id}`);
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
