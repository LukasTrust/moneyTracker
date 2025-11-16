import React, { lazy, Suspense, useState, useMemo } from 'react';
import { useAccounts } from '../hooks';
import { Card, Button, LoadingSpinner, ErrorMessage } from '../components/common';
import DateRangeFilter from '../components/visualization/DateRangeFilter';
import SummaryCards from '../components/visualization/SummaryCards';

// Lazy load tabs
const AccountList = lazy(() => import('../components/accounts/AccountList'));
const CategoryManager = lazy(() => import('../components/categories/CategoryManager'));

/**
 * Modern Dashboard with Tabs
 * 
 * FEATURES:
 * - Responsive Tabs (Mobile: Dropdown, Desktop: Horizontal)
 * - Global Date Range Filter
 * - KPI Overview
 * - Quick Actions
 * 
 * TABS:
 * - Übersicht: Aggregated data across all accounts
 * - Konten: Account management
 * - Kategorien: Global category management
 * 
 * ERWEITERBARKEIT:
 * - Berichte Tab
 * - Einstellungen Tab
 * - Export Tab
 */
export default function DashboardModern() {
  const [activeTab, setActiveTab] = useState('overview');
  const { accounts, loading: accountsLoading } = useAccounts();

  const tabs = useMemo(() => [
    { id: 'overview', label: 'Übersicht', icon: '📊' },
    { id: 'accounts', label: 'Meine Konten', icon: '💳' },
    { id: 'categories', label: 'Kategorien', icon: '🏷️' },
  ], []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <Header />

      {/* Tabs Navigation */}
      <TabsNav tabs={tabs} activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <Suspense fallback={<LoadingSpinner text="Lädt..." />}>
          {activeTab === 'overview' && <OverviewTab accounts={accounts} />}
          {activeTab === 'accounts' && <AccountList />}
          {activeTab === 'categories' && <CategoryManager />}
        </Suspense>
      </main>
    </div>
  );
}

/**
 * Header Component
 */
function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-xl font-bold">€</span>
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">
                Money Tracker
              </h1>
              <p className="text-sm text-gray-600 hidden sm:block">
                Ihre Finanzen im Überblick
              </p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline">
              Export
            </Button>
            <Button size="sm" variant="primary">
              + Neu
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}

/**
 * Tabs Navigation
 */
function TabsNav({ tabs, activeTab, onTabChange }) {
  return (
    <div className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Desktop Tabs */}
        <nav className="hidden sm:flex gap-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`
                py-4 px-1 border-b-2 font-medium text-sm transition-colors
                ${activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Mobile Dropdown */}
        <div className="sm:hidden py-3">
          <select
            value={activeTab}
            onChange={(e) => onTabChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            {tabs.map((tab) => (
              <option key={tab.id} value={tab.id}>
                {tab.icon} {tab.label}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

/**
 * Overview Tab - Aggregated View
 */
function OverviewTab({ accounts }) {
  if (!accounts || accounts.length === 0) {
    return (
      <Card padding="lg">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">💳</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Keine Konten vorhanden
          </h3>
          <p className="text-gray-600 mb-6">
            Erstellen Sie Ihr erstes Konto, um zu beginnen
          </p>
          <Button variant="primary">
            + Konto erstellen
          </Button>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Date Range Filter */}
      <Card title="Zeitraum auswählen" padding="md">
        <DateRangeFilter />
      </Card>

      {/* Summary Cards */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Gesamtübersicht
        </h2>
        <SummaryCards accountId={null} />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Entwicklung über Zeit" padding="md">
          {/* BalanceChart Component */}
          <div className="h-64 flex items-center justify-center text-gray-400">
            Chart Placeholder
          </div>
        </Card>

        <Card title="Kategorieverteilung" padding="md">
          {/* CategoryPieChart Component */}
          <div className="h-64 flex items-center justify-center text-gray-400">
            Pie Chart Placeholder
          </div>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card 
        title="Letzte Transaktionen" 
        padding="md"
        headerAction={
          <Button size="sm" variant="ghost">
            Alle anzeigen →
          </Button>
        }
      >
        {/* TransactionTable Component (limited) */}
        <div className="text-center py-8 text-gray-400">
          Transaction Table Placeholder
        </div>
      </Card>
    </div>
  );
}
