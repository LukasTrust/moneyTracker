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
import RecurringTransactionsWidget from '../components/recurring/RecurringTransactionsWidget';
import ComparisonView from '../components/comparison/ComparisonView';
import ImportHistory from '../components/csv/ImportHistory';
import { format } from 'date-fns';

/**
 * Account Detail Page mit Tabs
 */
export default function AccountDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { currentAccount, fetchAccount, loading: accountLoading } = useAccountStore();
  
  // Get filters from global filter store
  const { 
    fromDate, 
    toDate, 
    selectedCategoryIds,
    minAmount,
    maxAmount,
    recipientQuery,
    purposeQuery,
    transactionType
  } = useFilterStore();
  
  const [activeTab, setActiveTab] = useState('data');
  const [importHistoryRefresh, setImportHistoryRefresh] = useState(0);
  const [dataRefreshKey, setDataRefreshKey] = useState(0);

  // Pagination State (page is 1-based)
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 50,
  });

  // Convert Date objects to ISO strings for API and add other filters
  // Only include date params if they are not null (null means "ALL")
  const filterParams = useMemo(() => {
    const params = {};
    if (fromDate !== null) {
      params.fromDate = format(fromDate, 'yyyy-MM-dd');
    }
    if (toDate !== null) {
      params.toDate = format(toDate, 'yyyy-MM-dd');
    }
    if (selectedCategoryIds && selectedCategoryIds.length > 0) {
      params.categoryIds = selectedCategoryIds.join(',');
    }
    // Advanced filters
    if (minAmount !== null) {
      params.minAmount = minAmount;
    }
    if (maxAmount !== null) {
      params.maxAmount = maxAmount;
    }
    if (recipientQuery) {
      params.recipient = recipientQuery;
    }
    if (purposeQuery) {
      params.purpose = purposeQuery;
    }
    if (transactionType && transactionType !== 'all') {
      params.transactionType = transactionType;
    }
    return params;
  }, [fromDate, toDate, selectedCategoryIds, minAmount, maxAmount, recipientQuery, purposeQuery, transactionType]);

  // Reset to first page whenever filters change
  useEffect(() => {
    setPagination((prev) => ({ ...prev, page: 1 }));
  }, [filterParams]);

  // Custom Hooks für Daten mit automatischem Reload
  // dataRefreshKey is used to force refresh after import
  const { 
    data: transactions, 
    total: totalTransactions,
    loading: transactionsLoading,
    refetch: refetchTransactions
  } = useTransactionData(id, {
    limit: pagination.limit,
    offset: (Math.max(1, pagination.page) - 1) * pagination.limit,
    ...filterParams,
    _refreshKey: dataRefreshKey,
  });

  const { 
    summary, 
    loading: summaryLoading,
    refetch: refetchSummary
  } = useSummaryData(id, { ...filterParams, _refreshKey: dataRefreshKey });

  const { 
    chartData, 
    loading: chartLoading,
    refetch: refetchChart
  } = useChartData(id, 'month', { ...filterParams, _refreshKey: dataRefreshKey });

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
    console.log('Import completed successfully - refreshing all data');
    
    // Trigger Import History refresh
    setImportHistoryRefresh(prev => prev + 1);
    
    // Trigger data refresh for all hooks (transactions, summary, charts)
    setDataRefreshKey(prev => prev + 1);
    
    // Also explicitly refetch to ensure immediate update
    setTimeout(() => {
      refetchTransactions();
      refetchSummary();
      refetchChart();
    }, 500); // Small delay to ensure backend has processed
  }, [refetchTransactions, refetchSummary, refetchChart]);

  const dataLoading = transactionsLoading || summaryLoading || chartLoading;

  const tabs = [
    { id: 'data', label: 'Übersicht', icon: '📊' },
    { id: 'contracts', label: 'Verträge', icon: '📋' },
    { id: 'categories', label: 'Kategorien', icon: '🏷️' },
    { id: 'budgets', label: 'Budgets', icon: '💰' },
    { id: 'recipients', label: 'Empfänger/Absender', icon: '👥' },
    { id: 'comparison', label: 'Zeitraum-Vergleich', icon: '📈' },
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
              showSearch={false}
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
                // New pagination props
                page={pagination.page}
                pages={Math.max(1, Math.ceil((totalTransactions || 0) / pagination.limit))}
                pageSize={pagination.limit}
                total={totalTransactions}
                onPageChange={(newPage) => setPagination((prev) => ({ ...prev, page: newPage }))}
                onPageSizeChange={(newSize) => setPagination({ page: 1, limit: newSize })}
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
              refreshTrigger={dataRefreshKey}
            />
          </div>
        )}

        {/* Contracts Tab */}
        {activeTab === 'contracts' && (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Verträge für {currentAccount.name}
              </h2>
              <p className="text-gray-600">
                Automatisch erkannte wiederkehrende Transaktionen für dieses Konto.
              </p>
            </div>
            <RecurringTransactionsWidget 
              accountId={parseInt(id)}
              refreshTrigger={dataRefreshKey}
            />
          </div>
        )}

        {/* Budgets Tab */}
        {activeTab === 'budgets' && (
          <div>
            <BudgetsTab 
              accountId={id} 
              currency={currentAccount.currency}
              refreshTrigger={dataRefreshKey}
            />
          </div>
        )}

        {/* Recipients/Senders Tab */}
        {activeTab === 'recipients' && (
          <div>
            <RecipientsTab 
              accountId={id} 
              currency={currentAccount.currency}
              refreshTrigger={dataRefreshKey}
            />
          </div>
        )}

        {/* Comparison Tab */}
        {activeTab === 'comparison' && (
          <div>
            <ComparisonView accountId={id} />
          </div>
        )}

        {/* CSV Import & Mapping Tab */}
        {activeTab === 'csv-import' && (
          <div className="space-y-8">
            {/* CSV Import Wizard */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                CSV Import
              </h2>
              <CsvImportWizard
                accountId={id}
                onImportSuccess={handleUploadComplete}
              />
            </div>

            {/* Divider */}
            <div className="border-t border-gray-300" />

            {/* Import History */}
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Import-Historie & Rollback
              </h2>
              <ImportHistory
                accountId={parseInt(id)}
                refreshTrigger={importHistoryRefresh}
                onRollbackSuccess={() => {
                  // Reload transactions when rollback succeeds
                  console.log('Rollback completed, reloading data');
                  setImportHistoryRefresh(prev => prev + 1);
                }}
              />
            </div>
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
