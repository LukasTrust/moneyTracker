/**
 * RecurringTransactionsWidget Component
 * Compact widget showing recurring transactions summary for dashboard
 */
import React from 'react';
import { useRecurring } from '../../hooks/useRecurring';
import { useNavigate } from 'react-router-dom';

const RecurringTransactionsWidget = ({ accountId = null }) => {
  const { recurring, stats, loading, error } = useRecurring(accountId);
  const navigate = useNavigate();

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
        <h3 className="text-lg font-semibold">📋 Verträge</h3>
      </div>

      {/* Summary Stats */}
      {stats && (
        <div className="mb-4 p-4 bg-gradient-to-r from-blue-50 to-green-50 rounded-lg border border-blue-200">
          <div className="flex justify-between items-center">
            <div>
              <div className="text-sm text-gray-600">Aktive Verträge</div>
              <div className="text-2xl font-bold text-gray-900">{stats.active_count}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600">Monatliche Kosten</div>
              <div className="text-2xl font-bold text-green-600">
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
            <div 
              key={item.id}
              className="flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
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
              <div className="text-right">
                <div className="text-sm font-semibold text-gray-900">
                  {formatCurrency(item.monthly_cost || 0)}
                </div>
                <div className="text-xs text-gray-500">
                  /Monat
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">Keine Verträge gefunden</p>
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
