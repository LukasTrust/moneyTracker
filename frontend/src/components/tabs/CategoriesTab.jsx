import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { format } from 'date-fns';
import UnifiedFilter from '../common/UnifiedFilter';
import CategoryManager from '../categories/CategoryManager';
import CategoryMappingEditor from '../categories/CategoryMappingEditor';
import CategoryPieChart from '../categories/CategoryPieChart';
import Button from '../common/Button';
import Card from '../common/Card';
import { useCategoryData, useCategoryStatistics } from '../../hooks/useDataFetch';
import { useFilterStore } from '../../store';

/**
 * CategoriesTab - Haupt-Tab für Kategorie-Management und -Visualisierung
 * 
 * FEATURES:
 * - CRUD für globale Kategorien
 * - Mapping-Editor für Absender/Empfänger/Verwendungszweck
 * - Visualisierung der Ausgaben/Einnahmen pro Kategorie
 * - Date Range Filter für dynamische Filterung
 * - Zwei Modi: "Verwalten" (CRUD) und "Analysieren" (Visualisierung)
 * 
 * ARCHITEKTUR:
 * - Kategorien sind global (nicht Account-spezifisch)
 * - Visualisierung ist Account-spezifisch (zeigt Daten für aktuellen Account)
 * - Mappings sind global, wirken aber auf alle Accounts
 * 
 * ERWEITERBARKEIT:
 * - Export/Import von Kategorien und Mappings
 * - Bulk-Operations auf Kategorien
 * - Kategorie-Templates für häufige Use-Cases
 * - Drill-down: Klick auf Segment zeigt Transaktionen
 * - Vergleich mehrerer Zeiträume
 * - Budget-Funktionen pro Kategorie
 * 
 * @param {Object} props
 * @param {number} props.accountId - Konto-ID für Visualisierung
 * @param {string} props.currency - Währung (z.B. "EUR")
 */
