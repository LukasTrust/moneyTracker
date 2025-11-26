import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../common/Button';
import Input from '../common/Input';
import Card from '../common/Card';
import Modal from '../common/Modal';
import accountService from '../../services/accountService';
import useAccountStore from '../../store/accountStore';

/**
 * AccountSettings - Komponente für Account-Verwaltung
 * 
 * FEATURES:
 * - Account umbenennen mit optimistischem Update
 * - Account löschen mit Confirmation Dialog
 * - Account-Info anzeigen (Erstellt am, etc.)
 * - Loading States
 * 
 * ERWEITERBARKEIT:
 * - Account-Berechtigungen (Teilen mit anderen Usern)
 * - Account-Archivierung (statt Löschen)
 * - Export aller Transaktionen als CSV/PDF
 * - Account-Farbe/Icon für bessere Unterscheidung
 * - Account-Beschreibung/Notizen
 * - Standard-Währung pro Account
 * 
 * @param {Object} props
 * @param {Object} props.account - Account-Objekt
 */
function AccountSettings({ account }) {
  const navigate = useNavigate();
  const { updateAccount, deleteAccount } = useAccountStore();
  
  const [isEditing, setIsEditing] = useState(false);
  const [newName, setNewName] = useState(account?.name || '');
  const [isEditingBalance, setIsEditingBalance] = useState(false);
  const [newBalance, setNewBalance] = useState(account?.initial_balance?.toString() || '0.00');
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [confirmName, setConfirmName] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isSavingBalance, setIsSavingBalance] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Umbenennen des Accounts
   * Mit optimistischem Update für schnelle UI-Reaktion
   */
  const handleRename = useCallback(async () => {
    if (!newName.trim()) {
      setError('Name darf nicht leer sein');
      return;
    }

    if (newName === account.name) {
      setIsEditing(false);
      return;
    }

    setIsSaving(true);
    setError(null);

    // Store alten Namen für Rollback
    const oldName = account.name;

    try {
      // Optimistisches Update: UI sofort ändern
      updateAccount(account.id, { name: newName.trim() }, true);
      
      // API-Call im Hintergrund
      await accountService.updateAccount(account.id, { name: newName.trim() });
      
      setIsEditing(false);
    } catch (err) {
      console.error('Error renaming account:', err);
      setError(err.response?.data?.message || 'Fehler beim Umbenennen');
      
      // Rollback bei Fehler
      updateAccount(account.id, { name: oldName }, true);
    } finally {
      setIsSaving(false);
    }
  }, [account, newName, updateAccount]);

  /**
   * Löschen des Accounts
   * Mit Bestätigungs-Dialog und Navigation zurück zur Übersicht
   */
  const handleDelete = useCallback(async () => {
    setIsDeleting(true);
    setError(null);

    try {
      // Use the store action which performs the API call and updates local state
      await deleteAccount(account.id);

      // Navigate zurück zum Dashboard
      navigate('/', { replace: true });
    } catch (err) {
      console.error('Error deleting account:', err);
      setError(err.response?.data?.message || 'Fehler beim Löschen');
      setShowDeleteModal(false);
    } finally {
      setIsDeleting(false);
      setConfirmName('');
    }
  }, [account, deleteAccount, navigate]);

  /**
   * Abbrechen der Bearbeitung
   */
  const handleCancel = useCallback(() => {
    setNewName(account.name);
    setIsEditing(false);
    setError(null);
  }, [account]);

  /**
   * Bearbeiten des Startguthabens
   * Mit optimistischem Update für schnelle UI-Reaktion
   */
  const handleBalanceUpdate = useCallback(async () => {
    const balanceValue = parseFloat(newBalance);
    
    if (isNaN(balanceValue)) {
      setError('Ungültiger Betrag');
      return;
    }

    if (balanceValue === parseFloat(account.initial_balance)) {
      setIsEditingBalance(false);
      return;
    }

    setIsSavingBalance(true);
    setError(null);

    // Store alten Wert für Rollback
    const oldBalance = account.initial_balance;

    try {
      // Optimistisches Update: UI sofort ändern
      updateAccount(account.id, { initial_balance: balanceValue }, true);
      
      // API-Call im Hintergrund
      await accountService.updateAccount(account.id, { initial_balance: balanceValue });
      
      setIsEditingBalance(false);
    } catch (err) {
      console.error('Error updating initial balance:', err);
      setError(err.response?.data?.message || 'Fehler beim Aktualisieren des Startguthabens');
      
      // Rollback bei Fehler
      updateAccount(account.id, { initial_balance: oldBalance }, true);
    } finally {
      setIsSavingBalance(false);
    }
  }, [account, newBalance, updateAccount]);

  /**
   * Abbrechen der Balance-Bearbeitung
   */
  const handleBalanceCancel = useCallback(() => {
    setNewBalance(account.initial_balance?.toString() || '0.00');
    setIsEditingBalance(false);
    setError(null);
  }, [account]);

  if (!account) {
    return (
      <Card>
        <div className="text-center py-8 text-gray-500">
          Account nicht gefunden
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900">Account-Einstellungen</h2>
        <p className="text-sm text-gray-600 mt-1">
          Verwalten Sie Ihren Account: Umbenennen oder Löschen
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex gap-3">
            <svg className="h-5 w-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-sm text-red-800">{error}</p>
          </div>
        </div>
      )}

      {/* Account Info */}
      <Card>
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Account-Informationen</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account-ID
              </label>
              <p className="text-sm text-gray-900 font-mono bg-gray-50 px-3 py-2 rounded">
                #{account.id}
              </p>
            </div>

            {/* Währung */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Währung
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded">
                {account.currency}
              </p>
            </div>

            {/* Startguthaben */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Startguthaben
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded">
                {parseFloat(account.initial_balance || 0).toLocaleString('de-DE', {
                  style: 'currency',
                  currency: account.currency || 'EUR'
                })}
              </p>
            </div>

            {/* Erstellt am */}
            {account.created_at && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Erstellt am
                </label>
                <p className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded">
                  {new Date(account.created_at).toLocaleDateString('de-DE', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
            )}

            {/* Letzte Änderung */}
            {account.updated_at && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Zuletzt geändert
                </label>
                <p className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded">
                  {new Date(account.updated_at).toLocaleDateString('de-DE', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
            )}
          </div>

          {/* Beschreibung */}
          {account.description && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Beschreibung
              </label>
              <p className="text-sm text-gray-900 bg-gray-50 px-3 py-2 rounded">
                {account.description}
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Rename Account */}
      <Card>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Account umbenennen</h3>
            <p className="text-sm text-gray-600 mt-1">
              Ändern Sie den Namen dieses Accounts
            </p>
          </div>

          {isEditing ? (
            <div className="space-y-4">
              <Input
                label="Neuer Name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="z.B. Girokonto, Sparkonto"
                autoFocus
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleRename();
                  }
                }}
              />
              <div className="flex gap-3">
                <Button
                  onClick={handleRename}
                  disabled={isSaving || !newName.trim()}
                >
                  {isSaving ? 'Speichert...' : 'Speichern'}
                </Button>
                <Button
                  variant="ghost"
                  onClick={handleCancel}
                  disabled={isSaving}
                >
                  Abbrechen
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Aktueller Name:</p>
                <p className="text-lg font-semibold text-gray-900">{account.name}</p>
              </div>
              <Button onClick={() => setIsEditing(true)}>
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Umbenennen
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Edit Initial Balance */}
      <Card>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Startguthaben bearbeiten</h3>
            <p className="text-sm text-gray-600 mt-1">
              Ändern Sie das Startguthaben für dieses Konto. Dies beeinflusst alle Berechnungen.
            </p>
          </div>

          {isEditingBalance ? (
            <div className="space-y-4">
              <Input
                label="Neues Startguthaben"
                type="number"
                step="0.01"
                value={newBalance}
                onChange={(e) => setNewBalance(e.target.value)}
                placeholder="0.00"
                autoFocus
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleBalanceUpdate();
                  }
                }}
                helperText="Geben Sie den tatsächlichen Kontostand zum Startzeitpunkt ein"
              />
              <div className="flex gap-3">
                <Button
                  onClick={handleBalanceUpdate}
                  disabled={isSavingBalance}
                >
                  {isSavingBalance ? 'Speichert...' : 'Speichern'}
                </Button>
                <Button
                  variant="ghost"
                  onClick={handleBalanceCancel}
                  disabled={isSavingBalance}
                >
                  Abbrechen
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Aktuelles Startguthaben:</p>
                <p className="text-lg font-semibold text-gray-900">
                  {parseFloat(account.initial_balance || 0).toLocaleString('de-DE', {
                    style: 'currency',
                    currency: account.currency || 'EUR'
                  })}
                </p>
              </div>
              <Button onClick={() => setIsEditingBalance(true)}>
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                Bearbeiten
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Delete Account */}
      <Card>
        <div className="space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-red-900">Danger Zone</h3>
            <p className="text-sm text-gray-600 mt-1">
              Irreversible Aktionen - Vorsicht geboten!
            </p>
          </div>

          <div className="border border-red-200 rounded-lg p-4 bg-red-50">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900">Account löschen</h4>
                <p className="text-sm text-gray-600 mt-1">
                  Löscht diesen Account unwiderruflich. Alle zugehörigen Transaktionen,
                  Mappings und hochgeladenen Daten werden ebenfalls gelöscht.
                </p>
                <p className="text-sm text-red-600 font-medium mt-2">
                  ⚠️ Diese Aktion kann nicht rückgängig gemacht werden!
                </p>
              </div>
              <Button
                variant="danger"
                onClick={() => setShowDeleteModal(true)}
                className="ml-4"
              >
                <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Account löschen
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => !isDeleting && setShowDeleteModal(false)}
        title="Account wirklich löschen?"
      >
        <div className="space-y-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex gap-3">
              <svg className="h-6 w-6 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div>
                <h4 className="font-semibold text-red-900 mb-2">
                  Sie sind dabei, den Account "{account.name}" zu löschen
                </h4>
                <p className="text-sm text-red-800">
                  Dies wird folgende Daten unwiderruflich löschen:
                </p>
                <ul className="mt-2 text-sm text-red-800 list-disc list-inside space-y-1">
                  <li>Alle Transaktionen dieses Accounts</li>
                  <li>Alle CSV-Uploads und Mappings</li>
                  <li>Alle Visualisierungen und Statistiken</li>
                </ul>
                <p className="mt-3 text-sm text-red-900 font-semibold">
                  Diese Aktion kann nicht rückgängig gemacht werden!
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-sm text-gray-700">
              Bitte geben Sie zur Bestätigung den Account-Namen ein:
            </p>
            <p className="text-sm font-semibold text-gray-900 mt-1">
              Geben Sie den Namen exakt ein, um die Löschung zu bestätigen.
            </p>
            <input
              type="text"
              value={confirmName}
              onChange={(e) => setConfirmName(e.target.value)}
              placeholder="Account-Name eingeben"
              className="mt-2 w-full px-3 py-2 border rounded focus:outline-none"
            />
            <p className="text-sm font-mono text-gray-700 mt-2 bg-white px-2 py-1 rounded">
              Zu löschender Account: <span className="font-semibold">{account.name}</span>
            </p>
          </div>

          <div className="flex gap-3 pt-4">
            <Button
              variant="danger"
              onClick={handleDelete}
              disabled={isDeleting || confirmName !== account.name}
              className="flex-1"
            >
              {isDeleting ? (
                <>
                  <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Wird gelöscht...
                </>
              ) : (
                <>
                  <svg className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Ja, unwiderruflich löschen
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              onClick={() => setShowDeleteModal(false)}
              disabled={isDeleting}
              className="flex-1"
            >
              Abbrechen
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

export default AccountSettings;
