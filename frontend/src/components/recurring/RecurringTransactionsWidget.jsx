/**
 * RecurringTransactionsWidget Component
 * Compact widget showing recurring transactions summary for dashboard
 */
import React, { useState } from 'react';
import { useRecurring } from '../../hooks/useRecurring';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../hooks/useToast';
import { getRecurringDetails } from '../../services/recurringService';

const RecurringTransactionsWidget = ({ accountId = null }) => {
  const { recurring, stats, loading, error } = useRecurring(accountId);
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [expandedId, setExpandedId] = useState(null);
  const [expandedData, setExpandedData] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);

  /**
   * Format currency
   */
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount);
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
   * Handle item click to expand/collapse details
   */
  const handleItemClick = async (recurringId, e) => {
    e.stopPropagation();
    
    if (expandedId === recurringId) {
      // Collapse if already expanded
      setExpandedId(null);
      setExpandedData(null);
      return;
    }

    // Expand and load details
    setExpandedId(recurringId);
    setLoadingDetails(true);
    setExpandedData(null);

    try {
      const details = await getRecurringDetails(recurringId);
      setExpandedData(details);
    } catch (err) {
      showToast('Fehler beim Laden der Details: ' + (err.message || ''), 'error');
      setExpandedId(null);
    } finally {
      setLoadingDetails(false);
    }
  };

  /**
   * Get top 5 recurring by monthly cost
   */
  const topRecurring = recurring
    .filter(r => r.is_active)
    .sort((a, b) => (b.monthly_cost || 0) - (a.monthly_cost || 0))
    .slice(0, 5);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-2">📋 Verträge</h3>
        <p className="text-sm text-red-600">Fehler beim Laden</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">📋 Aktive Verträge</h3>
      </div>

      {/* Summary Stats */}
      {stats && stats.active_count > 0 && (
        <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border border-blue-200">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-sm text-gray-600">Aktive Verträge</div>
              <div className="text-2xl font-bold text-gray-900">{stats.active_count}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Monatliche Kosten</div>
                <div className={"text-2xl font-bold " + (Number(stats.total_monthly_cost || 0) < 0 ? 'text-red-600' : 'text-green-600')}>
                  {formatCurrency(stats.total_monthly_cost)}
                </div>
            </div>
          </div>
        </div>
      )}

      {/* Top Recurring */}
      {topRecurring.length > 0 ? (
        <div className="space-y-2">
          <div className="text-sm font-medium text-gray-700 mb-2">
            Top Verträge nach monatl. Kosten:
          </div>
          {topRecurring.map((item) => (
            <div key={item.id}>
              <div 
                className="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer"
                onClick={(e) => handleItemClick(item.id, e)}
              >
                <div className="flex-1 min-w-0 flex items-center">
                  <div className="mr-2 text-gray-400 text-xs">
                    {expandedId === item.id ? '▼' : '▶'}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 truncate">
                      {item.recipient}
                    </div>
                    <div className="text-xs text-gray-500">
                      {item.average_interval_days <= 35 ? '📅 Monatlich' : 
                       item.average_interval_days <= 100 ? '📅 Vierteljährlich' : 
                       '📅 Jährlich'}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={"text-sm font-semibold " + (Number(item.monthly_cost || 0) < 0 ? 'text-red-600' : 'text-green-600')}>
                    {formatCurrency(item.monthly_cost || 0)}
                  </div>
                  <div className="text-xs text-gray-500">
                    /Monat
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedId === item.id && (
                <div className="mt-2 p-4 bg-white border border-gray-200 rounded-lg">
                  {loadingDetails ? (
                    <div className="flex justify-center py-4">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                    </div>
                  ) : expandedData ? (
                    <div className="space-y-3">
                      {/* Statistics */}
                      <div className="grid grid-cols-2 gap-3">
                        <div className="bg-gray-50 rounded p-2 border">
                          <div className="text-xs text-gray-500">Erste Transaktion</div>
                          <div className="text-sm font-semibold text-gray-900">
                            {formatDate(expandedData.first_occurrence)}
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded p-2 border">
                          <div className="text-xs text-gray-500">
                            {expandedData.total_spent >= 0 ? 'Gesamt erhalten' : 'Gesamt ausgegeben'}
                          </div>
                          <div className={"text-sm font-semibold " + (expandedData.total_spent >= 0 ? 'text-green-600' : 'text-red-600')}>
                            {formatCurrency(expandedData.total_spent)}
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded p-2 border">
                          <div className="text-xs text-gray-500">Ø Abstand</div>
                          <div className="text-sm font-semibold text-gray-900">
                            {expandedData.average_days_between 
                              ? `${Math.round(expandedData.average_days_between)} Tage`
                              : '-'}
                          </div>
                        </div>
                        <div className="bg-gray-50 rounded p-2 border">
                          <div className="text-xs text-gray-500">Betrag Spanne</div>
                          <div className="text-xs font-semibold text-gray-900">
                            {formatCurrency(expandedData.min_amount)} - {formatCurrency(expandedData.max_amount)}
                          </div>
                        </div>
                      </div>

                      {/* Linked Transactions */}
                      {expandedData.linked_transactions && expandedData.linked_transactions.length > 0 && (
                        <div>
                          <div className="text-xs font-semibold text-gray-700 mb-2">
                            Letzte 5 Transaktionen:
                          </div>
                          <div className="bg-gray-50 rounded border max-h-48 overflow-y-auto">
                            <div className="divide-y divide-gray-200">
                              {expandedData.linked_transactions.slice(0, 5).map((tx) => {
                                const category = categories.find(cat => cat.id === tx.category_id);
                                const categoryIcon = category?.icon || '❓';
                                const categoryColor = category?.color || '#9ca3af';
                                return (
                                <div key={tx.id} className="p-2 hover:bg-gray-100 text-xs">
                                  <div className="flex justify-between items-center">
                                    <div className="flex items-center gap-2">
                                      <span 
                                        className="text-base"
                                        style={{ 
                                          backgroundColor: `${categoryColor}20`,
                                          borderRadius: '4px',
                                          padding: '1px 4px'
                                        }}
                                        title={category?.name || 'Unkategorisiert'}
                                      >
                                        {categoryIcon}
                                      </span>
                                      <span className="text-gray-600">{formatDate(tx.transaction_date)}</span>
                                    </div>
                                    <span className="font-medium text-gray-900">{formatCurrency(tx.amount)}</span>
                                  </div>
                                  {tx.description && (
                                    <div className="text-gray-500 truncate mt-1 ml-7">{tx.description}</div>
                                  )}
                                </div>
                                );
                              })}
                            </div>
                          </div>
                          {expandedData.linked_transactions.length > 5 && (
                            <div className="text-xs text-gray-500 mt-1 text-center">
                              +{expandedData.linked_transactions.length - 5} weitere Transaktionen
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center text-gray-500 py-2 text-sm">
                      Keine Details verfügbar
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm font-medium">Keine aktiven Verträge gefunden</p>
          <p className="text-xs mt-1">
            Importiere Transaktionen für automatische Erkennung
          </p>
        </div>
      )}

      {/* Category Breakdown */}
      {stats && stats.by_category && Object.keys(stats.by_category).length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="text-sm font-medium text-gray-700 mb-2">Nach Kategorie:</div>
          <div className="space-y-1">
            {Object.entries(stats.by_category)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 3)
              .map(([category, amount]) => (
                <div key={category} className="flex justify-between text-sm">
                  <span className="text-gray-600">{category}</span>
                  <span className="font-medium text-gray-900">
                    {formatCurrency(amount)}
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RecurringTransactionsWidget;
