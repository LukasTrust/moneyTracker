/**
 * TransferCandidates Component
 * 
 * Displays potential transfer transactions that were detected during CSV import
 * and allows users to create transfers from them.
 */

import React, { useState } from 'react';

export default function TransferCandidates({ candidates, onCreateTransfer }) {
  const [expandedCandidates, setExpandedCandidates] = useState(new Set());
  const [creatingTransfers, setCreatingTransfers] = useState(new Set());

  const toggleCandidate = (index) => {
    const newExpanded = new Set(expandedCandidates);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedCandidates(newExpanded);
  };

  const handleCreateTransfer = async (candidate, index) => {
    setCreatingTransfers(prev => new Set(prev).add(index));
    try {
      await onCreateTransfer(candidate);
    } finally {
      setCreatingTransfers(prev => {
        const newSet = new Set(prev);
        newSet.delete(index);
        return newSet;
      });
    }
  };

  if (!candidates || candidates.length === 0) {
    return null;
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
      <div className="flex items-start gap-3 mb-4">
        <span className="text-3xl">🔄</span>
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-blue-900 mb-1">
            Mögliche Überweisungen erkannt
          </h3>
          <p className="text-sm text-blue-700">
            Wir haben {candidates.length} potenzielle Überweisungen zwischen Konten gefunden. 
            Diese können als interne Transfers markiert werden.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        {candidates.map((candidate, index) => {
          const isExpanded = expandedCandidates.has(index);
          const isCreating = creatingTransfers.has(index);
          
          return (
            <div 
              key={index}
              className="bg-white border border-blue-300 rounded-lg overflow-hidden"
            >
              {/* Header - Always visible */}
              <div 
                className="p-4 cursor-pointer hover:bg-blue-50 transition-colors"
                onClick={() => toggleCandidate(index)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <span className="text-xl">
                        {candidate.confidence_score >= 0.9 ? '✓' : candidate.confidence_score >= 0.7 ? '⚠️' : '❓'}
                      </span>
                      <div>
                        <p className="font-semibold text-neutral-900">
                          {candidate.from_account_name || 'Unbekannt'} → {candidate.to_account_name || 'Unbekannt'}
                        </p>
                        <p className="text-sm text-neutral-600">
                          {candidate.amount ? `${candidate.amount.toFixed(2)} €` : 'Unbekannter Betrag'} • 
                          {candidate.transfer_date ? ` ${new Date(candidate.transfer_date).toLocaleDateString('de-DE')}` : ' Unbekanntes Datum'}
                          {candidate.confidence_score && (
                            <span className={`ml-2 ${
                              candidate.confidence_score >= 0.9 ? 'text-green-600' : 
                              candidate.confidence_score >= 0.7 ? 'text-yellow-600' : 
                              'text-red-600'
                            }`}>
                              • {Math.round(candidate.confidence_score * 100)}% Übereinstimmung
                            </span>
                          )}
                        </p>
                      </div>
                    </div>
                  </div>
                  <button
                    className="text-neutral-500 hover:text-neutral-700 ml-4"
                    aria-label={isExpanded ? 'Zuklappen' : 'Aufklappen'}
                  >
                    {isExpanded ? '▼' : '▶'}
                  </button>
                </div>
              </div>

              {/* Expanded Details */}
              {isExpanded && (
                <div className="border-t border-blue-200 bg-blue-50 p-4 space-y-4">
                  {/* Transaction Details */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <h4 className="font-semibold text-neutral-900 mb-2">Ausgehende Transaktion</h4>
                      <div className="bg-white border border-neutral-200 rounded p-3 space-y-1">
                        <p><span className="text-neutral-600">Konto:</span> <span className="font-medium">{candidate.from_account_name}</span></p>
                        <p><span className="text-neutral-600">Betrag:</span> <span className="font-medium text-red-600">-{Math.abs(candidate.amount || 0).toFixed(2)} €</span></p>
                        <p><span className="text-neutral-600">Datum:</span> <span className="font-medium">{candidate.transfer_date ? new Date(candidate.transfer_date).toLocaleDateString('de-DE') : 'N/A'}</span></p>
                        {candidate.from_transaction?.recipient && (
                          <p><span className="text-neutral-600">Empfänger:</span> <span className="font-medium">{candidate.from_transaction.recipient}</span></p>
                        )}
                        {candidate.from_transaction?.purpose && (
                          <p><span className="text-neutral-600">Zweck:</span> <span className="font-medium">{candidate.from_transaction.purpose}</span></p>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-neutral-900 mb-2">Eingehende Transaktion</h4>
                      <div className="bg-white border border-neutral-200 rounded p-3 space-y-1">
                        <p><span className="text-neutral-600">Konto:</span> <span className="font-medium">{candidate.to_account_name}</span></p>
                        <p><span className="text-neutral-600">Betrag:</span> <span className="font-medium text-green-600">+{Math.abs(candidate.amount || 0).toFixed(2)} €</span></p>
                        <p><span className="text-neutral-600">Datum:</span> <span className="font-medium">{candidate.transfer_date ? new Date(candidate.transfer_date).toLocaleDateString('de-DE') : 'N/A'}</span></p>
                        {candidate.to_transaction?.recipient && (
                          <p><span className="text-neutral-600">Absender:</span> <span className="font-medium">{candidate.to_transaction.recipient}</span></p>
                        )}
                        {candidate.to_transaction?.purpose && (
                          <p><span className="text-neutral-600">Zweck:</span> <span className="font-medium">{candidate.to_transaction.purpose}</span></p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Match Reason */}
                  {candidate.match_reason && (
                    <div>
                      <h4 className="font-semibold text-neutral-900 mb-2 text-sm">Erkennungsgrund:</h4>
                      <div className="bg-white border border-neutral-200 rounded p-3">
                        <p className="text-sm text-neutral-700">{candidate.match_reason}</p>
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-3 pt-2">
                    <button
                      onClick={() => handleCreateTransfer(candidate, index)}
                      disabled={isCreating}
                      className={`
                        flex-1 px-4 py-2 rounded-lg font-medium transition-colors
                        ${isCreating 
                          ? 'bg-neutral-300 text-neutral-500 cursor-not-allowed' 
                          : 'bg-primary-600 text-white hover:bg-primary-700'
                        }
                      `}
                    >
                      {isCreating ? 'Erstelle...' : 'Als Transfer markieren'}
                    </button>
                    <button
                      onClick={() => toggleCandidate(index)}
                      disabled={isCreating}
                      className="px-4 py-2 border border-neutral-300 text-neutral-700 rounded-lg font-medium hover:bg-neutral-50 transition-colors disabled:opacity-50"
                    >
                      Ignorieren
                    </button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-4 text-xs text-blue-700">
        <p>
          💡 <strong>Hinweis:</strong> Diese Vorschläge basieren auf automatischer Analyse. 
          Überprüfen Sie bitte jede Überweisung vor der Bestätigung.
        </p>
      </div>
    </div>
  );
}
