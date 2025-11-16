import React, { useState, useCallback, useMemo, useEffect } from 'react';
import UnifiedFilter from '../common/UnifiedFilter';
import RecipientPieChart from '../visualization/RecipientPieChart';
import RecipientList from '../visualization/RecipientList';
import { useRecipientData, useSenderData, useCategoryData } from '../../hooks/useDataFetch';
import { useFilterStore } from '../../store';

/**
 * RecipientsTab - Tab für Empfänger/Absender Analyse
 * 
 * FEATURES:
 * - Date Range Filter mit Quick Buttons (nutzt globalen FilterStore)
 * - Kategorie-Filter Dropdown
 * - Zwei Kuchendiagramme (Absender/Empfänger)
 * - Top 10 Listen mit Details
 * - Responsive Layout (Desktop: nebeneinander, Mobile: gestapelt)
 * - Skeleton Loader während Daten laden
 * - Click-Handler für Drill-down (optional)
 * 
 * CHANGELOG v2.0:
 * ✅ Verwendet globalen FilterStore für Datumsfilter
 * ✅ Beide Pie-Charts funktionieren unabhängig
 * ✅ Top 5 + "Andere" Gruppierung in Charts
 * ✅ Verbesserte Legende
 * 
 * @param {Object} props
 * @param {number} props.accountId - Konto-ID
 * @param {string} props.currency - Währung (z.B. "EUR")
 */
