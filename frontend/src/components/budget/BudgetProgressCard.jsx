import React, { useEffect, useState } from 'react';
import { useBudgetStore } from '../../store/budgetStore';
import Card from '../common/Card';

/**
 * BudgetProgressCard - Visualisierung des Budget-Fortschritts
 * 
 * FEATURES:
 * - Fortschrittsbalken pro Kategorie (actual vs. budget)
 * - Farbcodierung (grün/gelb/rot je nach Status)
 * - Warnungen bei Überschreitungen
 * - Zusammenfassung aller Budgets
 * - Responsive Design
 * - Auto-Refresh
 * 
 * @param {Object} props
 * @param {number} props.accountId - Optional: Filter nach Account
 * @param {boolean} props.activeOnly - Nur aktive Budgets anzeigen
 * @param {boolean} props.showSummary - Zusammenfassung anzeigen
 * @param {number} props.refreshInterval - Auto-Refresh Intervall in ms (0 = deaktiviert)
 */

function BudgetProgressCard({ 
  accountId = null, 
  activeOnly = true, 
  showSummary = true,
  refreshInterval = 60000 // 1 minute default
}) {
  const {
    budgetsWithProgress,
    summary,
    loading,
    error,
    fetchBudgetsWithProgress,
    fetchBudgetSummary
  } = useBudgetStore();

  const [lastUpdate, setLastUpdate] = useState(new Date());

  // Initial load
  useEffect(() => {
    loadData();
  }, [accountId, activeOnly]);

  // Auto-refresh
  useEffect(() => {
    if (refreshInterval <= 0) return;

    const interval = setInterval(() => {
      loadData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [accountId, activeOnly, refreshInterval]);

  const loadData = async () => {
    try {
      await fetchBudgetsWithProgress({ activeOnly, accountId });
      if (showSummary) {
        await fetchBudgetSummary({ activeOnly, accountId });
      }
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error loading budget data:', err);
    }
  };

  /**
   * Get progress bar color based on percentage
   */
  const getProgressColor = (percentage, isExceeded) => {
    if (isExceeded) return 'bg-red-500';
    if (percentage >= 80) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  /**
   * Get text color for percentage
   */
  const getTextColor = (percentage, isExceeded) => {
    if (isExceeded) return 'text-red-700';
    if (percentage >= 80) return 'text-yellow-700';
    return 'text-green-700';
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

  // Ensure budgetsWithProgress is always an array
  const budgets = Array.isArray(budgetsWithProgress) ? budgetsWithProgress : [];

  if (loading && budgets.length === 0) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-500">Lade Budget-Daten...</div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <div className="p-4 bg-red-50 border border-red-200 text-red-700 rounded">
          <p className="font-semibold">Fehler beim Laden der Budget-Daten</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </Card>
    );
  }

  if (budgets.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Budget-Übersicht</h3>
        <div className="text-center py-8 text-gray-500">
          {activeOnly 
            ? 'Keine aktiven Budgets vorhanden. Erstelle dein erstes Budget!'
            : 'Keine Budgets vorhanden.'}
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-800">Budget-Übersicht</h3>
        <div className="text-xs text-gray-500">
          Aktualisiert: {lastUpdate.toLocaleTimeString('de-DE')}
        </div>
      </div>

      {/* Summary Section */}
      {showSummary && summary && (
        <div className="mb-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-gray-600 mb-1">Gesamt-Budget</div>
              <div className="text-lg font-bold text-gray-800">
                {formatCurrency(summary.total_budget_amount)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-600 mb-1">Ausgegeben</div>
              <div className="text-lg font-bold text-blue-600">
                {formatCurrency(summary.total_spent)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-600 mb-1">Verbleibend</div>
              <div className={`text-lg font-bold ${summary.total_remaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatCurrency(summary.total_remaining)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-600 mb-1">Auslastung</div>
              <div className={`text-lg font-bold ${getTextColor(summary.overall_percentage, summary.budgets_exceeded > 0)}`}>
                {summary.overall_percentage.toFixed(1)}%
              </div>
            </div>
          </div>

          {/* Warnings */}
          {(summary.budgets_exceeded > 0 || summary.budgets_at_risk > 0) && (
            <div className="mt-3 pt-3 border-t border-blue-200 flex gap-4 text-sm">
              {summary.budgets_exceeded > 0 && (
                <div className="flex items-center gap-1 text-red-600">
                  <span className="font-semibold">⚠️ {summary.budgets_exceeded}</span>
                  <span>überschritten</span>
                </div>
              )}
              {summary.budgets_at_risk > 0 && (
                <div className="flex items-center gap-1 text-yellow-600">
                  <span className="font-semibold">⚡ {summary.budgets_at_risk}</span>
                  <span>kritisch (&gt;80%)</span>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Individual Budget Progress Bars */}
      <div className="space-y-4">
        {budgets.map((budget) => {
          const { progress } = budget;
          const percentage = Math.min(progress.percentage, 100); // Cap at 100 for visual

          return (
            <div key={budget.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              {/* Header */}
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-2">
                  <div
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: budget.category_color }}
                  />
                  <div>
                    <div className="font-semibold text-gray-800 flex items-center gap-2">
                      {budget.category_icon && <span>{budget.category_icon}</span>}
                      {budget.category_name}
                    </div>
                    <div className="text-xs text-gray-500">
                      {budget.start_date} - {budget.end_date}
                      {progress.days_remaining > 0 && (
                        <span className="ml-2">
                          ({progress.days_remaining} {progress.days_remaining === 1 ? 'Tag' : 'Tage'} verbleibend)
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Status Badge */}
                {progress.is_exceeded && (
                  <span className="px-2 py-1 text-xs font-semibold bg-red-100 text-red-700 rounded-full">
                    Überschritten
                  </span>
                )}
                {!progress.is_exceeded && progress.percentage >= 80 && (
                  <span className="px-2 py-1 text-xs font-semibold bg-yellow-100 text-yellow-700 rounded-full">
                    Kritisch
                  </span>
                )}
              </div>

              {/* Progress Bar */}
              <div className="mb-3">
                <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${getProgressColor(progress.percentage, progress.is_exceeded)}`}
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <div className="text-xs text-gray-500">Ausgegeben</div>
                  <div className="font-semibold text-gray-800">
                    {formatCurrency(progress.spent)}
                  </div>
                  <div className={`text-xs font-medium ${getTextColor(progress.percentage, progress.is_exceeded)}`}>
                    {progress.percentage.toFixed(1)}% von {formatCurrency(budget.amount)}
                  </div>
                </div>

                <div>
                  <div className="text-xs text-gray-500">Verbleibend</div>
                  <div className={`font-semibold ${progress.remaining >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatCurrency(progress.remaining)}
                  </div>
                  {progress.remaining < 0 && (
                    <div className="text-xs text-red-600 font-medium">
                      {formatCurrency(Math.abs(progress.remaining))} über Budget
                    </div>
                  )}
                </div>

                <div>
                  <div className="text-xs text-gray-500">Ø täglich</div>
                  <div className="font-semibold text-gray-800">
                    {formatCurrency(progress.daily_average_spent)}
                  </div>
                  {progress.projected_total > budget.amount && (
                    <div className="text-xs text-yellow-600 font-medium">
                      Prognose: {formatCurrency(progress.projected_total)}
                    </div>
                  )}
                </div>
              </div>

              {/* Warning: Projection exceeds budget */}
              {!progress.is_exceeded && progress.projected_total > budget.amount && progress.days_remaining > 0 && (
                <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-700">
                  ⚠️ Warnung: Bei gleichbleibender Ausgabenrate wird das Budget um ca.{' '}
                  <strong>{formatCurrency(progress.projected_total - budget.amount)}</strong> überschritten.
                </div>
              )}

              {/* Description */}
              {budget.description && (
                <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-600">
                  {budget.description}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}

export default BudgetProgressCard;
