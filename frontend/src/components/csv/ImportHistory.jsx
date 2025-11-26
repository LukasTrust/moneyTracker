import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import {
  getImportHistory,
  rollbackImport,
} from '../../services/importHistoryService';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import Pagination from '../common/Pagination';
import { useToast } from '../../hooks/useToast';

/**
 * Import History Component
 * 
 * Displays list of CSV imports with statistics and rollback functionality
 */
export default function ImportHistory({ accountId, onRollbackSuccess, refreshTrigger }) {
  const [imports, setImports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [rollbackingId, setRollbackingId] = useState(null);
  const [confirmRollbackId, setConfirmRollbackId] = useState(null);
  const { showToast } = useToast();

  // Pagination state
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(25);
  const [total, setTotal] = useState(0);
  const pages = Math.max(1, Math.ceil(total / limit));

  // Fetch import history on mount and when refreshTrigger, page or limit changes
  useEffect(() => {
    loadImportHistory();
  }, [accountId, refreshTrigger, page, limit]);

  const loadImportHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const offset = (page - 1) * limit;
      const data = await getImportHistory(accountId, limit, offset);
      // data shape: { imports: [...], total: N }
      setImports(data.imports || []);
      setTotal(typeof data.total === 'number' ? data.total : (data.imports || []).length);
    } catch (err) {
      console.error('Error loading import history:', err);
      setError('Fehler beim Laden der Import-Historie');
      showToast('Fehler beim Laden der Import-Historie', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (importId, filename) => {
    // First click: Show confirmation
    if (confirmRollbackId !== importId) {
      setConfirmRollbackId(importId);
      return;
    }

    // Second click: Execute rollback
    setRollbackingId(importId);
    setConfirmRollbackId(null);

    try {
      const result = await rollbackImport(importId, true);
      
      showToast(
        `${result.rows_deleted} Transaktionen aus "${filename}" wurden gelöscht`,
        'success'
      );

      // Reload import history
      await loadImportHistory();

      // Notify parent component
      if (onRollbackSuccess) {
        onRollbackSuccess();
      }
    } catch (err) {
      console.error('Error rolling back import:', err);
      showToast('Fehler beim Rückgängig machen des Imports', 'error');
    } finally {
      setRollbackingId(null);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      success: (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
          Erfolgreich
        </span>
      ),
      partial: (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
          Teilweise
        </span>
      ),
      failed: (
        <span className="px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
          Fehlgeschlagen
        </span>
      ),
    };
    return badges[status] || badges.failed;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount);
  };

  // Don't early-return on loading — render skeleton inside the normal layout

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">{error}</p>
        <Button onClick={loadImportHistory} variant="secondary">
          Erneut versuchen
        </Button>
      </div>
    );
  }

  if (imports.length === 0) {
    return (
      <div className="text-center py-12 text-neutral-500">
        <p className="text-lg mb-2"><span aria-hidden="true">📋</span> Keine Imports gefunden</p>
        <p className="text-sm">
          Importiere CSV-Dateien, um hier eine Historie zu sehen
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-neutral-900">
          Import-Historie ({imports.length})
        </h3>
        <Button onClick={loadImportHistory} variant="secondary" size="sm">
          🔄 Aktualisieren
        </Button>
      </div>

      {/* Pagination (above the list) */}
      <Pagination
        page={page}
        pages={pages}
        pageSize={limit}
        total={total}
        loading={loading}
        onPageChange={(p) => setPage(p)}
        onPageSizeChange={(s) => { setLimit(s); setPage(1); }}
      />

      {/* Import List */}
      <div className="space-y-3">
        {loading
          ? // Skeleton placeholders while loading
            Array.from({ length: Math.min(limit, 6) }).map((_, i) => (
              <div key={`skeleton-${i}`} className="bg-white border border-neutral-200 rounded-lg p-4 animate-pulse">
                <div className="h-4 bg-neutral-200 rounded w-1/3 mb-3"></div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 pt-3 border-t border-neutral-100">
                  <div className="h-6 bg-neutral-200 rounded"></div>
                  <div className="h-6 bg-neutral-200 rounded"></div>
                  <div className="h-6 bg-neutral-200 rounded"></div>
                  <div className="h-6 bg-neutral-200 rounded"></div>
                </div>
              </div>
            ))
          : imports.map((importItem) => (
          <div
            key={importItem.id}
            className={`bg-white border border-neutral-200 rounded-lg p-4 hover:shadow-md transition-shadow transition-opacity duration-200 ${""}`} 
          >
            {/* Header Row */}
            <div className="flex justify-between items-start mb-3">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-base font-semibold text-neutral-900">
                    <span aria-hidden="true">📄</span> {importItem.filename}
                  </span>
                  {getStatusBadge(importItem.status)}
                </div>
                <p className="text-sm text-neutral-600">
                  {format(new Date(importItem.uploaded_at), 'dd. MMM yyyy, HH:mm', {
                    locale: de,
                  })}
                  {importItem.account_name && (
                    <span className="ml-2 text-neutral-500">
                      • {importItem.account_name}
                    </span>
                  )}
                </p>
              </div>

              {/* Rollback Button */}
              {importItem.can_rollback && (
                <div className="ml-4">
                  <Button
                    onClick={() =>
                      handleRollback(importItem.id, importItem.filename)
                    }
                    variant={confirmRollbackId === importItem.id ? 'danger' : 'secondary'}
                    size="sm"
                    disabled={rollbackingId === importItem.id}
                  >
                    {rollbackingId === importItem.id ? (
                      '⏳ Wird gelöscht...'
                    ) : confirmRollbackId === importItem.id ? (
                      '⚠️ Bestätigen?'
                    ) : (
                      '↩️ Rückgängig'
                    )}
                  </Button>
                </div>
              )}
            </div>

            {/* Statistics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-3 pt-3 border-t border-neutral-100">
              {/* Imported Rows */}
              <div>
                <p className="text-xs text-neutral-500 mb-1">Importiert</p>
                <p className="text-lg font-semibold text-green-600">
                  {importItem.rows_inserted}
                </p>
              </div>

              {/* Duplicates */}
              <div>
                <p className="text-xs text-neutral-500 mb-1">Duplikate</p>
                <p className="text-lg font-semibold text-yellow-600">
                  {importItem.rows_duplicated}
                </p>
              </div>

              {/* Current Count */}
              <div>
                <p className="text-xs text-neutral-500 mb-1">Aktuell</p>
                <p className="text-lg font-semibold text-blue-600">
                  {importItem.current_row_count}
                </p>
              </div>

              {/* Total Amount */}
              <div>
                <p className="text-xs text-neutral-500 mb-1">Summe</p>
                <p
                  className={`text-lg font-semibold ${
                    parseFloat(importItem.total_income) +
                      parseFloat(importItem.total_expenses) >=
                    0
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {formatCurrency(
                    parseFloat(importItem.total_income) +
                      parseFloat(importItem.total_expenses)
                  )}
                </p>
              </div>
            </div>

            {/* Warning if no rows left */}
            {importItem.current_row_count === 0 &&
              importItem.rows_inserted > 0 && (
                <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-800">
                  ⚠️ Alle Transaktionen wurden bereits gelöscht
                </div>
              )}
          </div>
        ))}
      </div>

      {/* Pagination */}
      <Pagination
        page={page}
        pages={pages}
        pageSize={limit}
        total={total}
        loading={loading}
        onPageChange={(p) => setPage(p)}
        onPageSizeChange={(s) => { setLimit(s); setPage(1); }}
      />
    </div>
  );
}
