import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';
import Card from '../common/Card';

/**
 * CategoryPieChart - Visualisierung der Kategorien mit Kreisdiagramm
 * 
 * FEATURES:
 * - Kreisdiagramm für Ausgaben- und Einnahmen-Kategorien (getrennt)
 * - Interaktive Tooltips mit Details
 * - Klickbare Segmente für Drill-down
 * - Automatische Prozentberechnung
 * - Responsive Design
 * 
 * ERWEITERBARKEIT:
 * - Balkendiagramm für zeitlichen Verlauf pro Kategorie
 * - Trendanalyse (Monat-über-Monat)
 * - Vergleich mit Vormonat/Vorjahr
 * - Export als Bild/PDF
 * - Animationen beim Laden
 * 
 * @param {Object} props
 * @param {Array} props.data - Array von Kategorie-Statistiken
 * @param {string} props.currency - Währung (z.B. "EUR")
 * @param {boolean} props.loading - Zeigt Skeleton Loader
 * @param {Function} props.onSegmentClick - Callback bei Klick auf Segment
 * @param {string} props.type - 'expenses' oder 'income'
 */

/**
 * Custom Tooltip für detaillierte Informationen
 */
const CustomTooltip = ({ active, payload, currency }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-neutral-200" role="status" aria-live="polite">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-2xl">{data.icon}</span>
          <p className="font-semibold text-neutral-900">{data.name}</p>
        </div>
        <p className="text-sm text-neutral-600">
          Betrag: <span className="font-semibold text-gray-900">
            {new Intl.NumberFormat('de-DE', {
              style: 'currency',
              currency: currency,
            }).format(Math.abs(data.value))}
          </span>
        </p>
        <p className="text-sm text-neutral-600">
          Transaktionen: <span className="font-semibold text-neutral-900">{data.count}</span>
        </p>
        <p className="text-sm text-neutral-600">
          Anteil: <span className="font-semibold text-neutral-900">
            {data.percentage?.toFixed(1)}%
          </span>
        </p>
      </div>
    );
  }
  return null;
};

/**
 * Custom Label für Segmente (zeigt Prozentsatz)
 */
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, payload }) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  // Nur Labels > 5% anzeigen für bessere Lesbarkeit
  if (percent < 0.05) return null;

  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="text-xs font-semibold drop-shadow-lg"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

/**
 * Custom Legend mit Icons
 */
const CustomLegend = ({ payload }) => {
    return (
    <div className="flex flex-wrap gap-4 justify-center mt-4" role="list" aria-label="Legende">
      {payload.map((entry, index) => (
        <div
          key={`legend-${index}`}
          className="flex items-center gap-2 text-sm"
          role="listitem"
        >
          <div className="flex items-center gap-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
              aria-hidden="true"
            />
            <span className="text-lg" aria-hidden="true">{entry.payload.icon}</span>
          </div>
          <span className="text-neutral-700">{entry.value}</span>
        </div>
      ))}
    </div>
  );
};

function CategoryPieChart({ 
  data, 
  currency = 'EUR', 
  loading = false, 
  onSegmentClick,
  type = 'expenses',
  title 
}) {
  // Filter und transformiere Daten basierend auf Typ
  const chartData = useMemo(() => {
    if (!data || data.length === 0) return [];

    // Filter nach Typ (Ausgaben = negative Werte, Einnahmen = positive Werte)
    const filtered = data.filter(item => {
      if (type === 'expenses') {
        return item.total_amount < 0;
      } else {
        return item.total_amount > 0;
      }
    });

    // Transformiere für Recharts
    return filtered.map(item => ({
      name: item.category_name,
      value: Math.abs(item.total_amount),
      count: item.transaction_count,
      percentage: item.percentage || 0,
      color: item.color,
      icon: item.icon,
      categoryId: item.category_id,
    }));
  }, [data, type]);

  // Berechne Gesamtsumme
  const total = useMemo(() => {
    return chartData.reduce((sum, item) => sum + item.value, 0);
  }, [chartData]);

  // Skeleton Loader
    if (loading) {
    return (
      <Card>
        <div className="space-y-4">
          <div className="h-6 bg-neutral-200 rounded w-1/3 animate-pulse" />
          <div className="h-80 bg-neutral-100 rounded animate-pulse" />
        </div>
      </Card>
    );
  }

  // Empty State
    if (chartData.length === 0) {
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          {title || (type === 'expenses' ? 'Ausgaben nach Kategorie' : 'Einnahmen nach Kategorie')}
        </h3>
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-neutral-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-neutral-900">
            Keine {type === 'expenses' ? 'Ausgaben' : 'Einnahmen'}
          </h3>
          <p className="mt-1 text-sm text-neutral-500">
            Für diesen Zeitraum wurden keine {type === 'expenses' ? 'Ausgaben' : 'Einnahmen'} in Kategorien gefunden.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-neutral-900">
          {title || (type === 'expenses' ? 'Ausgaben nach Kategorie' : 'Einnahmen nach Kategorie')}
        </h3>
        <div className="text-right">
          <p className="text-sm text-neutral-600">Gesamt</p>
          <p className="text-xl font-bold text-neutral-900">
            {new Intl.NumberFormat('de-DE', {
              style: 'currency',
              currency: currency,
            }).format(total)}
          </p>
        </div>
      </div>

      {/* Pie Chart */}
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={120}
            fill="#8884d8"
            dataKey="value"
            onClick={(data) => {
              if (onSegmentClick) {
                onSegmentClick(data);
              }
            }}
            className="cursor-pointer"
          >
            {chartData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.color}
                className="hover:opacity-80 transition-opacity"
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip currency={currency} />} />
          <Legend content={<CustomLegend />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Stats Summary */}
      <div className="mt-6 pt-6 border-t border-neutral-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-sm text-neutral-600">Kategorien</p>
            <p className="text-2xl font-bold text-neutral-900">{chartData.length}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-neutral-600">Transaktionen</p>
            <p className="text-2xl font-bold text-neutral-900">
              {chartData.reduce((sum, item) => sum + item.count, 0)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-neutral-600">Durchschnitt</p>
            <p className="text-2xl font-bold text-neutral-900">
              {new Intl.NumberFormat('de-DE', {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 0,
                maximumFractionDigits: 0,
              }).format(total / chartData.length)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-neutral-600">Größte Kategorie</p>
            <p className="text-2xl font-bold text-neutral-900">
              {chartData[0]?.icon || '—'}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}

/**
 * CategoryBarChart - Balkendiagramm für Kategorie-Vergleich
 * 
 * VERWENDUNG:
 * Kann für zeitlichen Verlauf oder Vergleich mehrerer Kategorien verwendet werden
 */
export function CategoryBarChart({ data, currency = 'EUR', loading = false }) {
  if (loading) {
    return (
      <Card>
        <div className="h-80 bg-neutral-100 rounded animate-pulse"></div>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <div className="text-center py-12 text-neutral-500">
          Keine Daten verfügbar
        </div>
      </Card>
    );
  }

  return (
    <Card>
      <h3 className="text-lg font-semibold text-neutral-900 mb-4">
        Kategorien im Vergleich
      </h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip
            formatter={(value) => 
              new Intl.NumberFormat('de-DE', {
                style: 'currency',
                currency: currency,
              }).format(Math.abs(value))
            }
          />
          <Bar 
            dataKey="value" 
            fill="#3b82f6"
            radius={[8, 8, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

export default CategoryPieChart;
