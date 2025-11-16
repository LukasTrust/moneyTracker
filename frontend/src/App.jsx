import React, { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { LoadingSpinner } from './components/common';
import ToastContainer from './components/common/Toast';
import { useCategoryStore } from './store/categoryStore';

// Lazy load pages for code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AccountDetailPage = lazy(() => import('./pages/AccountDetailPage'));
const ComparisonPage = lazy(() => import('./pages/ComparisonPage'));
const TransferManagementPage = lazy(() => import('./components/transfers/TransferManagementPage'));
const NotFound = lazy(() => import('./pages/NotFound'));

/**
 * Main App Component with Routing and Performance Optimizations
 * 
 * FEATURES:
 * - Code Splitting via React.lazy
 * - Suspense with Loading States
 * - Global Toast Notifications
 * - Global Category Store Initialization
 * 
 * ERWEITERBARKEIT:
 * - Error Boundary
 * - Authentication
 * - Theme Provider (Dark Mode)
 * - i18n Provider
 */
function App() {
  const fetchCategories = useCategoryStore((state) => state.fetchCategories);

  // Initialize global data (categories) on app mount
  useEffect(() => {
    fetchCategories();
  }, [fetchCategories]);

  return (
    <Router>
      {/* Global Toast Container */}
      <ToastContainer />

      {/* Routes with Suspense */}
      <Suspense fallback={<LoadingSpinner fullScreen text="Lädt..." />}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/accounts/:id" element={<AccountDetailPage />} />
          <Route path="/accounts/:id/compare" element={<ComparisonPage />} />
          <Route path="/transfers" element={<TransferManagementPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </Router>
  );
}

export default App;

