/**
 * CSV Import Wizard - Step-by-Step Import Process
 * 
 * STEPS:
 * 1. File Upload (Drag & Drop)
 * 2. Mapping Configuration & Preview
 * 3. Import Progress & Results
 */

import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import ImportProgress from './ImportProgress';
import { previewCsv, importCsv, validateSavedMapping } from '../../services/csvImportApi';
import mappingService from '../../services/mappingService';
import { useToast } from '../../hooks/useToast';

const STEPS = [
  { id: 1, title: 'Datei hochladen', icon: '📁' },
  { id: 2, title: 'Überprüfen', icon: '✓' },
  { id: 3, title: 'Importieren', icon: '⚡' },
];

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

export default function CsvImportWizard({ accountId, onImportSuccess }) {
  const [currentStep, setCurrentStep] = useState(1);
  const [file, setFile] = useState(null);
  const [csvPreview, setCsvPreview] = useState(null);
  const [mapping, setMapping] = useState({
    date: '',
    amount: '',
    recipient: '',
    purpose: '',
  });
  const [existingMapping, setExistingMapping] = useState(null);
  const [mappingEditable, setMappingEditable] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [importStage, setImportStage] = useState('uploading');
  const [importProgress, setImportProgress] = useState({ status: '', progress: 0, message: '' });

  const { showToast } = useToast();

  // Load existing mappings when component mounts
  useEffect(() => {
    if (accountId) {
      loadExistingMappings();
    }
  }, [accountId]);

  /**
   * Load existing mappings from backend
   */
  const loadExistingMappings = async () => {
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
        setExistingMapping(null);
        setMappingEditable(true);
      }
    } catch (error) {
      console.error('Error loading mappings:', error);
      setExistingMapping(null);
      setMappingEditable(true);
    }
  };

  // Drag & Drop Configuration
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    multiple: false,
    onDrop: async (acceptedFiles) => {
      const csvFile = acceptedFiles[0];
      if (!csvFile) return;

      setIsLoading(true);
      setFile(csvFile);
      
      try {
        // First, get CSV preview
        const preview = await previewCsv(csvFile);
        setCsvPreview(preview);
        
        // Then validate against saved mappings
        if (existingMapping) {
          try {
            const validation = await validateSavedMapping(accountId, csvFile);
            setValidationResult(validation);
            
            if (validation.is_valid) {
              // All headers match - use saved mapping
              setMappingEditable(false);
              showToast('✅ CSV erfolgreich geladen. Gespeichertes Mapping wird verwendet.', 'success');
            } else if (validation.has_saved_mapping) {
              // Some headers are missing - enable editing and show warnings
              setMappingEditable(true);
              
              // Apply suggestions where available
              const updatedMapping = { ...existingMapping };
              validation.validation_results.forEach(result => {
                if (!result.is_valid && result.suggested_header) {
                  updatedMapping[result.field] = result.suggested_header;
                }
              });
              setMapping(updatedMapping);
              
              showToast(
                `⚠️ ${validation.missing_headers.length} Spalte(n) nicht gefunden. Bitte Mapping überprüfen.`,
                'warning'
              );
            }
          } catch (error) {
            console.error('Validation error:', error);
            // Fallback to simple header check
            const existingHeaders = Object.values(existingMapping).filter(h => h);
            const headersMatch = existingHeaders.every(h => preview.headers.includes(h));
            
            if (!headersMatch) {
              setMappingEditable(true);
              showToast('⚠️ CSV-Struktur weicht vom gespeicherten Mapping ab.', 'warning');
            } else {
              setMappingEditable(false);
              showToast('✅ CSV erfolgreich geladen.', 'success');
            }
          }
        } else {
          // No existing mapping - enable manual editing
          setMappingEditable(true);
          showToast('✅ CSV erfolgreich geladen. Bitte ordnen Sie die Felder zu.', 'success');
        }
        
        setCurrentStep(2);
      } catch (error) {
        showToast(
          error.response?.data?.detail || 'Fehler beim Laden der CSV',
          'error'
        );
        setFile(null);
        setCsvPreview(null);
        setValidationResult(null);
      } finally {
        setIsLoading(false);
      }
    },
  });

  const handleMappingChange = (fieldName, csvHeader) => {
    if (!mappingEditable) return;
    
    setMapping((prev) => ({
      ...prev,
      [fieldName]: csvHeader,
    }));
  };

  const enableMappingEdit = () => {
    setMappingEditable(true);
  };

  const handleStartImport = async () => {
    if (!file || !mapping) return;

    // Validate mapping before starting import
    const missingFields = REQUIRED_FIELDS.filter(field => !mapping[field]);
    
    if (missingFields.length > 0) {
      showToast(
        `❌ Pflichtfelder fehlen: ${missingFields.join(', ')}`,
        'error'
      );
      return;
    }

    setIsLoading(true);
    setCurrentStep(3);

    try {
      // Use job-aware import with progress tracking
      setImportStage('uploading');
      
      const result = await importCsv(accountId, mapping, file, {
        waitForCompletion: true,
        onProgress: (progress) => {
          setImportProgress(progress);
          // Map job status to stages for UI
          if (progress.status === 'pending') setImportStage('uploading');
          else if (progress.status === 'running') {
            if (progress.progress < 30) setImportStage('parsing');
            else if (progress.progress < 60) setImportStage('validating');
            else setImportStage('importing');
          }
          else if (progress.status === 'completed') setImportStage('finishing');
        }
      });
      
      setImportStage('finishing');
      await new Promise(resolve => setTimeout(resolve, 300));
      
      setImportResult(result);
      
      // Show detailed success message
      if (result.imported_count > 0) {
        showToast(
          `✅ ${result.imported_count} Transaktionen erfolgreich importiert!`,
          'success'
        );
      }
      
      if (result.duplicate_count > 0) {
        showToast(
          `ℹ️ ${result.duplicate_count} Duplikate übersprungen`,
          'info'
        );
      }
      
      if (result.error_count > 0) {
        showToast(
          `⚠️ ${result.error_count} Zeilen mit Fehlern`,
          'warning'
        );
      }
      
      if (result.recurring_detected > 0) {
        showToast(
          `📋 ${result.recurring_detected} wiederkehrende Verträge erkannt`,
          'success'
        );
      }

      // Reload mappings (they were saved after import)
      await loadExistingMappings();
      
      // Notify parent component (without automatic redirect)
      if (onImportSuccess) {
        onImportSuccess();
      }
    } catch (error) {
      const errorDetail = error.response?.data?.detail || 'Unbekannter Fehler beim Import';
      showToast(
        `❌ Import fehlgeschlagen: ${errorDetail}`,
        'error'
      );
      setCurrentStep(2); // Go back to review
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setCurrentStep(1);
    setFile(null);
    setCsvPreview(null);
    setMapping(existingMapping || {
      date: '',
      amount: '',
      recipient: '',
      purpose: '',
    });
    setMappingEditable(!existingMapping);
    setValidationResult(null);
    setImportResult(null);
    setImportStage('uploading');
    setImportProgress({ status: '', progress: 0, message: '' });
  };

  return (
    <div className="space-y-6">
      {/* Progress Stepper */}
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        <div className="flex items-center justify-between">
          {STEPS.map((step, index) => (
            <React.Fragment key={step.id}>
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`
                    w-12 h-12 rounded-full flex items-center justify-center text-xl font-bold transition-all
                    ${currentStep >= step.id
                      ? 'bg-primary-600 text-white'
                      : 'bg-neutral-200 text-neutral-500'
                    }
                    ${currentStep === step.id ? 'ring-4 ring-primary-200' : ''}
                  `}
                >
                  {step.icon}
                </div>
                <span
                  className={`
                    mt-2 text-xs font-medium text-center
                    ${currentStep >= step.id ? 'text-neutral-900' : 'text-neutral-500'}
                  `}
                >
                  {step.title}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`
                    flex-1 h-1 mx-2 rounded transition-all
                    ${currentStep > step.id ? 'bg-primary-600' : 'bg-neutral-200'}
                  `}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-lg border border-neutral-200 p-6">
        {/* STEP 1: File Upload */}
        {currentStep === 1 && (
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-neutral-900">
              <span aria-hidden="true">📁</span> CSV-Datei hochladen
            </h2>
            <p className="text-neutral-600">
              Laden Sie Ihre Banktransaktionen als CSV-Datei hoch.
            </p>

            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all
                ${isDragActive
                  ? 'border-primary-600 bg-primary-50'
                  : 'border-neutral-300 hover:border-neutral-400 bg-neutral-50'
                }
              `}
            >
              <input {...getInputProps()} />
              <div className="text-6xl mb-4" aria-hidden="true">📄</div>
              {isDragActive ? (
                <p className="text-lg font-medium text-primary-600">
                  Datei hier ablegen...
                </p>
              ) : (
                <>
                  <p className="text-lg font-medium text-neutral-900 mb-2">
                    CSV-Datei hierher ziehen oder klicken
                  </p>
                  <p className="text-sm text-neutral-500">
                    Unterstützte Formate: .csv
                  </p>
                </>
              )}
            </div>

            {isLoading && (
              <div className="flex items-center justify-center gap-3 py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-2 border-primary-600 border-t-transparent" aria-hidden="true"></div>
                <span className="text-neutral-600">Analysiere CSV...</span>
              </div>
            )}
          </div>
        )}

        {/* STEP 2: Mapping Configuration & Preview */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-neutral-900">
                  ✓ Überprüfung & Mapping
                </h2>
                <p className="text-neutral-600 mt-1">
                  Prüfen Sie das Mapping und starten Sie den Import
                </p>
              </div>
              <button
                onClick={() => setCurrentStep(1)}
                className="text-sm text-neutral-500 hover:text-neutral-700"
                aria-label="Zurück zum Upload"
              >
                ← Zurück
              </button>
            </div>

            {csvPreview && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-sm text-green-800">
                  ✓ CSV geladen: <strong>{csvPreview.total_rows}</strong> Zeilen,{' '}
                  <strong>{csvPreview.headers.length}</strong> Spalten
                </p>
              </div>
            )}

            {/* Validation Warnings */}
            {validationResult && !validationResult.is_valid && validationResult.has_saved_mapping && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">⚠️</span>
                  <div className="flex-1">
                    <h3 className="font-semibold text-yellow-900 mb-2">
                      Gespeichertes Mapping nicht vollständig kompatibel
                    </h3>
                    <p className="text-sm text-yellow-800 mb-3">
                      Folgende Spalten wurden in der CSV nicht gefunden:
                    </p>
                    <ul className="text-sm text-yellow-800 list-disc list-inside space-y-1">
                      {validationResult.validation_results
                        .filter(r => !r.is_valid)
                        .map(result => (
                          <li key={result.field}>
                            <strong>{getFieldLabel(result.field)}</strong>: 
                            erwartet wurde "<em>{result.csv_header}</em>"
                            {result.suggested_header && (
                              <span className="text-yellow-700">
                                {' '}→ Vorschlag: "<em>{result.suggested_header}</em>"
                              </span>
                            )}
                          </li>
                        ))
                      }
                    </ul>
                    <p className="text-sm text-yellow-800 mt-3">
                      Bitte überprüfen Sie die Zuordnungen unten und passen Sie sie bei Bedarf an.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Mapping Configuration */}
            <div className="bg-white rounded-lg border border-neutral-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-neutral-900">
                  Felder zuordnen
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

              <div className="space-y-4">
                {REQUIRED_FIELDS.map((field) => {
                  // Check if this field has a validation issue
                  const fieldValidation = validationResult?.validation_results?.find(r => r.field === field);
                  const hasIssue = fieldValidation && !fieldValidation.is_valid;
                  const suggestedHeader = fieldValidation?.suggested_header;
                  
                  return (
                    <div 
                      key={field} 
                      className={`border rounded-lg p-4 ${hasIssue ? 'border-yellow-400 bg-yellow-50' : 'border-neutral-200'}`}
                    >
                      <label className="block text-sm font-medium text-neutral-900 mb-2">
                        <span className="mr-2">{getFieldIcon(field)}</span>
                        {getFieldLabel(field)}
                        <span className="text-red-500 ml-1">*</span>
                        {!mappingEditable && (
                          <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                        )}
                        {hasIssue && (
                          <span className="ml-2 text-xs text-yellow-700 font-semibold">⚠️ Spalte nicht gefunden</span>
                        )}
                      </label>
                      <select
                        value={mapping[field] || ''}
                        onChange={(e) => handleMappingChange(field, e.target.value)}
                        disabled={!mappingEditable}
                        className={`mt-1 block w-full rounded-lg shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed ${
                          hasIssue ? 'border-yellow-400' : 'border-neutral-300'
                        }`}
                      >
                        <option value="">-- Bitte wählen --</option>
                        {csvPreview?.headers.map((header) => (
                          <option key={header} value={header}>
                            {header}
                          </option>
                        ))}
                      </select>
                      {hasIssue && suggestedHeader && (
                        <p className="mt-2 text-xs text-yellow-700">
                          💡 Vorschlag: <strong>{suggestedHeader}</strong>
                        </p>
                      )}
                      <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
                    </div>
                  );
                })}

                {/* Optional Fields Section */}
                {OPTIONAL_FIELDS.map((field) => {
                  const fieldValidation = validationResult?.validation_results?.find(r => r.field === field);
                  const hasIssue = fieldValidation && !fieldValidation.is_valid;
                  const suggestedHeader = fieldValidation?.suggested_header;
                  
                  return (
                    <div 
                      key={field} 
                      className={`border rounded-lg p-4 ${hasIssue ? 'border-yellow-300 bg-yellow-50' : 'border-neutral-200 bg-neutral-50'}`}
                    >
                      <label className="block text-sm font-medium text-neutral-900 mb-2">
                        <span className="mr-2">{getFieldIcon(field)}</span>
                        {getFieldLabel(field)}
                        <span className="text-neutral-400 ml-1 text-xs">(optional)</span>
                        {!mappingEditable && (
                          <span className="ml-2 text-xs text-neutral-500">🔒 Gesperrt</span>
                        )}
                        {hasIssue && (
                          <span className="ml-2 text-xs text-yellow-600">⚠️ Spalte nicht gefunden</span>
                        )}
                      </label>
                      <select
                        value={mapping[field] || ''}
                        onChange={(e) => handleMappingChange(field, e.target.value)}
                        disabled={!mappingEditable}
                        className={`mt-1 block w-full rounded-lg shadow-sm focus:border-primary-500 focus:ring-primary-500 disabled:bg-neutral-100 disabled:cursor-not-allowed ${
                          hasIssue ? 'border-yellow-300' : 'border-neutral-300'
                        }`}
                      >
                        <option value="">-- Nicht zuordnen --</option>
                        {csvPreview?.headers.map((header) => (
                          <option key={header} value={header}>
                            {header}
                          </option>
                        ))}
                      </select>
                      {hasIssue && suggestedHeader && (
                        <p className="mt-2 text-xs text-yellow-600">
                          💡 Vorschlag: <strong>{suggestedHeader}</strong>
                        </p>
                      )}
                      <p className="mt-1 text-xs text-neutral-500">{FIELD_CONFIG[field]?.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Validation Alert */}
            {(() => {
              const missingFields = REQUIRED_FIELDS.filter(field => !mapping[field]);
              const hasAllRequired = missingFields.length === 0;
              
              return (
                <>
                  {!hasAllRequired && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">⚠️</span>
                        <div>
                          <h3 className="font-semibold text-red-900 mb-1">
                            Pflichtfelder fehlen
                          </h3>
                          <p className="text-sm text-red-700">
                            Folgende Felder müssen gemappt werden: <strong>{missingFields.map(f => getFieldLabel(f)).join(', ')}</strong>
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                  {hasAllRequired && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">✅</span>
                        <div>
                          <h3 className="font-semibold text-green-900 mb-1">
                            Mapping vollständig
                          </h3>
                          <p className="text-sm text-green-700">
                            Alle Pflichtfelder sind korrekt zugeordnet
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </>
              );
            })()}

            {/* CSV Preview */}
            {csvPreview && csvPreview.sample_rows && (
              <div>
                <h3 className="text-sm font-semibold text-neutral-900 mb-2">
                  Vorschau (erste 5 Zeilen):
                </h3>
                <div className="overflow-x-auto border border-neutral-200 rounded-lg">
                  <table className="min-w-full divide-y divide-neutral-200">
                    <thead className="bg-neutral-50">
                      <tr>
                        {csvPreview.headers.slice(0, 6).map((header, idx) => (
                          <th
                            key={idx}
                            className="px-3 py-2 text-left text-xs font-medium text-neutral-700"
                          >
                            {header}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-neutral-200">
                      {csvPreview.sample_rows.slice(0, 5).map((row, idx) => (
                        <tr key={idx}>
                          {csvPreview.headers.slice(0, 6).map((header, cellIdx) => (
                            <td
                              key={cellIdx}
                              className="px-3 py-2 text-sm text-neutral-900"
                            >
                              {row.data?.[header] || '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleStartImport}
                disabled={!REQUIRED_FIELDS.every(field => mapping[field])}
                className={`
                  flex-1 px-6 py-3 rounded-lg font-semibold transition-colors
                  ${!REQUIRED_FIELDS.every(field => mapping[field])
                    ? 'bg-neutral-300 text-neutral-500 cursor-not-allowed'
                    : 'bg-primary-600 text-white hover:bg-primary-700'
                  }
                `}
              >
                ⚡ Import starten
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: Import Progress & Results */}
        {currentStep === 3 && (
          <div className="space-y-6 text-center">
            {isLoading ? (
              <>
                <ImportProgress 
                  estimatedRows={csvPreview?.total_rows || 0}
                  stage={importStage}
                />
                {importProgress.progress > 0 && (
                  <div className="mt-4 max-w-md mx-auto">
                    <div className="flex justify-between text-sm text-neutral-600 mb-2">
                      <span>{importProgress.message || importProgress.status}</span>
                      <span>{Math.round(importProgress.progress)}%</span>
                    </div>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${importProgress.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </>
            ) : importResult ? (
              <>
                <div className="text-6xl mb-4">✅</div>
                <h2 className="text-2xl font-bold text-green-600">
                  Import erfolgreich!
                </h2>
                
                {/* Recurring Transactions Info */}
                {importResult.recurring_detected !== undefined && importResult.recurring_detected !== null && (
                  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg max-w-md mx-auto">
                    <p className="text-sm text-blue-800">
                      <span className="font-semibold">📋 {importResult.recurring_detected}</span> Verträge gefunden
                    </p>
                  </div>
                )}
                
                <div className="grid grid-cols-3 gap-4 max-w-2xl mx-auto">
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <p className="text-3xl font-bold text-green-600">
                      {importResult.imported_count}
                    </p>
                    <p className="text-sm text-green-700 mt-1">Importiert</p>
                  </div>
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p className="text-3xl font-bold text-yellow-600">
                      {importResult.duplicate_count}
                    </p>
                    <p className="text-sm text-yellow-700 mt-1">Duplikate</p>
                  </div>
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p className="text-3xl font-bold text-red-600">
                      {importResult.error_count}
                    </p>
                    <p className="text-sm text-red-700 mt-1">Fehler</p>
                  </div>
                </div>
                <button
                  onClick={handleReset}
                  className="mt-6 bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700"
                >
                  Weiteren Import starten
                </button>
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
}
