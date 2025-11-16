import React, { useState, useEffect } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import { useToast } from '../../hooks/useToast';
import { 
  getAllTransfers, 
  detectTransfers, 
  createTransfer, 
  deleteTransfer 
} from '../../services/transferService';

/**
 * TransferManagementPage
 * 
 * Full-page component for managing inter-account transfers:
 * - View all existing transfers
 * - Auto-detect potential transfers
 * - Manually link/unlink transactions
 */
export default function TransferManagementPage() {
  const [transfers, setTransfers] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detecting, setDetecting] = useState(false);
  const [stats, setStats] = useState(null);
  const { showToast } = useToast();

  useEffect(() => {
    loadTransfers();
  }, []);

  const loadTransfers = async () => {
    try {
      setLoading(true);
      const data = await getAllTransfers({ include_details: true });
      setTransfers(data);
    } catch (error) {
      showToast('Failed to load transfers', 'error');
      console.error('Error loading transfers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDetect = async () => {
    try {
      setDetecting(true);
      const result = await detectTransfers({
        min_confidence: 0.7,
        auto_create: false
      });
      
      setCandidates(result.candidates);
      setStats({
        total_found: result.total_found,
        auto_created: result.auto_created
      });
      
      showToast(
        `Found ${result.total_found} potential transfer${result.total_found !== 1 ? 's' : ''}`,
        'success'
      );
    } catch (error) {
      showToast('Failed to detect transfers', 'error');
      console.error('Error detecting transfers:', error);
    } finally {
      setDetecting(false);
    }
  };

  const handleAutoCreate = async (candidate) => {
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
      
      // Reload transfers
      await loadTransfers();
      
      showToast('Transfer created successfully', 'success');
    } catch (error) {
      showToast('Failed to create transfer', 'error');
      console.error('Error creating transfer:', error);
    }
  };

  const handleDelete = async (transferId) => {
    if (!confirm('Are you sure you want to unlink this transfer?')) {
      return;
    }

    try {
      await deleteTransfer(transferId);
      await loadTransfers();
      showToast('Transfer deleted successfully', 'success');
    } catch (error) {
      showToast('Failed to delete transfer', 'error');
      console.error('Error deleting transfer:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transfer Management</h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage inter-account transfers to keep your statistics accurate
          </p>
        </div>
        <Button
          onClick={handleDetect}
          disabled={detecting}
          leftIcon={detecting ? <span className="animate-spin">⟳</span> : <span>✨</span>}
        >
          {detecting ? 'Detecting...' : 'Auto-Detect Transfers'}
        </Button>
      </div>

      {/* Stats Card */}
      <Card padding="md">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{transfers.length}</div>
            <div className="text-sm text-gray-600">Active Transfers</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {transfers.filter(t => t.is_auto_detected).length}
            </div>
            <div className="text-sm text-gray-600">Auto-Detected</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">
              {candidates.length}
            </div>
            <div className="text-sm text-gray-600">Potential Matches</div>
          </div>
        </div>
      </Card>

      {/* Candidates Section */}
      {candidates.length > 0 && (
        <Card 
          title="Potential Transfers" 
          subtitle={`${candidates.length} potential transfer${candidates.length !== 1 ? 's' : ''} detected`}
        >
          <div className="space-y-3">
            {candidates.map((candidate, index) => (
              <CandidateRow
                key={index}
                candidate={candidate}
                onAccept={() => handleAutoCreate(candidate)}
                onReject={() => setCandidates(prev => prev.filter((_, i) => i !== index))}
              />
            ))}
          </div>
        </Card>
      )}

      {/* Existing Transfers */}
      <Card 
        title="Active Transfers"
        subtitle={`${transfers.length} linked transfer${transfers.length !== 1 ? 's' : ''}`}
      >
        {transfers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-5xl mb-3 opacity-50">🔄</div>
            <p>No transfers found</p>
            <p className="text-sm mt-1">Use Auto-Detect to find potential transfers</p>
          </div>
        ) : (
          <div className="space-y-3">
            {transfers.map((transfer) => (
              <TransferRow
                key={transfer.id}
                transfer={transfer}
                onDelete={() => handleDelete(transfer.id)}
              />
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

/**
 * CandidateRow - Display a potential transfer match
 */
function CandidateRow({ candidate, onAccept, onReject }) {
  const confidence = Math.round(candidate.confidence_score * 100);
  const confidenceColor = 
    confidence >= 90 ? 'text-green-600' : 
    confidence >= 70 ? 'text-yellow-600' : 
    'text-orange-600';

  return (
    <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <div className="flex-1 grid grid-cols-3 gap-4 items-center">
        {/* From Transaction */}
        <div className="text-sm">
          <div className="font-medium text-gray-900">
            {candidate.from_transaction.recipient || 'Unknown'}
          </div>
          <div className="text-gray-600">
            {new Date(candidate.from_transaction.date).toLocaleDateString()}
          </div>
          <div className="text-red-600 font-semibold">
            -{Math.abs(candidate.from_transaction.amount).toFixed(2)} €
          </div>
        </div>

        {/* Arrow & Amount */}
        <div className="text-center">
          <div className="text-2xl text-blue-600 mb-1">→</div>
          <div className="text-sm font-semibold">{candidate.amount.toFixed(2)} €</div>
          <div className={`text-xs ${confidenceColor}`}>
            {confidence}% match
          </div>
        </div>

        {/* To Transaction */}
        <div className="text-sm text-right">
          <div className="font-medium text-gray-900">
            {candidate.to_transaction.recipient || 'Unknown'}
          </div>
          <div className="text-gray-600">
            {new Date(candidate.to_transaction.date).toLocaleDateString()}
          </div>
          <div className="text-green-600 font-semibold">
            +{candidate.to_transaction.amount.toFixed(2)} €
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 ml-4">
        <Button
          size="sm"
          variant="success"
          onClick={onAccept}
          leftIcon={<span>✓</span>}
          title="Create transfer"
        >
          Link
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={onReject}
          leftIcon={<span>✕</span>}
          title="Ignore this match"
        >
          Ignore
        </Button>
      </div>
    </div>
  );
}

/**
 * TransferRow - Display an existing transfer
 */
function TransferRow({ transfer, onDelete }) {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 border border-gray-200 rounded-lg">
      <div className="flex-1 grid grid-cols-3 gap-4 items-center">
        {/* From Transaction */}
        <div className="text-sm">
          <div className="font-medium text-gray-900">
            {transfer.from_account_name || 'Unknown Account'}
          </div>
          <div className="text-gray-600">
            {transfer.from_transaction?.recipient || 'Unknown'}
          </div>
          <div className="text-red-600 font-semibold">
            -{Math.abs(transfer.amount).toFixed(2)} €
          </div>
        </div>

        {/* Arrow & Date */}
        <div className="text-center">
          <div className="text-2xl text-gray-400 mb-1">→</div>
          <div className="text-sm text-gray-600">
            {new Date(transfer.transfer_date).toLocaleDateString()}
          </div>
          {transfer.is_auto_detected && (
            <div className="text-xs text-blue-600 flex items-center justify-center gap-1">
              <span>✨</span>
              <span>Auto</span>
            </div>
          )}
        </div>

        {/* To Transaction */}
        <div className="text-sm text-right">
          <div className="font-medium text-gray-900">
            {transfer.to_account_name || 'Unknown Account'}
          </div>
          <div className="text-gray-600">
            {transfer.to_transaction?.recipient || 'Unknown'}
          </div>
          <div className="text-green-600 font-semibold">
            +{transfer.amount.toFixed(2)} €
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="ml-4">
        <Button
          size="sm"
          variant="danger"
          onClick={onDelete}
          leftIcon={<span>🗑️</span>}
          title="Unlink transfer"
        >
          Unlink
        </Button>
      </div>
    </div>
  );
}