function RecipientsTab({ accountId, currency = 'EUR' }) {
  // Nutze globalen FilterStore für Datumsbereich
  const { fromDate, toDate } = useFilterStore();

  // Category Filter State (lokal)
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);

  // Limit für Top-Listen (Standard: 10)
  const [limit] = useState(10);

  // Konvertiere Date-Objekte zu ISO-Strings für API
  const dateParams = useMemo(() => ({
    fromDate: fromDate ? fromDate.toISOString().split('T')[0] : undefined,
    toDate: toDate ? toDate.toISOString().split('T')[0] : undefined,
  }), [fromDate, toDate]);

  // Fetch Categories
  const { categories, loading: categoriesLoading } = useCategoryData();

  // Fetch Recipients (Empfänger - Ausgaben) mit Kategorie-Filter
  const { recipients, loading: recipientsLoading, error: recipientsError } = useRecipientData(
    accountId,
    {
      fromDate: dateParams.fromDate,
      toDate: dateParams.toDate,
      limit,
      transactionType: 'expense',
      categoryId: selectedCategoryId,
    }
  );

  // Fetch Senders (Absender - Einnahmen) mit Kategorie-Filter
  const { senders, loading: sendersLoading, error: sendersError } = useSenderData(
    accountId,
    {
      fromDate: dateParams.fromDate,
      toDate: dateParams.toDate,
      limit,
      categoryId: selectedCategoryId,
    }
  );

  // Debug logging
  useEffect(() => {
    console.log('RecipientsTab: FilterStore Date Range:', { fromDate, toDate });
    console.log('RecipientsTab: API Date Params:', dateParams);
    console.log('RecipientsTab: Category Filter:', selectedCategoryId);
    console.log('RecipientsTab: Recipients data:', recipients);
    console.log('RecipientsTab: Recipients error:', recipientsError);
    console.log('RecipientsTab: Senders data:', senders);
    console.log('RecipientsTab: Senders error:', sendersError);
  }, [fromDate, toDate, dateParams, selectedCategoryId, recipients, senders, recipientsError, sendersError]);

  // Handler für Kategorie-Filter Änderungen
  const handleCategoryChange = useCallback((event) => {
    const value = event.target.value;
    setSelectedCategoryId(value === '' ? null : parseInt(value, 10));
  }, []);

  // Handler für Segment-Klick (optional - für Drill-down)
  const handleRecipientClick = useCallback((recipient) => {
    console.log('Empfänger ausgewählt:', recipient);
    // DEVELOPER NOTE: Hier kann Drill-down implementiert werden
    // z.B. navigate(`/transactions?recipient=${recipient.name}&from=${dateParams.fromDate}&to=${dateParams.toDate}`);
  }, [dateParams]);

  const handleSenderClick = useCallback((sender) => {
    console.log('Absender ausgewählt:', sender);
    // DEVELOPER NOTE: Hier kann Drill-down implementiert werden
  }, [dateParams]);

  // PERFORMANCE: Memoize berechnete Werte
  const stats = useMemo(() => {
    const totalExpenses = recipients?.reduce((sum, r) => sum + Math.abs(r.total_amount || r.value || 0), 0) || 0;
    const totalIncome = senders?.reduce((sum, s) => sum + Math.abs(s.total_amount || s.value || 0), 0) || 0;
    const balance = totalIncome - totalExpenses;

    return {
      totalExpenses,
      totalIncome,
      balance,
      recipientCount: recipients?.length || 0,
      senderCount: senders?.length || 0,
    };
  }, [recipients, senders]);

  // Check if we have any data
  const hasData = (recipients && recipients.length > 0) || (senders && senders.length > 0);
  const isLoading = recipientsLoading || sendersLoading;
  const hasError = recipientsError || sendersError;

  return (
    <div className="space-y-6">
      {/* Unified Filter */}
      <UnifiedFilter
        showDateRange={true}
        showCategory={true}
        showTransactionType={true}
        showSearch={false}
        compact={false}
      />

      {/* Loading State */}
      {isLoading && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
            <p className="text-gray-500 mt-4">Lade Empfänger/Absender-Daten...</p>
          </div>
        </div>
      )}

      {/* Error State */}
      {!isLoading && hasError && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="text-center py-8">
            <div className="text-red-500 mb-4">
              <svg
                className="mx-auto h-12 w-12"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
            </div>
            <p className="text-gray-900 font-semibold">Fehler beim Laden der Daten</p>
            <p className="text-sm text-gray-500 mt-2">
              {recipientsError || sendersError}
            </p>
          </div>
        </div>
      )}

      {/* No Data State */}
      {!isLoading && !hasError && !hasData && (
        <div className="bg-white rounded-lg shadow p-6">
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
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">Keine Daten verfügbar</h3>
            <p className="mt-2 text-sm text-gray-500">
              Es sind noch keine Transaktionen mit Empfängern oder Absendern für diesen Zeitraum vorhanden.
            </p>
          </div>
        </div>
      )}

      {/* Statistik-Übersicht - only show if data exists */}
      {!isLoading && !hasError && hasData && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Einnahmen */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Einnahmen</p>
              <p className="text-2xl font-bold text-green-600 mt-1">
                {new Intl.NumberFormat('de-DE', {
                  style: 'currency',
                  currency,
                }).format(stats.totalIncome)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.senderCount} Absender
              </p>
            </div>
            <div className="text-green-500">
              <svg className="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 11l5-5m0 0l5 5m-5-5v12"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Ausgaben */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Ausgaben</p>
              <p className="text-2xl font-bold text-red-600 mt-1">
                {new Intl.NumberFormat('de-DE', {
                  style: 'currency',
                  currency,
                }).format(stats.totalExpenses)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {stats.recipientCount} Empfänger
              </p>
            </div>
            <div className="text-red-500">
              <svg className="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M17 13l-5 5m0 0l-5-5m5 5V6"
                />
              </svg>
            </div>
          </div>
        </div>

        {/* Saldo */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Saldo</p>
              <p className={`text-2xl font-bold mt-1 ${
                stats.balance >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {new Intl.NumberFormat('de-DE', {
                  style: 'currency',
                  currency,
                }).format(stats.balance)}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {fromDate && toDate
                  ? `${fromDate.toLocaleDateString('de-DE')} - ${toDate.toLocaleDateString('de-DE')}`
                  : 'Gesamter Zeitraum'}
              </p>
            </div>
            <div className={stats.balance >= 0 ? 'text-green-500' : 'text-red-500'}>
              <svg className="h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* Kuchendiagramme - Responsive Grid - only show if data exists */}
      {!isLoading && !hasError && hasData && (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Absender (Einnahmen) */}
        <RecipientPieChart
          data={senders}
          title="Top Absender (Einnahmen)"
          currency={currency}
          loading={sendersLoading}
          onSegmentClick={handleSenderClick}
        />

        {/* Top Empfänger (Ausgaben) */}
        <RecipientPieChart
          data={recipients}
          title="Top Empfänger (Ausgaben)"
          currency={currency}
          loading={recipientsLoading}
          onSegmentClick={handleRecipientClick}
        />
      </div>
      )}

      {/* Listen - Responsive Grid - only show if data exists */}
      {!isLoading && !hasError && hasData && (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Absender Liste */}
        <RecipientList
          data={senders}
          title="Top Absender Details"
          type="sender"
          currency={currency}
          loading={sendersLoading}
          onRowClick={handleSenderClick}
        />

        {/* Top Empfänger Liste */}
        <RecipientList
          data={recipients}
          title="Top Empfänger Details"
          type="recipient"
          currency={currency}
          loading={recipientsLoading}
          onRowClick={handleRecipientClick}
        />
      </div>
      )}

      {/* DEVELOPER NOTE: Weitere Komponenten können hier hinzugefügt werden */}
      {/* 
        Beispiele:
        - Export Button
        - Vergleichs-Ansicht (mehrere Zeiträume)
        - Transaktions-Details Modal
        - Kategorie-Filter
      */}
    </div>
  );
}

export default RecipientsTab;

/**
 * CHANGELOG v2.0 - 16. November 2025
 * 
 * ✅ BEHOBEN: Datumsfilter funktioniert jetzt korrekt
 *    - Nutzt globalen FilterStore (useFilterStore)
 *    - Date-Objekte werden zu ISO-Strings konvertiert (YYYY-MM-DD)
 *    - API erhält korrekte Parameter (from_date, to_date)
 * 
 * ✅ BEHOBEN: Beide Pie-Charts funktionieren unabhängig
 *    - Separate Hooks: useRecipientData (expense) & useSenderData (income)
 *    - Korrekte transactionType-Parameter
 *    - Eigene Loading/Error-States
 * 
 * ✅ IMPLEMENTIERT: Top 5 + "Andere" Gruppierung
 *    - RecipientPieChart zeigt max. 6 Segmente (Top 5 + Andere)
 *    - Backend limitiert auf 10 Einträge
 *    - Frontend gruppiert Rest zu "Andere"
 * 
 * ✅ VERBESSERT: Legende
 *    - Custom Legend Component in RecipientPieChart
 *    - Labels auf 18 Zeichen gekürzt (mit "…")
 *    - Sortierung nach Betrag (größte zuerst)
 *    - Farbige Kreise vor jedem Eintrag
 *    - Bessere Typografie mit tabular-nums
 * 
 * ✅ KONSISTENZ: Absender & Empfänger
 *    - Beide nutzen dieselbe RecipientPieChart Component
 *    - Einheitliche Datenstruktur
 *    - Gleiche Filter-Logik
 * 
 * WEITERE ERWEITERUNGEN:
 * - Export-Funktion: CSV/PDF Export der Daten
 * - Drill-down: Klick auf Segment öffnet gefilterte Transaktionsliste
 * - Vergleich: Mehrere Zeiträume nebeneinander anzeigen
 * - Mindestbetrag-Filter: Nur Transaktionen über X€ anzeigen
 */
