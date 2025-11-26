import React, { useEffect, useState } from 'react';
import useAccountStore from '../../store/accountStore';
import AccountCard from './AccountCard';
import Button from '../common/Button';
import LoadingSpinner from '../common/LoadingSpinner';
import ErrorMessage from '../common/ErrorMessage';
import CreateAccountModal from './CreateAccountModal';

/**
 * Liste aller Konten
 */
export default function AccountList() {
  const { accounts, loading, error, fetchAccounts, createAccount, clearError } = useAccountStore();
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const handleCreateAccount = async (accountData) => {
    await createAccount(accountData);
  };

  if (loading && accounts.length === 0) {
    return <LoadingSpinner size="lg" text="Lade Konten..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neutral-900">Meine Konten</h1>
          <p className="text-sm text-neutral-600 mt-1">
            {accounts.length === 0 
              ? 'Erstellen Sie Ihr erstes Konto, um zu beginnen'
              : `${accounts.length} ${accounts.length === 1 ? 'Konto' : 'Konten'} verwaltet`
            }
          </p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} title="Neues Konto hinzufügen" aria-label="Neues Konto hinzufügen">
          <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Neues Konto
        </Button>
      </div>

      {/* Error Message */}
      {error && (
        <ErrorMessage 
          message={error} 
          onDismiss={clearError}
        />
      )}

      {/* Accounts Grid or Empty State */}
      {accounts.length === 0 ? (
        <div className="bg-white rounded-xl border-2 border-dashed border-neutral-300 p-12">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center mb-4">
              <svg
                className="h-10 w-10 text-neutral-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-neutral-900 mb-2">Keine Konten vorhanden</h3>
            <p className="text-sm text-neutral-600 mb-6 max-w-md mx-auto">
              Erstellen Sie Ihr erstes Konto, um Ihre Finanzen zu verwalten und Transaktionen zu erfassen.
            </p>
            <Button onClick={() => setIsModalOpen(true)} size="lg">
              <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              Erstes Konto erstellen
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {accounts.map((account) => (
            <AccountCard key={account.id} account={account} />
          ))}
        </div>
      )}

      {/* Create Account Modal */}
      <CreateAccountModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreate={handleCreateAccount}
      />
    </div>
  );
}
