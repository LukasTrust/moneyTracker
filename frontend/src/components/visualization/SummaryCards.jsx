import React from 'react';
import Card from '../common/Card';

/**
 * Summary Cards für Einnahmen, Ausgaben, Aktueller Kontostand
 */
export default function SummaryCards({ summary, currency = 'EUR' }) {
  const currencySymbols = {
    EUR: '€',
    USD: '$',
    GBP: '£',
    CHF: 'Fr',
  };

  const symbol = currencySymbols[currency] || currency;

  const formatAmount = (amount) => {
    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(Math.abs(amount || 0));
  };

  const cards = [
    {
      title: 'Einnahmen',
      value: summary?.total_income || 0,
      icon: (
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      ),
      color: 'green',
      bgColor: 'bg-green-50',
      textColor: 'text-green-600',
      borderColor: 'border-green-200',
    },
    {
      title: 'Ausgaben',
      value: summary?.total_expenses || 0,
      icon: (
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
        </svg>
      ),
      color: 'red',
      bgColor: 'bg-red-50',
      textColor: 'text-red-600',
      borderColor: 'border-red-200',
    },
    {
      title: 'Aktueller Kontostand',
      value: summary?.current_balance || 0,
      icon: (
        <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: summary?.current_balance >= 0 ? 'blue' : 'orange',
      bgColor: summary?.current_balance >= 0 ? 'bg-blue-50' : 'bg-orange-50',
      textColor: summary?.current_balance >= 0 ? 'text-blue-600' : 'text-orange-600',
      borderColor: summary?.current_balance >= 0 ? 'border-blue-200' : 'border-orange-200',
    },
  ];

  // Show message if no data
  if (!summary || summary.transaction_count === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center mb-6">
        <p className="text-gray-500">Keine Daten verfügbar</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
      {cards.map((card, index) => (
        <div
          key={index}
          className={`${card.bgColor} border ${card.borderColor} rounded-lg p-6`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">
                {card.title}
              </p>
              <p className={`text-3xl font-bold ${card.textColor}`}>
                {card.value < 0 ? '-' : ''}
                {formatAmount(card.value)} {symbol}
              </p>
              {summary?.transaction_count && index === 2 && (
                <p className="text-xs text-gray-500 mt-2">
                  {summary.transaction_count} Transaktionen
                </p>
              )}
            </div>
            <div className={card.textColor}>
              {card.icon}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