function CategoriesTab({ accountId, currency = 'EUR' }) {
  // View Mode: 'manage' oder 'analyze'
  const [viewMode, setViewMode] = useState('analyze');
  
  // Selected Category für Mapping Editor
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showMappingEditor, setShowMappingEditor] = useState(false);

  // Global Date Filter Store
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

  // Fetch Daten
  const { categories, loading: categoriesLoading, refetch: refetchCategories } = useCategoryData();
  const { 
    categoryData, 
    loading: statsLoading, 
    error: statsError,
    refetch: refetchStats 
  } = useCategoryStatistics(accountId, { 
    fromDate: fromDate !== null ? format(fromDate, 'yyyy-MM-dd') : undefined, 
    toDate: toDate !== null ? format(toDate, 'yyyy-MM-dd') : undefined,
    categoryIds: selectedCategoryIds && selectedCategoryIds.length > 0 ? selectedCategoryIds.join(',') : undefined,
    minAmount: minAmount !== null ? minAmount : undefined,
    maxAmount: maxAmount !== null ? maxAmount : undefined,
    recipient: recipientQuery || undefined,
    purpose: purposeQuery || undefined,
    transactionType: transactionType && transactionType !== 'all' ? transactionType : undefined
  });

  /**
   * Aktualisiere selectedCategory, wenn Kategorien neu geladen werden
   */
  useEffect(() => {
    if (selectedCategory && categories && categories.length > 0) {
      const updated = categories.find(cat => cat.id === selectedCategory.id);
      if (updated) {
        setSelectedCategory(updated);
      }
    }
  }, [categories]); // Nur categories in deps, nicht selectedCategory (würde Loop erzeugen)

  /**
   * Handler für Kategorie-Änderungen (Erstellen/Bearbeiten/Löschen)
   */
  const handleCategoryChange = useCallback(() => {
    refetchCategories();
    refetchStats();
  }, [refetchCategories, refetchStats]);

  /**
   * Handler für Segment-Klick im Pie Chart
   */
  const handleSegmentClick = useCallback((segment) => {
    console.log('Kategorie-Segment angeklickt:', segment);
    // Example: navigate(`/accounts/${accountId}/transactions?category=${segment.categoryId}&from=${fromDate}&to=${toDate}`);
  }, [accountId, fromDate, toDate]);

  /**
   * Öffnet Mapping-Editor für Kategorie
   */
  const handleEditMappings = useCallback((category) => {
    setSelectedCategory(category);
    setShowMappingEditor(true);
  }, []);

  /**
   * Schließt Mapping-Editor
   */
  const handleCloseMappingEditor = useCallback(() => {
    setShowMappingEditor(false);
    setSelectedCategory(null);
    refetchCategories(); // Refresh categories after mapping changes
    refetchStats(); // Refresh stats after mapping changes
  }, [refetchCategories, refetchStats]);

  /**
   * Handler nach erfolgreichem Speichern der Mappings (ohne Editor zu schließen)
   */
  const handleMappingsSaved = useCallback(() => {
    refetchCategories(); // Refresh categories after mapping changes
    refetchStats(); // Refresh stats after mapping changes
  }, [refetchCategories, refetchStats]);

  /**
   * Separate Ausgaben und Einnahmen
   */
  const { expenseData, incomeData, stats } = useMemo(() => {
    // Handle undefined or null categoryData
    if (!categoryData || !Array.isArray(categoryData)) {
      return {
        expenseData: [],
        incomeData: [],
        stats: {
          totalExpenses: 0,
          totalIncome: 0,
          balance: 0,
          categoriesWithExpenses: 0,
          categoriesWithIncome: 0,
        }
      };
    }

    const expenses = categoryData.filter(item => item.total_amount < 0);
    const income = categoryData.filter(item => item.total_amount > 0);
    
    const totalExpenses = expenses.reduce((sum, item) => sum + Math.abs(item.total_amount), 0);
    const totalIncome = income.reduce((sum, item) => sum + Math.abs(item.total_amount), 0);
    
    return {
      expenseData: expenses,
      incomeData: income,
      stats: {
        totalExpenses,
        totalIncome,
        balance: totalIncome - totalExpenses,
        categoriesWithExpenses: expenses.length,
        categoriesWithIncome: income.length,
      }
    };
  }, [categoryData]);

  return (
    <div className="space-y-6">
      {/* Header with Mode Toggle */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Kategorien</h2>
          <p className="text-sm text-gray-600 mt-1">
            {viewMode === 'manage' 
              ? 'Kategorien erstellen, bearbeiten und Zuordnungen verwalten'
              : 'Ausgaben und Einnahmen nach Kategorien analysieren'
            }
          </p>
        </div>
        
        {/* Mode Toggle */}
        <div className="flex gap-2 bg-gray-100 p-1 rounded-lg">
          <button
            onClick={() => setViewMode('analyze')}
            className={`
              px-4 py-2 rounded-md font-medium text-sm transition-colors
              ${viewMode === 'analyze'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <svg className="h-5 w-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Analysieren
          </button>
          <button
            onClick={() => setViewMode('manage')}
            className={`
              px-4 py-2 rounded-md font-medium text-sm transition-colors
              ${viewMode === 'manage'
                ? 'bg-white text-primary-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-900'
              }
            `}
          >
            <svg className="h-5 w-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Verwalten
          </button>
        </div>
      </div>

      {/* MANAGE MODE: Category Management & Mapping Editor */}
      {viewMode === 'manage' && (
        <div className="space-y-6">
          {/* Mapping Editor (wenn Kategorie ausgewählt) */}
          {showMappingEditor && selectedCategory ? (
            <div>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleCloseMappingEditor}
                className="mb-4"
              >
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                Zurück zur Übersicht
              </Button>
              <CategoryMappingEditor
                category={selectedCategory}
                accountId={accountId}
                onSave={handleMappingsSaved}
                onCancel={handleCloseMappingEditor}
              />
            </div>
          ) : (
            <>
              {/* Category Manager */}
              <CategoryManager 
                accountId={accountId}
                onCategoryChange={handleCategoryChange} 
              />
            </>
          )}
        </div>
      )}

      {/* ANALYZE MODE: Visualization */}
      {viewMode === 'analyze' && (
        <div className="space-y-6">
          {/* Unified Filter */}
          <UnifiedFilter
            showDateRange={true}
            showCategory={true}
            showTransactionType={true}
            showSearch={false}
            compact={false}
          />

          {/* Stats Cards - only show if data exists and no error */}
          {!statsLoading && !statsError && categoryData && categoryData.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Gesamtausgaben</p>
                  <p className="text-2xl font-bold text-red-600">
                    {new Intl.NumberFormat('de-DE', {
                      style: 'currency',
                      currency: currency,
                    }).format(stats.totalExpenses)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats.categoriesWithExpenses} Kategorien
                  </p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Gesamteinnahmen</p>
                  <p className="text-2xl font-bold text-green-600">
                    {new Intl.NumberFormat('de-DE', {
                      style: 'currency',
                      currency: currency,
                    }).format(stats.totalIncome)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats.categoriesWithIncome} Kategorien
                  </p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Saldo</p>
                  <p className={`text-2xl font-bold ${stats.balance >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {new Intl.NumberFormat('de-DE', {
                      style: 'currency',
                      currency: currency,
                    }).format(stats.balance)}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {((stats.balance / (stats.totalIncome || 1)) * 100).toFixed(1)}% Sparquote
                  </p>
                </div>
              </Card>

              <Card>
                <div className="text-center">
                  <p className="text-sm text-gray-600 mb-1">Kategorien gesamt</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {categories.length}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {stats.categoriesWithExpenses + stats.categoriesWithIncome} aktiv
                  </p>
                </div>
              </Card>
            </div>
          )}

          {/* Loading State */}
          {statsLoading && (
            <Card>
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
                <p className="text-gray-500 mt-4">Lade Statistiken...</p>
              </div>
            </Card>
          )}

          {/* Error State */}
          {!statsLoading && statsError && (
            <Card>
              <div className="text-center py-8">
                <p className="text-red-500 mb-4">Fehler beim Laden der Kategorie-Statistiken</p>
                <Button onClick={refetchStats}>Erneut versuchen</Button>
              </div>
            </Card>
          )}

          {/* No Data State */}
          {!statsLoading && !statsError && (!categoryData || categoryData.length === 0) && (
            <Card>
              <div className="text-center py-12">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900">Keine Daten verfügbar</h3>
                <p className="mt-2 text-sm text-gray-500">
                  Es sind noch keine Transaktionen für diesen Zeitraum vorhanden.
                </p>
              </div>
            </Card>
          )}

          {/* Pie Charts - only show if data exists */}
          {!statsLoading && !statsError && categoryData && categoryData.length > 0 && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Ausgaben */}
              <CategoryPieChart
                data={categoryData}
                type="expenses"
                currency={currency}
                loading={statsLoading}
                onSegmentClick={handleSegmentClick}
              />

              {/* Einnahmen */}
              <CategoryPieChart
                data={categoryData}
                type="income"
                currency={currency}
                loading={statsLoading}
                onSegmentClick={handleSegmentClick}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CategoriesTab;
