/**
 * useTransfers Hook
 * 
 * Custom hook for managing transfer data and operations
 */
import { useState, useEffect, useCallback } from 'react';
import { 
  getAllTransfers, 
  getTransferForTransaction,
  detectTransfers,
  createTransfer,
  deleteTransfer,
  getTransferStats
} from '../services/transferService';

export function useTransfers(accountId = null) {
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadTransfers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        include_details: true
      };
      if (accountId) {
        params.account_id = accountId;
      }
      const data = await getAllTransfers(params);
      setTransfers(data);
    } catch (err) {
      setError(err.message || 'Failed to load transfers');
      console.error('Error loading transfers:', err);
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  useEffect(() => {
    loadTransfers();
  }, [loadTransfers]);

  return {
    transfers,
    loading,
    error,
    refetch: loadTransfers
  };
}

/**
 * useTransferForTransaction Hook
 * 
 * Check if a specific transaction is part of a transfer
 */
export function useTransferForTransaction(transactionId) {
  const [transfer, setTransfer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!transactionId) {
      setTransfer(null);
      return;
    }

    let mounted = true;

    const loadTransfer = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getTransferForTransaction(transactionId);
        if (mounted) {
          setTransfer(data);
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || 'Failed to check transfer status');
          console.error('Error checking transfer:', err);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadTransfer();

    return () => {
      mounted = false;
    };
  }, [transactionId]);

  return {
    transfer,
    loading,
    error,
    isTransfer: !!transfer
  };
}

/**
 * useTransferDetection Hook
 * 
 * Detect potential transfers with auto-matching
 */
export function useTransferDetection() {
  const [candidates, setCandidates] = useState([]);
  const [detecting, setDetecting] = useState(false);
  const [error, setError] = useState(null);

  const detect = useCallback(async (params = {}) => {
    try {
      setDetecting(true);
      setError(null);
      const result = await detectTransfers({
        min_confidence: 0.7,
        auto_create: false,
        ...params
      });
      setCandidates(result.candidates);
      return result;
    } catch (err) {
      setError(err.message || 'Failed to detect transfers');
      console.error('Error detecting transfers:', err);
      throw err;
    } finally {
      setDetecting(false);
    }
  }, []);

  const acceptCandidate = useCallback(async (candidate) => {
    try {
      await createTransfer({
        from_transaction_id: candidate.from_transaction_id,
        to_transaction_id: candidate.to_transaction_id,
        amount: candidate.amount,
        transfer_date: candidate.transfer_date,
        notes: candidate.match_reason
      });
      
      // Remove from candidates
      setCandidates(prev => prev.filter(c => 
        c.from_transaction_id !== candidate.from_transaction_id || 
        c.to_transaction_id !== candidate.to_transaction_id
      ));
    } catch (err) {
      console.error('Error creating transfer:', err);
      throw err;
    }
  }, []);

  const rejectCandidate = useCallback((candidate) => {
    setCandidates(prev => prev.filter(c => 
      c.from_transaction_id !== candidate.from_transaction_id || 
      c.to_transaction_id !== candidate.to_transaction_id
    ));
  }, []);

  return {
    candidates,
    detecting,
    error,
    detect,
    acceptCandidate,
    rejectCandidate
  };
}

/**
 * useTransferStats Hook
 * 
 * Get transfer statistics
 */
export function useTransferStats(accountId = null) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getTransferStats(accountId);
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to load transfer stats');
      console.error('Error loading transfer stats:', err);
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  return {
    stats,
    loading,
    error,
    refetch: loadStats
  };
}

export default useTransfers;
