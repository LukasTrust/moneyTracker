import React from 'react';
import { useNavigate } from 'react-router-dom';
import Card from '../common/Card';
import { format } from 'date-fns';
import { de } from 'date-fns/locale';

/**
 * Einzelne Account-Card für die Liste
 */
export default function AccountCard({ account }) {
  const navigate = useNavigate();

  const handleClick = () => {
    navigate(`/accounts/${account.id}`);
  };

  const currencySymbols = {
    EUR: '€',
    USD: '$',
    GBP: '£',
    CHF: 'Fr',
  };

  // Konten-Icons basierend auf Namen oder Typ
  const getAccountIcon = () => {
    const name = account.name.toLowerCase();
    if (name.includes('giro') || name.includes('checking')) return '🏦';
    if (name.includes('spar') || name.includes('savings')) return '💰';
    if (name.includes('kredit') || name.includes('credit')) return '💳';
    if (name.includes('depot') || name.includes('investment')) return '📈';
    if (name.includes('paypal')) return '💵';
    if (name.includes('cash') || name.includes('bar')) return '💶';
    return '💼'; // Default
  };

  // Farben basierend auf Währung oder Position
  const getAccountColor = () => {
    const colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ec4899', '#14b8a6'];
    // Konsistente Farbe basierend auf Account-ID
    return colors[account.id % colors.length];
  };

  const accountIcon = getAccountIcon();
  const accountColor = getAccountColor();

  return (
    <Card 
      hoverable
      clickable
      onClick={handleClick}
      className="transition-all duration-200 hover:shadow-lg"
    >
      <div className="flex items-start gap-4">
        {/* Icon & Color Badge */}
        <div
          className="w-14 h-14 rounded-xl flex items-center justify-center text-3xl flex-shrink-0 shadow-sm"
          style={{ backgroundColor: accountColor + '20' }}
        >
          {accountIcon}
        </div>

        {/* Account Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 truncate">
                {account.name}
              </h3>
              {account.description && (
                <p className="text-sm text-gray-600 mt-1 line-clamp-2">{account.description}</p>
              )}
            </div>
            <svg className="h-5 w-5 text-gray-400 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </div>

          {/* Meta Information */}
          <div className="flex items-center gap-4 mt-3 text-sm">
            <div className="flex items-center gap-1.5">
              <div
                className="w-3 h-3 rounded"
                style={{ backgroundColor: accountColor }}
              />
              <span className="text-gray-700 font-medium">
                {currencySymbols[account.currency] || account.currency}
              </span>
            </div>
            <span className="text-gray-400">•</span>
            <span className="flex items-center gap-1.5 text-gray-500">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {account.created_at ? format(new Date(account.created_at), 'dd.MM.yyyy', { locale: de }) : 'Unbekannt'}
            </span>
          </div>
        </div>
      </div>
    </Card>
  );
}
