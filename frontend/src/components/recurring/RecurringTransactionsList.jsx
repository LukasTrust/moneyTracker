/**
 * RecurringTransactionsList Component
 * Displays list of recurring transactions (Verträge) with actions
 */
import React, { useState, useEffect } from 'react';
import { useRecurring } from '../../hooks/useRecurring';
import { useToast } from '../../hooks/useToast';
import Modal from '../common/Modal';
import Button from '../common/Button';

const RecurringTransactionsList = ({ accountId = null, showTitle = true }) => {
  const { recurring, stats, loading, error, triggerDetection, toggle, remove, refresh } = useRecurring(accountId);
  const { showToast } = useToast();
  const [includeInactive, setIncludeInactive] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState(null); // { id, recipient }

  /**
   * Handle detection trigger
   */
  const handleDetect = async () => {
    setDetecting(true);
    try {
      const result = await triggerDetection();
      showToast(`Erkennung abgeschlossen: ✅ ${result.created} neu, 🔄 ${result.updated} aktualisiert, ❌ ${result.deleted} entfernt`, 'success');
    } catch (err) {
      showToast('Fehler bei der Erkennung: ' + (err.message || ''), 'error');
    } finally {
      setDetecting(false);
    }
  };

  /**
   * Handle toggle active status
   */
  const handleToggle = async (recurringId, currentStatus) => {
    try {
      await toggle(recurringId, !currentStatus);
    } catch (err) {
      showToast('Fehler beim Ändern: ' + (err.message || ''), 'error');
    }
  };

  /**
   * Handle delete
   */
  const handleDelete = async (recurringId, recipient) => {
    // open confirmation modal
    setConfirmTarget({ id: recurringId, recipient });
    setConfirmOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!confirmTarget) return;
    const { id } = confirmTarget;
    setConfirmOpen(false);
    try {
      await remove(id);
      showToast('Vertrag gelöscht', 'success');
    } catch (err) {
      showToast('Fehler beim Löschen: ' + (err.message || ''), 'error');
    } finally {
      setConfirmTarget(null);
    }
  };

  const handleCancelDelete = () => {
    setConfirmOpen(false);
    setConfirmTarget(null);
  };

  // Refresh when includeInactive changes
  useEffect(() => {
    // refresh can be async, don't block UI
    try {
      if (refresh) refresh(includeInactive);
    } catch (e) {
      // ignore refresh errors here - hook exposes loading/error state
      console.error('Error refreshing recurring on includeInactive change', e);
    }
  }, [includeInactive, refresh]);

  /**
   * Format interval to readable text
   */
  const formatInterval = (days) => {
    if (days <= 10) return `${days} Tage`;
    if (days <= 35) return 'Monatlich';
    if (days <= 100) return 'Vierteljährlich';
    if (days <= 400) return 'Jährlich';
    return `${days} Tage`;
  };

  /**
   * Format date to German locale
   */
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  };

  /**
   * Format currency
   */
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">❌ Fehler: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      {showTitle && (
        <div className="flex justify-between items-center">
          <h2 className="text-2xl font-bold">📋 Verträge & Wiederkehrende Zahlungen</h2>
          <Button
            onClick={handleDetect}
            disabled={detecting}
            loading={detecting}
            leftIcon={detecting ? <span className="animate-spin">⟳</span> : <span>🔍</span>}
            size="md"
          >
            {detecting ? '🔄 Erkenne...' : '🔍 Erkennung starten'}
          </Button>
        </div>
      )}

      {/* Statistics */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm text-blue-600 font-medium">Aktive Verträge</div>
            <div className="text-2xl font-bold text-blue-900">{stats.active_count}</div>
          </div>
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-sm text-green-600 font-medium">Monatliche Fixkosten</div>
            <div className="text-2xl font-bold text-green-900">{formatCurrency(stats.total_monthly_cost)}</div>
          </div>
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="text-sm text-gray-600 font-medium">Gesamt</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_count}</div>
          </div>
        </div>
      )}

      {/* Filter Toggle */}
      <div className="flex items-center space-x-2">
        <input
          type="checkbox"
          id="include-inactive"
          checked={includeInactive}
          onChange={(e) => setIncludeInactive(e.target.checked)}
          className="rounded border-gray-300"
        />
        <label htmlFor="include-inactive" className="text-sm text-gray-600">
          Inaktive Verträge anzeigen
        </label>
      </div>

      {/* List */}
      {recurring.length === 0 ? (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <p className="text-gray-600">Keine Verträge gefunden.</p>
          <p className="text-sm text-gray-500 mt-2">
            Importiere mehr Transaktionen oder klicke auf "Erkennung starten".
          </p>
        </div>
      ) : (
        <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Empfänger
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Betrag
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Intervall
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Monatlich
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Letzte Zahlung
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Nächste erwartet
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Aktionen
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {recurring.map((item) => (
                <tr 
                  key={item.id} 
                  className={item.is_active ? '' : 'bg-gray-50 opacity-60'}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    {item.is_active ? (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        ✓ Aktiv
                      </span>
                    ) : (
                      <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                        ⊗ Inaktiv
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{item.recipient}</div>
                    <div className="text-xs text-gray-500">
                      {item.occurrence_count}x erkannt
                      {item.confidence_score < 1.0 && (
                        <span className="ml-2 text-yellow-600">
                          ⚠ {Math.round(item.confidence_score * 100)}% sicher
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(item.average_amount)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatInterval(item.average_interval_days)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {formatCurrency(item.monthly_cost || 0)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(item.last_occurrence)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                    {formatDate(item.next_expected_date)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                    <button
                      onClick={() => handleToggle(item.id, item.is_active)}
                      className="text-blue-600 hover:text-blue-800"
                      title={item.is_active ? 'Als inaktiv markieren' : 'Als aktiv markieren'}
                    >
                      {item.is_active ? '⏸' : '▶'}
                    </button>
                    <button
                      onClick={() => handleDelete(item.id, item.recipient)}
                      className="text-red-600 hover:text-red-800"
                      title="Löschen"
                    >
                      🗑
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Confirm Delete Modal */}
      {confirmOpen && confirmTarget && (
        <Modal
          isOpen={confirmOpen}
          onClose={handleCancelDelete}
          title="Vertrag löschen"
        >
          <div className="space-y-4">
            <p>Vertrag "{confirmTarget.recipient}" wirklich löschen?</p>
            <div className="flex justify-end gap-3 pt-4">
              <button
                onClick={handleCancelDelete}
                className="px-4 py-2 rounded-lg border"
              >
                Abbrechen
              </button>
              <button
                onClick={handleConfirmDelete}
                className="px-4 py-2 bg-red-600 text-white rounded-lg"
              >
                Löschen
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};

export default RecurringTransactionsList;
