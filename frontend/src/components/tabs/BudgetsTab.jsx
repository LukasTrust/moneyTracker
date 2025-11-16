import React, { useState, useCallback } from 'react';
import { format } from 'date-fns';
import Card from '../common/Card';
import Button from '../common/Button';
import BudgetProgressCard from '../budget/BudgetProgressCard';
import BudgetManager from '../budget/BudgetManager';
import { useFilterStore } from '../../store';

/**
 * BudgetsTab - Budget-Verwaltung und Fortschritt für Account
 * 
 * FEATURES:
 * - Budget-Fortschritt für aktuellen Account
 * - CRUD für Budgets
 * - Date Range Filter Integration
 * - Zwei Modi: "Übersicht" (Fortschritt) und "Verwalten" (CRUD)
 * 
 * @param {Object} props
 * @param {number} props.accountId - Konto-ID für Account-spezifische Budgets
 * @param {string} props.currency - Währung (z.B. "EUR")
 */
function BudgetsTab({ accountId, currency = 'EUR' }) {
  // View Mode: 'overview' oder 'manage'
  const [viewMode, setViewMode] = useState('overview');

  // Global Date Filter Store
  const { fromDate, toDate } = useFilterStore();

  /**
   * Handler für Budget-Änderungen
   * Trigger refresh of budget progress
   */
  const handleBudgetChange = useCallback(() => {
    // BudgetProgressCard has auto-refresh, but we can force it
    console.log('Budget changed, data will auto-refresh');
  }, []);

  return (
    <div className="space-y-6">
      {/* Header mit View Mode Switcher */}
      <Card>
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">
              {viewMode === 'overview' ? 'Budget-Übersicht' : 'Budget-Verwaltung'}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {viewMode === 'overview' 
                ? 'Fortschritt und Status Ihrer Budgets für dieses Konto'
                : 'Budgets erstellen, bearbeiten und löschen'}
            </p>
          </div>
          
          <div className="flex gap-2">
            <Button
              variant={viewMode === 'overview' ? 'primary' : 'secondary'}
              onClick={() => setViewMode('overview')}
              size="sm"
            >
              📊 Übersicht
            </Button>
            <Button
              variant={viewMode === 'manage' ? 'primary' : 'secondary'}
              onClick={() => setViewMode('manage')}
              size="sm"
            >
              ⚙️ Verwalten
            </Button>
          </div>
        </div>
      </Card>

      {/* Date Range Info (wenn Filter aktiv) */}
      {(fromDate || toDate) && viewMode === 'overview' && (
        <Card>
          <div className="flex items-center gap-2 text-sm text-blue-600 bg-blue-50 p-3 rounded">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span>
              Hinweis: Der globale Datumsfilter hat keine Auswirkung auf Budget-Berechnungen. 
              Budgets werden basierend auf ihrem definierten Zeitraum berechnet.
            </span>
          </div>
        </Card>
      )}

      {/* Content */}
      {viewMode === 'overview' && (
        <div className="space-y-6">
          {/* Budget Progress für diesen Account */}
          <BudgetProgressCard 
            accountId={accountId}
            activeOnly={true}
            showSummary={true}
            refreshInterval={60000}
          />

          {/* Info Card */}
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">💡 Tipps zu Budgets</h3>
              
              <div className="space-y-3 text-sm text-gray-600">
                <div className="flex gap-3">
                  <span className="text-green-500 font-bold">✓</span>
                  <div>
                    <strong>Monatliche Budgets</strong> helfen Ihnen, Ihre laufenden Ausgaben zu kontrollieren.
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <span className="text-blue-500 font-bold">ℹ</span>
                  <div>
                    <strong>Fortschrittsbalken</strong> zeigen in Echtzeit, wie viel von Ihrem Budget bereits ausgegeben wurde.
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <span className="text-yellow-500 font-bold">⚠</span>
                  <div>
                    <strong>Warnungen</strong> erscheinen automatisch, wenn Sie 80% Ihres Budgets erreichen.
                  </div>
                </div>
                
                <div className="flex gap-3">
                  <span className="text-purple-500 font-bold">📈</span>
                  <div>
                    <strong>Prognosen</strong> zeigen, ob Sie Ihr Budget basierend auf Ihrem aktuellen Ausgabeverhalten überschreiten werden.
                  </div>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-200">
                <Button
                  onClick={() => setViewMode('manage')}
                  variant="secondary"
                  size="sm"
                >
                  → Budget erstellen oder bearbeiten
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}

      {viewMode === 'manage' && (
        <div className="space-y-6">
          {/* Info Box */}
          <Card>
            <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="text-sm text-blue-800">
                  <p className="font-semibold mb-1">Hinweis zu Budgets</p>
                  <p>
                    Budgets werden pro <strong>Kategorie</strong> definiert und gelten für alle Ihre Konten. 
                    Die Fortschrittsanzeige kann jedoch nach Account gefiltert werden.
                  </p>
                </div>
              </div>
            </div>
          </Card>

          {/* Budget Manager */}
          <BudgetManager onBudgetChange={handleBudgetChange} />

          {/* Quick Actions */}
          <Card>
            <h3 className="text-lg font-semibold text-gray-800 mb-4">Schnellaktionen</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <button
                onClick={() => setViewMode('overview')}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50 transition-colors text-left group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-xl group-hover:bg-blue-200 transition-colors">
                    📊
                  </div>
                  <div>
                    <div className="font-semibold text-gray-800">Budget-Fortschritt anzeigen</div>
                    <div className="text-sm text-gray-600">Zum Übersicht-Modus wechseln</div>
                  </div>
                </div>
              </button>

              <button
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                className="p-4 border border-gray-200 rounded-lg hover:border-gray-300 hover:bg-gray-50 transition-colors text-left group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center text-xl group-hover:bg-gray-200 transition-colors">
                    ⬆️
                  </div>
                  <div>
                    <div className="font-semibold text-gray-800">Nach oben scrollen</div>
                    <div className="text-sm text-gray-600">Zurück zum Anfang der Seite</div>
                  </div>
                </div>
              </button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

export default BudgetsTab;
