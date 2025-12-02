/**
 * CSV Import & Mapping Component (3+1 Fields)
 * 
 * FEATURES:
 * - 3 Pflichtfelder: Datum, Betrag, Empfänger/Absender
 * - 1 Optionales Feld: Verwendungszweck (purpose)
 * - CSV-Upload mit Preview
 * - Automatische Mapping-Erkennung wenn vorhanden
 * - Manuelles Mapping wenn kein gespeichertes Mapping vorhanden
 * - Read-Only Ansicht des gespeicherten Mappings (mit Bearbeitungsmöglichkeit)
 * - "Mapping ändern" Button bei CSV-Upload mit gespeichertem Mapping
 * - CSV-Header-Validierung
 * - Kategorie-Zuordnung via CategoryMatcher (Backend)
 */

import React, { useState, useEffect } from 'react';
import { previewCsv, suggestMapping, importCsv } from '../../services/csvImportApi';
import mappingService from '../../services/mappingService';
import { useToast } from '../../hooks/useToast';

const REQUIRED_FIELDS = ['date', 'amount', 'recipient'];
const OPTIONAL_FIELDS = ['purpose'];
const ALL_FIELDS = [...REQUIRED_FIELDS, ...OPTIONAL_FIELDS];

// Field configuration
const FIELD_CONFIG = {
  date: { label: 'Datum', icon: '📅', description: 'Transaktionsdatum' },
  amount: { label: 'Betrag', icon: '💰', description: 'Transaktionsbetrag' },
  recipient: { label: 'Empfänger/Absender', icon: '👤', description: 'Gegenpartei der Transaktion' },
  purpose: { label: 'Verwendungszweck', icon: '📝', description: 'Beschreibung/Buchungstext (optional)' },
};

const getFieldLabel = (field) => FIELD_CONFIG[field]?.label || field;
const getFieldIcon = (field) => FIELD_CONFIG[field]?.icon || '📄';

