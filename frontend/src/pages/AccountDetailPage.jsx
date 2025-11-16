import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import useAccountStore from '../store/accountStore';
import { useFilterStore } from '../store/filterStore';
import { useTransactionData, useSummaryData, useChartData } from '../hooks/useDataFetch';
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner';
import CsvImportWizard from '../components/csv/CsvImportWizard';
import SummaryCards from '../components/visualization/SummaryCards';
import DataChart from '../components/visualization/DataChart';
import TransactionTable from '../components/visualization/TransactionTable';
import UnifiedFilter from '../components/common/UnifiedFilter';
import RecipientsTab from '../components/tabs/RecipientsTab';
import CategoriesTab from '../components/tabs/CategoriesTab';
import BudgetsTab from '../components/tabs/BudgetsTab';
import AccountSettings from '../components/accounts/AccountSettings';
import { format } from 'date-fns';

/**
 * Account Detail Page mit Tabs
 */
export default function AccountDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentAccount, fetchAccount, loading: accountLoading } = useAccountStore();
  
  // Get date range from global filter store
  const { fromDate, toDate } = useFilterStore();
  
  const [activeTab, setActiveTab] = useState('data');

  // Pagination State
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
  });

  // Convert Date objects to ISO strings for API
  const dateRange = useMemo(() => ({
    fromDate: fromDate ? format(fromDate, 'yyyy-MM-dd') : '',
    toDate: toDate ? format(toDate, 'yyyy-MM-dd') : '',
  }), [fromDate, toDate]);

  // Custom Hooks für Daten mit automatischem Reload
  const { 
    data: transactions, 
    total: totalTransactions,
    loading: transactionsLoading 
  } = useTransactionData(id, {
    ...pagination,
    ...dateRange,
  });

  const { 
    summary, 
    loading: summaryLoading 
  } = useSummaryData(id, dateRange);

  const { 
    chartData, 
    loading: chartLoading 
  } = useChartData(id, 'month', dateRange);

  useEffect(() => {
    if (id) {
      fetchAccount(id);
    }
  }, [id]);

  /**
   * Handler für CSV Upload
   * Daten werden automatisch durch die Hooks neu geladen
   */
  const handleUploadComplete = useCallback(() => {
    // User bleibt auf dem Import-Tab und sieht die Success-Meldung
    // Die Daten-Hooks laden automatisch neu beim nächsten Tab-Wechsel
    console.log('Import completed successfully');
  }, []);

  const dataLoading = transactionsLoading || summaryLoading || chartLoading;

  const tabs = [
    { id: 'data', label: 'Übersicht', icon: '📊' },
    { id: 'categories', label: 'Kategorien', icon: '🏷️' },
    { id: 'budgets', label: 'Budgets', icon: '💰' },
    { id: 'recipients', label: 'Empfänger/Absender', icon: '👥' },
    { id: 'csv-import', label: 'CSV Import & Mapping', icon: '📁' },
    { id: 'settings', label: 'Einstellungen', icon: '⚙️' },
  ];

  if (accountLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <LoadingSpinner size="xl" text="Lade Konto..." />
      </div>
    );
  }

  if (!currentAccount) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Konto nicht gefunden</h2>
          <Button onClick={() => navigate('/')}>Zurück zur Übersicht</Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="mx-auto px-6 sm:px-8 lg:px-12 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/')}
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Zurück
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">{currentAccount.name}</h1>
                {currentAccount.description && (
                  <p className="text-sm text-gray-600 mt-1">{currentAccount.description}</p>
                )}
              </div>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {currentAccount.currency}
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
        {/* Data Tab */}
        {activeTab === 'data' && (
          <div className="space-y-6">
            {/* Unified Filter - NEW! */}
            <UnifiedFilter
              showDateRange={true}
              showCategory={true}
              showTransactionType={false}
              showSearch={true}
            />

            {/* Summary Cards mit Loading State */}
            {summaryLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-gray-100 rounded-lg h-32 animate-pulse" />
                ))}
              </div>
            ) : (
              <SummaryCards summary={summary} currency={currentAccount.currency} />
            )}

            {/* Chart mit Loading State */}
            {chartLoading ? (
              <div className="bg-gray-100 rounded-lg h-80 animate-pulse" />
            ) : (
              <DataChart
                data={chartData}
                type="line"
                title="Finanzübersicht (Monatlich)"
                currency={currentAccount.currency}
              />
            )}

            {/* Transaction Table mit Loading State */}
            {transactionsLoading ? (
              <div className="bg-gray-100 rounded-lg h-96 animate-pulse" />
            ) : (
              <TransactionTable
                transactions={transactions}
                currency={currentAccount.currency}
                loading={transactionsLoading}
                hasMore={pagination.offset + pagination.limit < totalTransactions}
                onLoadMore={() => setPagination((prev) => ({
                  ...prev,
                  offset: prev.offset + prev.limit,
                }))}
              />
            )}
          </div>
        )}

        {/* Categories Tab */}
        {activeTab === 'categories' && (
          <div>
            <CategoriesTab 
              accountId={id} 
              currency={currentAccount.currency} 
            />
          </div>
        )}

        {/* Budgets Tab */}
        {activeTab === 'budgets' && (
          <div>
            <BudgetsTab 
              accountId={id} 
              currency={currentAccount.currency} 
            />
          </div>
        )}

        {/* Recipients/Senders Tab */}
        {activeTab === 'recipients' && (
          <div>
            <RecipientsTab 
              accountId={id} 
              currency={currentAccount.currency} 
            />
          </div>
        )}

        {/* CSV Import & Mapping Tab */}
        {activeTab === 'csv-import' && (
          <div className="space-y-6">
            <CsvImportWizard
              accountId={id}
              onImportSuccess={handleUploadComplete}
            />
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div>
            <AccountSettings account={currentAccount} />
          </div>
        )}
      </main>
    </div>
  );
}
