import React, { useState } from 'react';
import AccountList from '../components/accounts/AccountList';
import CategoryManager from '../components/categories/CategoryManager';
import DashboardGraphOverview from '../components/dashboard/DashboardGraphOverview';

/**
 * Dashboard - Hauptseite mit Tabs
 * 
 * TABS:
 * - Übersicht: Aggregierte Graphen und KPIs über alle Accounts
 * - Konten: AccountList mit Erstellen/Verwalten
 * - Kategorien: Globaler CategoryManager
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
        {activeTab === 'overview' && <DashboardGraphOverview />}
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
      </main>
    </div>
  );
}
