import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import Card from '../common/Card';

/**
 * Chart-Komponente für Datenvisualisierung
 */
export default function DataChart({ data, type = 'line', title, currency = 'EUR' }) {
  const currencySymbols = {
    EUR: '€',
    USD: '$',
    GBP: '£',
    CHF: 'Fr',
  };

  const symbol = currencySymbols[currency] || currency;

  const formatAmount = (value) => {
    // Ensure value is a number
    const numValue = typeof value === 'number' ? value : parseFloat(value);
    
    // Check if conversion resulted in a valid number
    if (isNaN(numValue)) {
      return `0.00 ${symbol}`;
    }
    
    return `${numValue.toFixed(2)} ${symbol}`;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900 mb-1">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {formatAmount(entry.value)}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const ChartComponent = type === 'bar' ? BarChart : LineChart;
  const DataComponent = type === 'bar' ? Bar : Line;

  if (!data || data.length === 0) {
    return (
      <Card title={title}>
        <div className="text-center py-12 text-gray-500">
          Keine Daten verfügbar
        </div>
      </Card>
    );
  }

  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={300}>
        <ChartComponent data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="label" 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            stroke="#6b7280"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `${value} ${symbol}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend />
          
          {/* Einnahmen */}
          {data[0]?.income !== undefined && (
            <DataComponent
              type="monotone"
              dataKey="income"
              stroke="#10b981"
              fill="#10b981"
              name="Einnahmen"
              strokeWidth={2}
            />
          )}
          
          {/* Ausgaben */}
          {data[0]?.expenses !== undefined && (
            <DataComponent
              type="monotone"
              dataKey="expenses"
              stroke="#ef4444"
              fill="#ef4444"
              name="Ausgaben"
              strokeWidth={2}
            />
          )}
          
          {/* Aktueller Kontostand */}
          {data[0]?.balance !== undefined && (
            <DataComponent
              type="monotone"
              dataKey="balance"
              stroke="#3b82f6"
              fill="#3b82f6"
              name="Aktueller Kontostand"
              strokeWidth={2}
            />
          )}
        </ChartComponent>
      </ResponsiveContainer>
    </Card>
  );
}
