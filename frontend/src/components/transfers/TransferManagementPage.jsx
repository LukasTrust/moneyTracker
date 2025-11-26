import React, { useState, useEffect } from 'react';
import Card from '../common/Card';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import Pagination from '../common/Pagination';
import Modal from '../common/Modal';
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
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState(null);
  // Pagination (client-side - backend currently returns all transfers)
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [total, setTotal] = useState(0);
  const pages = Math.max(1, Math.ceil(total / limit));

  useEffect(() => {
    loadTransfers();
  }, []);

  const loadTransfers = async () => {
    try {
      setLoading(true);
      // Keep calling existing API (returns full list). We'll paginate client-side to avoid backend changes.
      const data = await getAllTransfers({ include_details: true });
      const list = Array.isArray(data) ? data : (data.transfers || []);
      setTransfers(list);
      setTotal(list.length);
    } catch (error) {
      showToast('Fehler beim Laden der Überweisungen', 'error');
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
        `${result.total_found} möglicher Treffer${result.total_found !== 1 ? 'n' : ''} gefunden`,
        'success'
      );
    } catch (error) {
      showToast('Fehler bei der Erkennung von Überweisungen', 'error');
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
      
      showToast('Überweisung erfolgreich erstellt', 'success');
    } catch (error) {
      showToast('Fehler beim Erstellen der Überweisung', 'error');
      console.error('Error creating transfer:', error);
    }
  };

  const handleDelete = async (transferId) => {
    setConfirmTarget(transferId);
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!confirmTarget) return;
    setConfirmOpen(false);
    try {
      await deleteTransfer(confirmTarget);
      await loadTransfers();
      showToast('Überweisung erfolgreich entfernt', 'success');
    } catch (error) {
      showToast('Fehler beim Entfernen der Überweisung', 'error');
      console.error('Error deleting transfer:', error);
    } finally {
      setConfirmTarget(null);
    }
  };

  const handleCancelConfirmDelete = () => {
    setConfirmOpen(false);
    setConfirmTarget(null);
  };

  // Do not early-return — show skeleton inside the page for smoother transitions

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Transfers verwalten</h1>
          <p className="mt-1 text-sm text-gray-500">
            Überweisungen zwischen Konten ansehen und verwalten, um Ihre Auswertungen korrekt zu halten
          </p>
        </div>
        <Button
          onClick={handleDetect}
          disabled={detecting}
          leftIcon={detecting ? <span className="animate-spin">⟳</span> : <span>✨</span>}
          title="Sucht mögliche Überweisungen zwischen Konten"
          aria-label="Transfers automatisch erkennen"
        >
          {detecting ? 'Erkenne...' : 'Automatisch erkennen'}
        </Button>
      </div>

      {/* Stats Card */}
      <Card padding="md">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-primary-600">{transfers.length}</div>
            <div className="text-sm text-gray-600">Verknüpfte Überweisungen</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">
              {transfers.filter(t => t.is_auto_detected).length}
            </div>
            <div className="text-sm text-gray-600">Automatisch erkannt</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-accent-600">
              {candidates.length}
            </div>
            <div className="text-sm text-gray-600">Mögliche Treffer</div>
          </div>
        </div>
      </Card>

      {/* Confirm Delete Modal */}
      {confirmOpen && (
        <Modal isOpen={confirmOpen} onClose={handleCancelConfirmDelete} title="Überweisung löschen">
          <div className="space-y-4">
            <p>Möchten Sie diese Überweisung wirklich entkoppeln?</p>
            <div className="flex justify-end gap-3 pt-4">
              <button onClick={handleCancelConfirmDelete} className="px-4 py-2 rounded-lg border">Abbrechen</button>
              <button onClick={handleConfirmDelete} className="px-4 py-2 bg-red-600 text-white rounded-lg">Entkoppeln</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Candidates Section */}
      {candidates.length > 0 && (
        <Card 
          title="Mögliche Überweisungen" 
          subtitle={`${candidates.length} möglicher Treffer${candidates.length !== 1 ? 'n' : ''} gefunden`}
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
        title="Verknüpfte Überweisungen"
        subtitle={`${total} verknüpfte Überweisung${total !== 1 ? 'en' : ''}`}
      >
        {/* Pagination above the list */}
        <Pagination
          page={page}
          pages={pages}
          pageSize={limit}
          total={total}
          loading={loading}
          onPageChange={(p) => setPage(p)}
          onPageSizeChange={(s) => { setLimit(s); setPage(1); }}
        />

        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: Math.min(limit, 6) }).map((_, i) => (
              <div key={`t-skel-${i}`} className="bg-gray-50 border border-gray-100 rounded-lg p-4 animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-1/3 mb-3"></div>
                <div className="grid grid-cols-3 gap-4">
                  <div className="h-6 bg-gray-200 rounded"></div>
                  <div className="h-6 bg-gray-200 rounded"></div>
                  <div className="h-6 bg-gray-200 rounded"></div>
                </div>
              </div>
            ))}
          </div>
        ) : transfers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <div className="text-5xl mb-3 opacity-50">🔄</div>
            <p>Keine Überweisungen gefunden</p>
            <p className="text-sm mt-1">Nutzen Sie „Automatisch erkennen“, um mögliche Überweisungen zu finden</p>
          </div>
        ) : (
          <div className={`space-y-3 transition-opacity duration-200`} key={`transfers-page-${page}`}>
              {transfers.slice((page - 1) * limit, page * limit).map((transfer) => (
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
    <div className="flex items-center justify-between p-4 bg-primary-50 border border-primary-200 rounded-lg">
      <div className="flex-1 grid grid-cols-3 gap-4 items-center">
        {/* From Transaction */}
        <div className="text-sm">
          <div className="font-medium text-gray-900">
            {candidate.from_transaction.recipient || 'Unbekannt'}
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
            {confidence}% Übereinstimmung
          </div>
        </div>

        {/* To Transaction */}
        <div className="text-sm text-right">
          <div className="font-medium text-gray-900">
            {candidate.to_transaction.recipient || 'Unbekannt'}
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
            title="Überweisung erstellen und verknüpfen"
            aria-label="Verknüpfen"
          >
          Verknüpfen
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={onReject}
            leftIcon={<span>✕</span>}
            title="Treffer ignorieren"
            aria-label="Ignorieren"
          >
          Ignorieren
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
            {transfer.from_account_name || 'Unbekanntes Konto'}
          </div>
          <div className="text-gray-600">
            {transfer.from_transaction?.recipient || 'Unbekannt'}
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
            <div className="text-xs text-primary-600 flex items-center justify-center gap-1">
              <span>✨</span>
              <span>Automatisch</span>
            </div>
          )}
        </div>

        {/* To Transaction */}
        <div className="text-sm text-right">
          <div className="font-medium text-gray-900">
            {transfer.to_account_name || 'Unbekanntes Konto'}
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
          title="Überweisung entkoppeln"
          aria-label="Entkoppeln"
        >
          Entkoppeln
        </Button>
      </div>
    </div>
  );
}
