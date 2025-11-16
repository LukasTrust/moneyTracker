import { useEffect } from 'react';
import { useAccountStore } from '../store';

/**
 * Custom Hook for Account Management
 * 
 * Provides easy access to account store with automatic fetching
 * 
 * @param {boolean} autoFetch - Automatically fetch accounts on mount (default: true)
 * @returns {object} Account store state and actions
 * 
 * @example
 * const { accounts, loading, error, fetchAccounts, createAccount } = useAccounts();
 */
export function useAccounts(autoFetch = true) {
  const store = useAccountStore();

  useEffect(() => {
    if (autoFetch && store.accounts.length === 0) {
      store.fetchAccounts();
    }
  }, [autoFetch]);

  return store;
}

/**
 * Custom Hook for Single Account
 * 
 * Fetches and returns a specific account by ID
 * 
 * @param {number} accountId - Account ID
 * @returns {object} { account, loading, error, refetch }
 * 
 * @example
 * const { account, loading, error } = useAccount(accountId);
 */
export function useAccount(accountId) {
  const { currentAccount, loading, error, fetchAccount } = useAccountStore();

  useEffect(() => {
    if (accountId) {
      fetchAccount(accountId);
    }
  }, [accountId]);

  return {
    account: currentAccount,
    loading,
    error,
    refetch: () => fetchAccount(accountId),
  };
}
