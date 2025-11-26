/**
 * useApi Hook
 *
 * Lightweight generic API helper for: fetching, caching, loading, error handling,
 * retries and optimistic update helper. Integrates with the project's `useToast`.
 */
import { useState, useRef } from 'react';
import useToast from './useToast';
import { useUIStore } from '../store';

// Simple in-memory cache shared across hook instances
const cache = new Map();

// Non-hook helper: callApi(fn) that can be used from stores (no React hooks)
export async function callApi(key, fn, options = {}) {
  const { force = false, cacheTTL = 0 } = options;

  if (!force && key && cache.has(key)) {
    const entry = cache.get(key);
    if (!entry.expireAt || entry.expireAt > Date.now()) {
      return entry.value;
    }
    cache.delete(key);
  }

  try {
    const result = await fn();
    if (key) {
      const expireAt = cacheTTL > 0 ? Date.now() + cacheTTL : null;
      cache.set(key, { value: result, expireAt });
    }
    return result;
  } catch (err) {
    const msg = err?.response?.data?.message || err.message || 'Serverfehler';
    try {
      useUIStore.getState().showError && useUIStore.getState().showError(msg);
    } catch (e) {
      // swallow
      // eslint-disable-next-line no-console
      console.error('callApi: failed to show error', e);
    }
    throw err;
  }
}

export function invalidateKey(key) {
  if (key) cache.delete(key);
}

export function clearAllCache() {
  cache.clear();
}

// Non-hook optimistic helper usable from stores
export async function runOptimistic(doLocalUpdate, remoteCall, rollback) {
  try {
    if (typeof doLocalUpdate === 'function') doLocalUpdate();
    const res = await remoteCall();
    return res;
  } catch (err) {
    if (typeof rollback === 'function') rollback();
    const msg = err?.response?.data?.message || err.message || 'Fehler beim Speichern';
    try {
      useUIStore.getState().showError && useUIStore.getState().showError(msg);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error('runOptimistic: failed to show error', e);
    }
    throw err;
  }
}

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const mounted = useRef(true);
  const { showError } = useToast();

  // Call an async function and optionally cache by key
  const call = async (key, fn, options = {}) => {
    const { force = false, cacheTTL = 0 } = options;

    if (!force && key && cache.has(key)) {
      const entry = cache.get(key);
      // TTL checking (optional)
      if (!entry.expireAt || entry.expireAt > Date.now()) {
        setData(entry.value);
        return entry.value;
      }
      cache.delete(key);
    }

    setLoading(true);
    setError(null);
    try {
      const result = await fn();
      if (key) {
        const expireAt = cacheTTL > 0 ? Date.now() + cacheTTL : null;
        cache.set(key, { value: result, expireAt });
      }
      if (mounted.current) setData(result);
      return result;
    } catch (err) {
      const msg = err?.response?.data?.message || err.message || 'Serverfehler';
      setError(msg);
      showError(msg);
      throw err;
    } finally {
      if (mounted.current) setLoading(false);
    }
  };

  // Invalidate cache for a key
  const invalidate = (key) => {
    if (key) cache.delete(key);
  };

  // Clear all cache
  const clearCache = () => cache.clear();

  // Helper for optimistic updates
  // doLocalUpdate: () => void
  // remoteCall: async () => remoteResult
  // rollback: () => void
  const runOptimistic = async (doLocalUpdate, remoteCall, rollback) => {
    try {
      doLocalUpdate();
      const res = await remoteCall();
      return res;
    } catch (err) {
      if (typeof rollback === 'function') rollback();
      const msg = err?.response?.data?.message || err.message || 'Fehler beim Speichern';
      setError(msg);
      showError(msg);
      throw err;
    }
  };

  // Lifecycle helper for cleanup (used in components if necessary)
  const unmount = () => {
    mounted.current = false;
  };

  return {
    call,
    data,
    loading,
    error,
    invalidate,
    clearCache,
    runOptimistic,
    unmount,
  };
}

export default useApi;
