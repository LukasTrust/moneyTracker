/**
 * ContractsPage
 * Full page view for managing recurring transactions (Verträge)
 */
import React from 'react';
import RecurringTransactionsList from '../components/recurring/RecurringTransactionsList';

const ContractsPage = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <RecurringTransactionsList showTitle={true} />
    </div>
  );
};

export default ContractsPage;
