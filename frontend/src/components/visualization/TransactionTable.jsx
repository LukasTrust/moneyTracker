import React, { useState } from 'react';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';
import Card from '../common/Card';
import Pagination from '../common/Pagination';

/**
 * Transaktions-Tabelle mit Pagination
 */
export default function TransactionTable({ 
  transactions = [], 
  currency = 'EUR',
  loading = false,
  // Pagination props
  page = 1,
  pages = 1,
  pageSize = 50,
  total = 0,
  onPageChange = () => {},
  onPageSizeChange = () => {},
}) {
  const currencySymbols = {
    EUR: '€',
    USD: '$',
    GBP: '£',
    CHF: 'Fr',
  };

  const symbol = currencySymbols[currency] || currency;

  const formatAmount = (amount) => {
    const absAmount = Math.abs(amount || 0);
    const formatted = new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(absAmount);
    
    return amount < 0 ? `-${formatted}` : formatted;
  };

  const formatDate = (dateString) => {
    try {
      return format(new Date(dateString), 'dd.MM.yyyy', { locale: de });
    } catch {
      return dateString;
    }
  };

  if (transactions.length === 0 && !loading) {
    return (
      <Card title="Transaktionen">
        <div className="text-center py-12 text-gray-500">
          <svg
            className="mx-auto h-12 w-12 text-gray-400 mb-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
          Keine Transaktionen vorhanden
        </div>
      </Card>
    );
  }

  return (
    <Card title="Transaktionen">
      <Pagination
        page={page}
        pages={pages}
        pageSize={pageSize}
        total={total}
        loading={loading}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
      />

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Datum
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Betrag
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Empfänger
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Verwendungszweck
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {transactions.map((transaction) => {
              const data = typeof transaction.data === 'string' 
                ? JSON.parse(transaction.data) 
                : transaction.data;
              
              const amount = parseFloat(data.amount || 0);
              const isNegative = amount < 0;

              return (
                <tr key={transaction.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(data.date)}
                  </td>
                    <td className={`px-6 py-4 whitespace-nowrap text-sm font-medium text-right ${
                      isNegative ? 'text-red-600' : 'text-green-600'
                    }`}>
                      {formatAmount(amount)} {symbol}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      <div className="max-w-xs truncate">
                        {data.recipient || '-'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      <div className="max-w-xs truncate">
                        {data.purpose || data.verwendungszweck || data.description || '-'}
                      </div>
                    </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      
    </Card>
  );
}
