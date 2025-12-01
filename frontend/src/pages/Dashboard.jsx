import React, { useState } from 'react';
import AccountList from '../components/accounts/AccountList';
import CategoryManager from '../components/categories/CategoryManager';
import DashboardGraphOverview from '../components/dashboard/DashboardGraphOverview';
import InsightPopup from '../components/dashboard/InsightPopup';
import BudgetManager from '../components/budget/BudgetManager';
import BudgetProgressCard from '../components/budget/BudgetProgressCard';
import RecurringTransactionsWidget from '../components/recurring/RecurringTransactionsWidget';
import TransferManagementPage from '../components/transfers/TransferManagementPage';

/**
 * Dashboard - Hauptseite mit Tabs
 * 
 * TABS:
 * - Übersicht: Aggregierte Graphen und KPIs über alle Accounts
 * - Konten: AccountList mit Erstellen/Verwalten
 * - Kategorien: Globaler CategoryManager
 * - Budgets: Budget-Verwaltung und Fortschrittsanzeige
 * 
 * ERWEITERBARKEIT:
 * - Weitere Tabs: z.B. "Berichte", "Einstellungen", "Benutzer"
 * - Schnellaktionen: Häufig genutzte Features direkt verfügbar
 */
export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');

  const tabs = [
    { id: 'overview', label: 'Übersicht', icon: '📊' },
    { id: 'accounts', label: 'Meine Konten', icon: '💳' },
    { id: 'categories', label: 'Kategorien', icon: '🏷️' },
    { id: 'budgets', label: 'Budgets', icon: '💰' },
    { id: 'contracts', label: 'Verträge', icon: '📋' },
    { id: 'transfers', label: 'Transfers', icon: '🔄' },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="mx-auto px-6 sm:px-8 lg:px-12 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <svg
                className="h-8 w-8 text-primary-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <h1 className="text-2xl font-bold text-gray-900">Money Tracker</h1>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="mx-auto px-6 sm:px-8 lg:px-12">
          <nav className="flex gap-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`
                  py-4 px-1 border-b-2 font-medium text-sm transition-colors
                  ${activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="mx-auto px-6 sm:px-8 lg:px-12 py-8">
        {/* Insight Popup - Auto-shows on page load */}
        <InsightPopup 
          accountId={null}
          maxInsights={2}
          delayMs={3000}
          autoShow={activeTab === 'overview'}
          onInsightShown={(insight) => {}}
          onInsightDismissed={(insight) => {}}
        />
        
        {activeTab === 'overview' && (
          <div className="space-y-6">            
            <DashboardGraphOverview />
            
            {/* Recurring Transactions Widget */}
            <div className="mt-6">
              <RecurringTransactionsWidget />
            </div>
            
            {/* Budget Overview in Dashboard */}
            <div className="mt-6">
              <BudgetProgressCard 
                activeOnly={true}
                showSummary={true}
                refreshInterval={60000}
              />
            </div>
          </div>
        )}
        {activeTab === 'accounts' && <AccountList />}
        {activeTab === 'categories' && (
          <div>
            <div className="mb-6">
              <p className="text-gray-600">
                Verwalten Sie hier Ihre globalen Kategorien. Kategorien können in allen Konten verwendet werden
                und helfen dabei, Transaktionen automatisch zu organisieren.
              </p>
            </div>
            <CategoryManager />
          </div>
        )}
        {activeTab === 'budgets' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Budget-Verwaltung</h2>
              <p className="text-gray-600">
                Setzen Sie Budgets für Ihre Kategorien und behalten Sie den Überblick über Ihre Ausgaben.
                Budgets helfen Ihnen, finanzielle Ziele zu erreichen und Ausgaben zu kontrollieren.
              </p>
            </div>
            
            {/* Budget Progress Overview */}
            <BudgetProgressCard 
              activeOnly={true}
              showSummary={true}
              refreshInterval={30000}
            />
            
            {/* Budget Management */}
            <BudgetManager />
          </div>
        )}
        {activeTab === 'contracts' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Verträge & Wiederkehrende Zahlungen</h2>
              <p className="text-gray-600">
                Automatische Erkennung wiederkehrender Transaktionen wie Miete, Netflix, etc.
                Behalten Sie den Überblick über Ihre fixen monatlichen Kosten.
              </p>
            </div>
            
            <RecurringTransactionsWidget />
          </div>
        )}
        {activeTab === 'transfers' && (
          <div className="space-y-6">
            <TransferManagementPage />
          </div>
        )}
      </main>
    </div>
  );
}
