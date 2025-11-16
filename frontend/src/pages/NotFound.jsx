import React from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/common/Button';

/**
 * 404 Not Found Page
 */
export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-gray-300">404</h1>
        <h2 className="text-3xl font-bold text-gray-900 mt-4 mb-2">
          Seite nicht gefunden
        </h2>
        <p className="text-gray-600 mb-8">
          Die von Ihnen gesuchte Seite existiert nicht.
        </p>
        <Button onClick={() => navigate('/')}>
          Zurück zur Startseite
        </Button>
      </div>
    </div>
  );
}
