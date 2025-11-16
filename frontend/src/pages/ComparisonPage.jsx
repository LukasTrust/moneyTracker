import React from 'react';
import { useParams } from 'react-router-dom';
import ComparisonView from '../components/comparison/ComparisonView';

/**
 * Comparison Page
 * Full-page wrapper for comparison view
 */
export default function ComparisonPage() {
  const { id } = useParams();
  
  return <ComparisonView accountId={id} />;
}
