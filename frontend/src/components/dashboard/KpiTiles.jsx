import React, { useEffect, useState } from 'react';
import { dashboardService } from '../../services/dashboardService';
import KpiTile from './KpiTile';

/**
 * KpiTiles - fetches summary and displays multiple KPI tiles
 * - Shows income, expenses, net balance and account count
 */
export default function KpiTiles({ className = '', params = {} }) {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await dashboardService.getSummary(params);
      setSummary(data);
    } catch (err) {
      console.error('Error fetching dashboard summary', err);
      setError(err.message || 'Fehler');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch();
  }, [JSON.stringify(params)]);

  if (loading && !summary) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-3"></div>
          <div className="grid grid-cols-2 gap-3">
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
            <div className="h-20 bg-gray-100 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !summary) {
    return (
      <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
        <div className="text-sm text-red-600">Fehler beim Laden der KPIs: {error}</div>
        <button onClick={fetch} className="mt-2 text-sm text-primary-600">Erneut laden</button>
      </div>
    );
  }

  const income = summary ? Number(summary.total_income || 0) : 0;
  const expenses = summary ? Number(summary.total_expenses || 0) : 0;
  const balance = summary ? Number(summary.current_balance || 0) : 0;
  const accounts = summary ? Number(summary.account_count || 0) : 0;

  // Decide accent color for balance (green when positive, red when negative)
  const balanceAccent = balance >= 0 ? 'green' : 'red';

  return (
    <div className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Schnelle KPIs</h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiTile label="Einnahmen" value={income} prefix="€" decimals={2} icon={'💶'} accent={'green'} />
        <KpiTile label="Ausgaben" value={Math.abs(expenses)} prefix="€" decimals={2} icon={'🛒'} accent={'red'} />
        <KpiTile label="Aktueller Kontostand" value={balance} prefix="€" decimals={2} icon={'💳'} accent={balanceAccent} />
        <KpiTile label="Konten" value={accounts} decimals={0} icon={'🏦'} accent={'purple'} />
      </div>
    </div>
  );
}