export default function CsvImportMapping({ accountId, onImportSuccess }) {
  // State management
  const [file, setFile] = useState(null);
  const [csvHeaders, setCsvHeaders] = useState([]);
  const [previewData, setPreviewData] = useState(null);
  const [mapping, setMapping] = useState({
    date: '',
    amount: '',
    recipient: '',
    purpose: '',
  });
  const [existingMapping, setExistingMapping] = useState(null);
  const [mappingEditable, setMappingEditable] = useState(false);
  const [csvHeadersMismatch, setCsvHeadersMismatch] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingMappings, setIsLoadingMappings] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);

  const { showToast } = useToast();

  // Load existing mappings when account changes
  useEffect(() => {
    if (accountId) {
      loadExistingMappings();
    }
  }, [accountId]);

  /**
   * Load existing mappings from backend
   */
  const loadExistingMappings = async () => {
    setIsLoadingMappings(true);
    try {
      const mappings = await mappingService.getMappings(accountId);
      
      if (mappings && mappings.length > 0) {
        // Convert array to object
        const mappingObj = {};
        mappings.forEach((m) => {
          mappingObj[m.standard_field] = m.csv_header;
        });
        
        setExistingMapping(mappingObj);
        setMapping(mappingObj);
        setMappingEditable(false);
      } else {
        // No mapping exists, allow editing
        setExistingMapping(null);
        setMappingEditable(true);
      }
    } catch (error) {
      console.error('Error loading mappings:', error);
      setExistingMapping(null);
      setMappingEditable(true);
    } finally {
      setIsLoadingMappings(false);
    }
  };

  /**
   * Handle file selection and preview
   */
  const handleFileChange = async (event) => {
    const selectedFile = event.target.files?.[0];
    if (!selectedFile) return;

    setIsLoading(true);
    setFile(selectedFile);

    try {
      // Get preview
      const preview = await previewCsv(selectedFile);
      setPreviewData(preview);
      setCsvHeaders(preview.headers);

      // Check if existing mapping exists and if headers match
      if (existingMapping) {
        const existingHeaders = Object.values(existingMapping).filter(h => h);
        const headersMatch = existingHeaders.every(h => preview.headers.includes(h));
        
        if (!headersMatch) {
          // Headers don't match - allow manual editing
          setCsvHeadersMismatch(true);
          setMappingEditable(true);
          showToast('⚠️ CSV-Struktur weicht vom gespeicherten Mapping ab. Bitte prüfen Sie die Zuordnungen.', 'warning');
        } else {
          // Headers match - keep read-only but user can unlock
          setCsvHeadersMismatch(false);
          setMappingEditable(false);
          showToast('✅ CSV erfolgreich geladen. Gespeichertes Mapping wird verwendet.', 'success');
        }
      } else {
        // No existing mapping - get intelligent suggestions
        setMappingEditable(true);
        try {
          const suggestions = await suggestMapping(selectedFile);
          
          // Auto-fill mapping with suggestions
          const suggestedMapping = {
            date: '',
            amount: '',
            recipient: '',
            purpose: '',
          };
          
          Object.entries(suggestions.suggestions).forEach(([field, suggestion]) => {
            if (suggestion.suggested_header && suggestion.confidence > 0.5) {
              suggestedMapping[field] = suggestion.suggested_header;
            }
          });
          
          setMapping(suggestedMapping);
          
          const autoMappedCount = Object.values(suggestedMapping).filter(v => v).length;
          if (autoMappedCount > 0) {
            showToast(
              `✅ CSV geladen. ${autoMappedCount} Felder automatisch zugeordnet.`,
              'success'
            );
          } else {
            showToast('✅ CSV erfolgreich geladen. Bitte ordnen Sie die Felder zu.', 'success');
          }
        } catch (error) {
          console.error('Error getting suggestions:', error);
          showToast('✅ CSV erfolgreich geladen. Bitte ordnen Sie die Felder zu.', 'success');
        }
      }
    } catch (error) {
      console.error('Error loading CSV:', error);
      showToast(
        error.response?.data?.detail || 'Fehler beim Laden der CSV-Datei',
        'error'
      );
      handleReset();
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * Handle mapping change for a field
   */
  const handleMappingChange = (fieldName, csvHeader) => {
    if (!mappingEditable) return;
    
    setMapping((prev) => ({
      ...prev,
      [fieldName]: csvHeader,
    }));

    setValidationErrors([]);
  };

  /**
   * Enable mapping editing
   */
  const enableMappingEdit = () => {
    setMappingEditable(true);
  };

  /**
   * Validate mapping before import
   */
  const validateCurrentMapping = () => {
    if (!file) {
      return { isValid: false, errors: ['Bitte wählen Sie zuerst eine CSV-Datei aus'] };
    }

    const errors = [];
    
    REQUIRED_FIELDS.forEach((field) => {
      if (!mapping[field]) {
        errors.push(`${getFieldLabel(field)} muss gemappt werden`);
      }
    });

    Object.entries(mapping).forEach(([field, header]) => {
      if (header && !csvHeaders.includes(header)) {
        errors.push(`Header "${header}" existiert nicht in der CSV-Datei`);
      }
    });

    setValidationErrors(errors);
    
    return { isValid: errors.length === 0, errors };
  };

  /**
   * Handle import
   */
  const handleImport = async () => {
    const validation = validateCurrentMapping();
    if (!validation.isValid) {
      showToast('Bitte beheben Sie die Fehler vor dem Import', 'error');
      return;
    }

    setIsImporting(true);

    try {
      const result = await importCsv(accountId, mapping, file);

      if (result.success) {
        showToast(
          `Erfolgreich ${result.imported_count} Transaktionen importiert`,
          'success'
        );

        if (result.duplicate_count > 0) {
          showToast(`${result.duplicate_count} Duplikate übersprungen`, 'info');
        }
        if (result.error_count > 0) {
          showToast(`${result.error_count} Zeilen mit Fehlern`, 'warning');
        }
        if (result.recurring_detected > 0) {
          showToast(
            `📋 ${result.recurring_detected} wiederkehrende Verträge erkannt`,
            'success'
          );
        }

        // Reload mappings (they were saved after import)
        await loadExistingMappings();

        // Reset file and notify parent
        handleReset();
        onImportSuccess?.();
      } else {
        throw new Error(result.message || 'Import fehlgeschlagen');
      }
    } catch (error) {
      console.error('Import error:', error);
      showToast(
        error.response?.data?.detail || 'Fehler beim Importieren',
        'error'
      );
    } finally {
      setIsImporting(false);
    }
  };

  /**
   * Reset component state
   */
  const handleReset = () => {
    setFile(null);
    setCsvHeaders([]);
    setPreviewData(null);
    setMapping({
      date: existingMapping?.date || '',
      amount: existingMapping?.amount || '',
      recipient: existingMapping?.recipient || '',
    });
    setValidationErrors([]);
    setCsvHeadersMismatch(false);
    
    const fileInput = document.getElementById('csv-file-input');
    if (fileInput) fileInput.value = '';
  };

  /**
   * Check if import button should be enabled
   */
  const canImport = () => {
    if (!file || isImporting) return false;
    return REQUIRED_FIELDS.every((field) => mapping[field]);
  };

  // Loading state
  if (isLoadingMappings) {
    return (
      <div className="flex items-center justify-center p-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto" aria-hidden="true"></div>
          <p className="mt-4 text-neutral-600">Lade Mapping-Konfiguration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-neutral-900">CSV Import & Mapping</h2>
        <p className="mt-2 text-neutral-600">
          Laden Sie eine CSV-Datei hoch und ordnen Sie die Spalten den entsprechenden Feldern zu.
        </p>
      </div>

      {/* Existing Mapping Info (if no file uploaded) */}
      {existingMapping && !file && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-2xl mr-3">ℹ️</span>
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-blue-900">Gespeichertes Mapping</h3>
                <button
                  onClick={enableMappingEdit}
                  className="px-3 py-1.5 text-xs font-medium text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100"
                >
                  ✏️ Bearbeiten
                </button>
              </div>
              <p className="mt-1 text-sm text-blue-700">
                Für dieses Konto ist bereits eine Mapping-Konfiguration gespeichert.
                Laden Sie eine CSV-Datei hoch, um den Import zu starten.
              </p>
              <div className="mt-3 space-y-1">
                {ALL_FIELDS.map((field) => {
                  const value = existingMapping[field];
                  if (!value && OPTIONAL_FIELDS.includes(field)) return null; // Skip empty optional fields
                  return (
                    <div key={field} className="text-xs text-blue-600">
                      <span className="font-medium">{getFieldLabel(field)}:</span> {value || '-'}
                      {OPTIONAL_FIELDS.includes(field) && <span className="text-blue-400 ml-1">(optional)</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No Mapping Info (if no file uploaded and no existing mapping) */}
      {!existingMapping && !file && (
        <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-4">
          <div className="flex items-start">
            <span className="text-2xl mr-3" aria-hidden="true">📋</span>
            <div>
              <h3 className="text-sm font-medium text-neutral-900">Kein Mapping vorhanden</h3>
              <p className="mt-1 text-sm text-neutral-600">
                Für dieses Konto wurde noch keine Mapping-Konfiguration gespeichert.
                Laden Sie eine CSV-Datei hoch, um ein neues Mapping zu erstellen.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Read-Only Mapping View (when no file but existing mapping) */}
      {existingMapping && !file && !mappingEditable && (
        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">Aktuelle Zuordnung</h3>
          
          <div className="space-y-4">
            {REQUIRED_FIELDS.map((field) => (
              <div key={field} className="border border-neutral-200 rounded-lg p-4 bg-neutral-50">
                <label className="block text-sm font-medium text-neutral-900 mb-2">
                  <span className="mr-2">{getFieldIcon(field)}</span>
                  {getFieldLabel(field)}
                  <span className="text-red-500 ml-1">*</span>
                  <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                </label>
                <div className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm bg-neutral-100 px-3 py-2 text-sm text-neutral-700">
                  {existingMapping[field] || '-'}
                </div>
                <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
              </div>
            ))}

            {/* Optional Fields Section */}
            {OPTIONAL_FIELDS.map((field) => {
              const value = existingMapping[field];
              if (!value) return null; // Skip if not mapped
              return (
                <div key={field} className="border border-neutral-200 rounded-lg p-4 bg-neutral-50">
                  <label className="block text-sm font-medium text-neutral-900 mb-2">
                    <span className="mr-2">{getFieldIcon(field)}</span>
                    {getFieldLabel(field)}
                    <span className="text-neutral-400 ml-1 text-xs">(optional)</span>
                    <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                  </label>
                  <div className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm bg-neutral-100 px-3 py-2 text-sm text-neutral-700">
                    {value}
                  </div>
                  <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
                </div>
              );
            })}
          </div>

          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-xs text-blue-700">
              💡 <strong>Tipp:</strong> Klicken Sie auf "Bearbeiten", um die Zuordnungen anzupassen, oder laden Sie eine CSV-Datei hoch, um mit dem Import zu beginnen.
            </p>
          </div>
        </div>
      )}

      {/* Editable Mapping View (when no file but editing mode) */}
      {existingMapping && !file && mappingEditable && (
        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-neutral-900">Zuordnung bearbeiten</h3>
            <button
              onClick={() => setMappingEditable(false)}
              className="px-3 py-1.5 text-sm font-medium text-neutral-700 bg-neutral-100 rounded-lg hover:bg-neutral-200"
            >
              ❌ Abbrechen
            </button>
          </div>

          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              ⚠️ <strong>Hinweis:</strong> Änderungen werden erst beim nächsten CSV-Import gespeichert.
            </p>
          </div>
          
          <div className="space-y-4">
            {REQUIRED_FIELDS.map((field) => (
              <div key={field} className="border border-neutral-200 rounded-lg p-4">
                <label className="block text-sm font-medium text-neutral-900 mb-2">
                  <span className="mr-2">{getFieldIcon(field)}</span>
                  {getFieldLabel(field)}
                  <span className="text-red-500 ml-1">*</span>
                </label>
                <input
                  type="text"
                  value={mapping[field]}
                  onChange={(e) => handleMappingChange(field, e.target.value)}
                  placeholder="CSV-Spaltenname"
                  className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
              </div>
            ))}

            {/* Optional Fields Section */}
            {OPTIONAL_FIELDS.map((field) => (
              <div key={field} className="border border-neutral-200 rounded-lg p-4 bg-neutral-50">
                <label className="block text-sm font-medium text-neutral-900 mb-2">
                  <span className="mr-2">{getFieldIcon(field)}</span>
                  {getFieldLabel(field)}
                  <span className="text-neutral-400 ml-1 text-xs">(optional)</span>
                </label>
                <input
                  type="text"
                  value={mapping[field]}
                  onChange={(e) => handleMappingChange(field, e.target.value)}
                  placeholder="CSV-Spaltenname (optional)"
                  className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* File Upload Section */}
      <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">1. CSV-Datei auswählen</h3>
        
        <div className="flex items-center gap-4">
          <input
            id="csv-file-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            disabled={isLoading}
            className="block w-full text-sm text-neutral-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-lg file:border-0
              file:text-sm file:font-semibold
              file:bg-primary-50 file:text-primary-700
              hover:file:bg-primary-100
              disabled:opacity-50 disabled:cursor-not-allowed"
          />
          
            {file && (
            <button
              onClick={handleReset}
              className="px-4 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
            >
              Zurücksetzen
            </button>
          )}
        </div>

        {file && previewData && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              ✓ CSV geladen: {previewData.total_rows} Zeilen, {previewData.headers.length} Spalten
            </p>
          </div>
        )}

        {isLoading && (
          <div className="mt-4 text-center text-neutral-600">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-sm">Analysiere CSV-Datei...</p>
          </div>
        )}
      </div>

      {/* Mapping Configuration */}
      {file && previewData && (
        <div className="bg-white rounded-lg shadow-sm border border-neutral-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-neutral-900">
              2. Felder zuordnen
            </h3>
            {existingMapping && !mappingEditable && (
              <button
                onClick={enableMappingEdit}
                className="px-3 py-1.5 text-sm font-medium text-primary-700 bg-primary-50 rounded-lg hover:bg-primary-100"
              >
                ✏️ Mapping ändern
              </button>
            )}
          </div>

          {csvHeadersMismatch && (
            <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800">
                ⚠️ Die CSV-Struktur passt nicht zum gespeicherten Mapping. Bitte überprüfen Sie die Zuordnungen.
              </p>
            </div>
          )}

            <div className="space-y-4">
            {REQUIRED_FIELDS.map((field) => (
              <div key={field} className="border border-neutral-200 rounded-lg p-4">
                <label className="block text-sm font-medium text-neutral-900 mb-2">
                  <span className="mr-2">{getFieldIcon(field)}</span>
                  {getFieldLabel(field)}
                  <span className="text-red-500 ml-1">*</span>
                  {!mappingEditable && (
                    <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                  )}
                </label>
                <select
                  value={mapping[field]}
                  onChange={(e) => handleMappingChange(field, e.target.value)}
                  disabled={!mappingEditable}
                  className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
                >
                  <option value="">-- Bitte wählen --</option>
                  {csvHeaders.map((header) => (
                    <option key={header} value={header}>
                      {header}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
                {validationErrors.includes(field) && (
                  <p className="mt-1 text-xs text-red-600">⚠️ Dieses Feld ist erforderlich</p>
                )}
              </div>
            ))}

            {/* Optional Fields Section */}
            {OPTIONAL_FIELDS.map((field) => (
              <div key={field} className="border border-neutral-200 rounded-lg p-4 bg-neutral-50">
                <label className="block text-sm font-medium text-neutral-900 mb-2">
                  <span className="mr-2">{getFieldIcon(field)}</span>
                  {getFieldLabel(field)}
                  <span className="text-neutral-400 ml-1 text-xs">(optional)</span>
                  {!mappingEditable && (
                    <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                  )}
                </label>
                <select
                  value={mapping[field]}
                  onChange={(e) => handleMappingChange(field, e.target.value)}
                  disabled={!mappingEditable}
                  className="mt-1 block w-full rounded-lg border-neutral-300 shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed"
                >
                  <option value="">-- Nicht zuordnen --</option>
                  {csvHeaders.map((header) => (
                    <option key={header} value={header}>
                      {header}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
              </div>
            ))}
          </div>

          {validationErrors.length > 0 && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <h4 className="text-sm font-medium text-red-900 mb-2">Validierungsfehler:</h4>
              <ul className="list-disc list-inside text-sm text-red-800 space-y-1">
                {validationErrors.map((error, idx) => (
                  <li key={idx}>{error}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Preview Section */}
      {file && previewData && previewData.sample_rows && (
        <div className="bg_white rounded-lg shadow-sm border border-neutral-200 p-6">
          <h3 className="text-lg font-semibold text-neutral-900 mb-4">3. Vorschau</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-neutral-200">
              <thead className="bg-neutral-50">
                <tr>
                  {previewData.headers.map((header, idx) => (
                    <th
                      key={idx}
                      className="px-4 py-3 text-left text-xs font-medium text-neutral-500 uppercase tracking-wider"
                    >
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-neutral-200">
                {previewData.sample_rows.slice(0, 5).map((row, rowIdx) => (
                  <tr key={rowIdx}>
                    {previewData.headers.map((header, colIdx) => (
                      <td
                        key={colIdx}
                        className="px-4 py-3 text-sm text-neutral-900 whitespace-nowrap"
                      >
                        {row.data?.[header] || '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-3 text-xs text-neutral-500">
            Zeige 5 von {previewData.total_rows} Zeilen
          </p>
        </div>
      )}

      {/* Action Buttons */}
      {file && (
        <div className="flex items-center justify-end gap-4">
          <button
            onClick={handleReset}
            className="px-6 py-2 text-sm font-medium text-neutral-700 bg-white border border-neutral-300 rounded-lg hover:bg-neutral-50"
          >
            Abbrechen
          </button>
          
          <button
            onClick={handleImport}
            disabled={!canImport()}
            className="px-6 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isImporting ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Importiere...</span>
              </>
            ) : (
              <>
                <span>🚀</span>
                <span>Import starten</span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
