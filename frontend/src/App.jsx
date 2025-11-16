import React, { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { LoadingSpinner } from './components/common';
import ToastContainer from './components/common/Toast';

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AccountDetailPage = lazy(() => import('./pages/AccountDetailPage'));
const NotFound = lazy(() => import('./pages/NotFound'));

/**
 * Main App Component with Routing and Performance Optimizations
 * 
 * FEATURES:
 * - Code Splitting via React.lazy
 * - Suspense with Loading States
 * - Global Toast Notifications
 * 
 * ERWEITERBARKEIT:
 * - Error Boundary
 * - Authentication
 * - Theme Provider (Dark Mode)
 * - i18n Provider
 */
function App() {
  return (
    <Router>
      {/* Global Toast Container */}
      <ToastContainer />

      {/* Routes with Suspense */}
      <Suspense fallback={<LoadingSpinner fullScreen text="Lädt..." />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/accounts/:id" element={<AccountDetailPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;

