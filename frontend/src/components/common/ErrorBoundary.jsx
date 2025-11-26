import React from 'react';
import { useUIStore } from '../../store';

/**
 * ErrorBoundary - Catches rendering errors in subtree and shows fallback UI.
 * Uses `useUIStore.getState().showError` to emit a toast when an error occurs.
 */
export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, info: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    // Log and surface a toast via uiStore without using hooks
    try {
      const msg = error?.message || 'Unbekannter Fehler';
      useUIStore.getState().showError(`Ein Fehler ist aufgetreten: ${msg}`);
    } catch (e) {
      // swallow
      // eslint-disable-next-line no-console
      console.error('ErrorBoundary: failed to show toast', e);
    }

    // Keep details in state for optional debug UI
    this.setState({ error, info });
    // Also keep console logging
    // eslint-disable-next-line no-console
    console.error('ErrorBoundary caught error:', error, info);
  }

  handleReload = () => {
    if (this.props.onReload) {
      this.props.onReload();
    } else {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
          <div className="max-w-md w-full bg-white border rounded-lg p-6 text-center shadow">
            <h2 className="text-xl font-bold text-gray-900 mb-2">Etwas ist schiefgelaufen</h2>
            <p className="text-sm text-gray-600 mb-4">Die Seite konnte nicht geladen werden. Versuchen Sie es erneut oder melden Sie das Problem.</p>
            <div className="flex items-center justify-center gap-3">
              <button onClick={this.handleReload} className="px-4 py-2 bg-primary-600 text-white rounded">Neu laden</button>
              <button onClick={() => useUIStore.getState().openModal && useUIStore.getState().openModal('reportError', { error: this.state.error, info: this.state.info })} className="px-4 py-2 border rounded">Fehler melden</button>
            </div>
            {this.props.showDetails && this.state.error && (
              <details className="text-left mt-4 text-xs text-gray-500">
                <summary>Fehlerdetails</summary>
                <pre className="whitespace-pre-wrap">{String(this.state.error)}{this.state.info ? '\n' + JSON.stringify(this.state.info, null, 2) : ''}</pre>
              </details>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
