import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import Card from '../common/Card';

/**
 * RecipientPieChart - Kuchendiagramm für Absender/Empfänger Visualisierung
 * 
 * @param {Object} props
 * @param {Array} props.data - Array von {recipient/name, total_amount/value, transaction_count/count} Objekten
 * @param {string} props.title - Diagramm-Titel (z.B. "Top Absender")
 * @param {string} props.currency - Währungssymbol (z.B. "EUR")
 * @param {boolean} props.loading - Zeigt Skeleton Loader wenn true
 * @param {Function} props.onSegmentClick - Optional: Callback bei Klick auf Segment
 * 
 * FEATURES:
 * - Top 5 Einträge + "Andere" Gruppierung
 * - Verbesserte Custom Legend mit Kürzung langer Labels
 * - Sortierung nach Betrag (größte zuerst)
 * - Responsive Design
 */

// Farbpalette für Segmente (6 Farben: Top 5 + "Andere")
const COLORS = [
  '#3b82f6', // blue-500 - Top 1
  '#10b981', // green-500 - Top 2
  '#f59e0b', // amber-500 - Top 3
  '#8b5cf6', // violet-500 - Top 4
  '#ec4899', // pink-500 - Top 5
  '#94a3b8', // slate-400 - "Andere"
];

/**
 * Hilfsfunktion: Kürzt lange Strings
 */
