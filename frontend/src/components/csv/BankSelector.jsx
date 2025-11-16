/**
 * Bank Selector Component
 * 
 * Allows users to select a predefined bank mapping or detect automatically
 */
import React, { useState, useEffect } from 'react';
import api from '../../services/api';

export default function BankSelector({ 
  csvFile, 
  onBankSelected, 
  onAutoDetect 
}) {
  const [banks, setBanks] = useState([]);
  const [selectedBank, setSelectedBank] = useState('');
  const [isDetecting, setIsDetecting] = useState(false);
  const [detectedBank, setDetectedBank] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load available banks on mount
  useEffect(() => {
    loadBanks();
  }, []);

  // Auto-detect when file is provided
  useEffect(() => {
    if (csvFile && onAutoDetect) {
      detectBankAutomatically();
    }
  }, [csvFile]);

  const loadBanks = async () => {
    setLoading(true);
    try {
      const response = await api.get('/csv-import/banks');
      setBanks(response.data.banks || []);
    } catch (error) {
      console.error('Error loading banks:', error);
    } finally {
      setLoading(false);
    }
  };

  const detectBankAutomatically = async () => {
    if (!csvFile) return;

    setIsDetecting(true);
    try {
      const formData = new FormData();
      formData.append('file', csvFile);

      const response = await api.post('/csv-import/detect-bank', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (response.data.detected) {
        setDetectedBank(response.data);
        setSelectedBank(response.data.bank_id);
        
        // Notify parent component
        if (onAutoDetect) {
          onAutoDetect(response.data);
        }
      } else {
        setDetectedBank(null);
      }
    } catch (error) {
      console.error('Error detecting bank:', error);
      setDetectedBank(null);
    } finally {
      setIsDetecting(false);
    }
  };

  const handleBankSelect = async (bankId) => {
    setSelectedBank(bankId);
    
    if (!bankId) {
      onBankSelected(null);
      return;
    }

    try {
      const response = await api.get(`/csv-import/banks/${bankId}/preset`);
      onBankSelected(response.data);
    } catch (error) {
      console.error('Error loading bank preset:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <div className="space-y-4">
        {/* Header */}
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            🏦 Bank auswählen
          </h3>
          <p className="text-sm text-gray-600 mt-1">
            Wählen Sie Ihre Bank für vorkonfigurierte Mappings
          </p>
        </div>

        {/* Auto-Detection Result */}
        {isDetecting && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <div className="animate-spin h-5 w-5 border-2 border-blue-600 border-t-transparent rounded-full"></div>
              <span className="text-sm text-blue-700">
                Erkenne Bank automatisch...
              </span>
            </div>
          </div>
        )}

        {detectedBank && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-green-900">
                  ✅ {detectedBank.bank_name} erkannt
                </p>
                <p className="text-xs text-green-700 mt-1">
                  {detectedBank.bank_description}
                </p>
              </div>
            </div>
          </div>
        )}

        {!isDetecting && !detectedBank && csvFile && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-center gap-3">
              <svg className="h-5 w-5 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <p className="text-sm font-medium text-yellow-900">
                  Bank nicht automatisch erkannt
                </p>
                <p className="text-xs text-yellow-700 mt-1">
                  Bitte wählen Sie Ihre Bank manuell aus der Liste
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Bank Dropdown */}
        <div>
          <label htmlFor="bank-select" className="block text-sm font-medium text-gray-700 mb-2">
            Bank wählen
          </label>
          <select
            id="bank-select"
            value={selectedBank}
            onChange={(e) => handleBankSelect(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            disabled={loading}
          >
            <option value="">-- Bitte wählen --</option>
            {banks.map((bank) => (
              <option key={bank.id} value={bank.id}>
                {bank.name}
              </option>
            ))}
            <option value="manual">🔧 Manuelles Mapping</option>
          </select>
          
          {selectedBank && selectedBank !== 'manual' && (
            <p className="text-xs text-gray-500 mt-2">
              {banks.find(b => b.id === selectedBank)?.description}
            </p>
          )}
        </div>

        {/* Manual Mapping Note */}
        {selectedBank === 'manual' && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <p className="text-sm text-gray-700">
              <strong>Manuelles Mapping:</strong> Sie können die CSV-Spalten manuell zuordnen.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
