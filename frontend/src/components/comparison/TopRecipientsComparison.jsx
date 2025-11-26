import React from 'react';

/**
 * Top Recipients Comparison
 * Show top recipients side by side
 */
export default function TopRecipientsComparison({ data }) {
  const { period1, period2 } = data;

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(value);
  };

  const RecipientCard = ({ period, recipients }) => (
    <div className="bg-neutral-50 rounded-lg p-4">
      <h3 className="text-sm font-semibold text-neutral-900 mb-4">
        {period}
      </h3>
      <div className="space-y-3">
        {recipients.length > 0 ? (
          recipients.map((recipient, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between p-3 bg-white rounded-md shadow-sm"
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-neutral-900 truncate">
                  {recipient.recipient}
                </p>
                {recipient.category_name && (
                  <p className="text-xs text-neutral-500">
                    {recipient.category_name}
                  </p>
                )}
              </div>
              <div className="ml-4 text-right">
                <p className="text-sm font-semibold text-neutral-900">
                  {formatCurrency(recipient.total_amount)}
                </p>
                <p className="text-xs text-neutral-500">
                  {recipient.transaction_count} Trans.
                </p>
              </div>
            </div>
          ))
        ) : (
          <p className="text-sm text-neutral-500 text-center py-4">
            Keine Transaktionen
          </p>
        )}
      </div>
    </div>
  );

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-neutral-900 mb-4">
        Top Empfänger/Absender
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RecipientCard
          period={period1.period_label}
          recipients={period1.top_recipients}
        />
        <RecipientCard
          period={period2.period_label}
          recipients={period2.top_recipients}
        />
      </div>
    </div>
  );
}