const truncateString = (str, maxLength = 18) => {
  if (!str || str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '…';
};

/**
 * Custom Legend Component - Verbesserte Typografie und Layout
 */
const CustomLegend = ({ chartData, currency }) => {
  // Sortiere nach Betrag absteigend (größte zuerst)
  const sortedData = [...chartData].sort((a, b) => b.value - a.value);

  return (
    <div className="mt-6 space-y-2">
      {sortedData.map((entry, index) => {
        const originalIndex = chartData.findIndex(item => item.name === entry.name);
        const color = COLORS[originalIndex % COLORS.length];
        const truncatedName = truncateString(entry.name, 18);
        const percentage = entry.percentage || 0;

        return (
          <div
            key={`legend-${index}`}
            className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {/* Links: Kreis + Name */}
            <div className="flex items-center space-x-3 flex-1 min-w-0">
              <div
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: color }}
              />
              <span
                className="text-sm font-medium text-gray-900 truncate"
                title={entry.name}
              >
                {truncatedName}
              </span>
            </div>

            {/* Rechts: Betrag + Prozent */}
            <div className="flex items-center space-x-4 flex-shrink-0">
              <span className="text-sm font-semibold text-gray-900 tabular-nums">
                {new Intl.NumberFormat('de-DE', {
                  style: 'currency',
                  currency: currency,
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 0,
                }).format(entry.value)}
              </span>
              <span className="text-sm text-gray-500 w-12 text-right tabular-nums">
                {percentage.toFixed(1)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

/**
 * Custom Tooltip für detaillierte Informationen
 */
const CustomTooltip = ({ active, payload, currency }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const name = data.name || data.recipient;
    const value = data.value || data.total_amount;
    const count = data.count || data.transaction_count;
    const percentage = data.percentage;
    
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold text-gray-900 mb-2">{name}</p>
        <p className="text-sm text-gray-600">
          Betrag: <span className="font-semibold text-gray-900">
            {new Intl.NumberFormat('de-DE', {
              style: 'currency',
              currency: currency,
            }).format(Math.abs(value))}
          </span>
        </p>
        <p className="text-sm text-gray-600">
          Transaktionen: <span className="font-semibold text-gray-900">{count}</span>
        </p>
        <p className="text-sm text-gray-600">
          Anteil: <span className="font-semibold text-gray-900">
            {percentage ? `${percentage.toFixed(1)}%` : 'N/A'}
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
const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
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
      className="text-xs font-semibold"
    >
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

function RecipientPieChart({ data, title, currency = 'EUR', loading = false, onSegmentClick }) {
  console.log(`[${title}] RecipientPieChart render:`, { data, loading, dataLength: data?.length });

  // Skeleton Loader während Daten laden
  if (loading) {
    return (
      <Card>
        <div className="space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse"></div>
          <div className="h-80 bg-gray-100 rounded animate-pulse"></div>
        </div>
      </Card>
    );
  }

  // Keine Daten vorhanden
  if (!data || data.length === 0) {
    console.log(`[${title}] No data available`);
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p className="mt-2 text-sm">Keine Daten verfügbar</p>
            <p className="text-xs text-gray-400 mt-1">
              Ändere den Zeitraum oder lade Transaktionen hoch
            </p>
          </div>
        </div>
      </Card>
    );
  }

  // Berechne Gesamtsumme für Prozentangaben
  // Normalize data format (support both old and new API format)
  const normalizedData = data.map(item => ({
    name: item.name || item.recipient,
    value: Math.abs(item.value || item.total_amount), // WICHTIG: Absolute Werte für PieChart
    originalValue: item.value || item.total_amount, // Originalwert für Anzeige
    count: item.count || item.transaction_count,
  }));
  
  // Sortiere nach absolutem Betrag absteigend
  normalizedData.sort((a, b) => b.value - a.value);
  
  const total = normalizedData.reduce((sum, item) => sum + item.value, 0);

  // Füge Prozentangaben hinzu
  const dataWithPercentage = normalizedData.map((item) => ({
    ...item,
    percentage: (item.value / total) * 100,
  }));

  // WICHTIG: Top 5 + "Andere" Gruppierung
  let chartData = [];
  
  if (dataWithPercentage.length <= 5) {
    // Weniger als 5 Einträge: Zeige alle
    chartData = dataWithPercentage;
  } else {
    // Mehr als 5: Top 5 + "Andere"
    const top5 = dataWithPercentage.slice(0, 5);
    const rest = dataWithPercentage.slice(5);
    
    const restTotal = rest.reduce((sum, item) => sum + item.value, 0);
    const restCount = rest.reduce((sum, item) => sum + item.count, 0);
    const restPercentage = (restTotal / total) * 100;
    
    chartData = [
      ...top5,
      {
        name: `Andere (${rest.length})`,
        value: restTotal,
        originalValue: -restTotal, // Für Ausgaben negativ
        count: restCount,
        percentage: restPercentage,
        isOther: true
      }
    ];
  }

  console.log('RecipientPieChart:', { 
    title, 
    originalDataLength: data.length, 
    chartDataLength: chartData.length,
    showingOthers: chartData.length === 6,
    sampleChartData: chartData.slice(0, 2),
    total,
    chartDataIsValid: chartData.every(d => d.value > 0)
  });

  // Safety Check: Stelle sicher, dass alle Werte positiv sind
  if (chartData.some(d => !d.value || d.value <= 0)) {
    console.error(`[${title}] Invalid chart data detected:`, chartData);
    return (
      <Card>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="h-80 flex items-center justify-center">
          <div className="text-center text-red-500">
            <p className="text-sm">Fehler beim Laden der Daten</p>
            <p className="text-xs mt-1">Ungültige Werte erkannt</p>
          </div>
        </div>
      </Card>
    );
  }

  // Handler für Segment-Klick
  const handleSegmentClick = (entry, index) => {
    if (onSegmentClick && !entry.isOther) {
      onSegmentClick(entry);
    }
  };

  return (
    <Card>
      <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
      
      <ResponsiveContainer width="100%" height={350}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={renderCustomLabel}
            outerRadius={110}
            fill="#8884d8"
            dataKey="value"
            nameKey="name"
            onClick={handleSegmentClick}
            style={{ cursor: onSegmentClick ? 'pointer' : 'default' }}
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
                className="hover:opacity-80 transition-opacity"
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip currency={currency} />} />
        </PieChart>
      </ResponsiveContainer>

      {/* Custom Legend - Ersetzt die Standard-Recharts-Legende */}
      <CustomLegend chartData={chartData} currency={currency} />

      {/* Statistik unter dem Diagramm */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-sm text-gray-600">Gesamt</p>
            <p className="text-lg font-semibold text-gray-900">
              {new Intl.NumberFormat('de-DE', {
                style: 'currency',
                currency: currency,
              }).format(total)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Einträge</p>
            <p className="text-lg font-semibold text-gray-900">{data.length}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Angezeigt</p>
            <p className="text-lg font-semibold text-gray-900">
              {chartData.length === 6 ? 'Top 5 + Andere' : `${chartData.length}`}
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}

export default RecipientPieChart;

/**
 * CHANGELOG v2.0:
 * ✅ Top 5 + "Andere" Gruppierung implementiert
 * ✅ Custom Legend mit verbesserter Typografie
 * ✅ Labels auf 18 Zeichen gekürzt mit "…"
 * ✅ Legende nach Betrag sortiert (größte zuerst)
 * ✅ Farbige Kreise vor jedem Legendeneintrag
 * ✅ Responsive Layout mit Hover-Effekten
 * ✅ Tabular Numbers für bessere Zahlen-Alignment
 * ✅ Beide Charts funktionieren unabhängig voneinander
 * 
 * ERWEITERBARKEITS-GUIDE:
 * 
 * 1. Weitere Filter hinzufügen:
 *    - Props erweitern: categoryFilter, amountRange, etc.
 *    - In Parent-Komponente filtern vor Übergabe an RecipientPieChart
 * 
 * 2. Export-Funktion:
 *    const handleExport = () => {
 *      const csv = data.map(d => `${d.name},${d.value},${d.count}`).join('\n');
 *      const blob = new Blob([csv], { type: 'text/csv' });
 *      saveAs(blob, 'recipients.csv');
 *    };
 * 
 * 3. Animation hinzufügen:
 *    import { motion } from 'framer-motion';
 *    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
 *      <PieChart>...</PieChart>
 *    </motion.div>
 * 
 * 4. Drill-down zu Transaktionen:
 *    const handleSegmentClick = (entry) => {
 *      navigate(`/transactions?recipient=${entry.name}`);
 *    };
 */
