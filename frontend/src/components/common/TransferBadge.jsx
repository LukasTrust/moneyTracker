import React from 'react';

/**
 * TransferBadge Component
 * 
 * Displays a badge indicating that a transaction is part of an inter-account transfer.
 * Shows direction (incoming/outgoing) and linked account information.
 * 
 * @param {Object} props
 * @param {Object} props.transfer - Transfer object with details
 * @param {number} props.currentTransactionId - ID of the current transaction
 * @param {string} props.size - Badge size: 'sm' | 'md' | 'lg'
 * @param {boolean} props.showDetails - Show detailed information
 */
export default function TransferBadge({ 
  transfer, 
  currentTransactionId,
  size = 'sm',
  showDetails = false 
}) {
  if (!transfer) return null;

  // Determine direction from current transaction's perspective
  const isOutgoing = transfer.from_transaction_id === currentTransactionId;
  const direction = isOutgoing ? 'outgoing' : 'incoming';
  
  // Get linked account name (may be undefined)
  const linkedAccountName = isOutgoing
    ? transfer.to_account_name
    : transfer.from_account_name;

  // Size classes
  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-sm px-2.5 py-1',
    lg: 'text-base px-3 py-1.5'
  };

  // Direction-specific styling
  const directionStyle = isOutgoing
    ? 'bg-orange-50 text-orange-700 border border-orange-200'
    : 'bg-blue-50 text-blue-700 border border-blue-200';

  return (
    <div className="inline-flex items-center gap-1.5">
      <span
        className={`
          inline-flex items-center gap-1 rounded-full font-medium
          ${sizeClasses[size]}
          ${directionStyle}
        `}
        title={`Transfer ${direction === 'outgoing' ? 'zu' : 'von'} ${linkedAccountName || 'anderem Konto'}`}
      >
        {/* Icon based on direction */}
        <span className="text-base">
          {direction === 'outgoing' ? '→' : '←'}
        </span>
        
        <span>Transfer</span>
        
        {/* Auto-detected indicator */}
        {transfer.is_auto_detected && (
          <span 
            className="ml-0.5 text-gray-400"
            title={`Automatisch erkannt (${Math.round(transfer.confidence_score * 100)}% Sicherheit)`}
          >
            🔄
          </span>
        )}
      </span>

      {/* Details (linked account) */}
      {showDetails && linkedAccountName && (
        <span className="text-xs text-gray-500">
          {direction === 'outgoing' ? '→' : '←'} {linkedAccountName}
        </span>
      )}
    </div>
  );
}

/**
 * TransferIndicator Component
 * 
 * Simpler icon-only indicator for compact displays (e.g., in tables)
 */
export function TransferIndicator({ 
  transfer, 
  currentTransactionId,
  size = 16 
}) {
  if (!transfer) return null;

  const isOutgoing = transfer.from_transaction_id === currentTransactionId;

  const linkedAccountName = isOutgoing ? transfer.to_account_name : transfer.from_account_name;

  return (
    <div 
      className={`
        inline-flex items-center justify-center rounded-full
        ${isOutgoing ? 'bg-orange-100 text-orange-600' : 'bg-blue-100 text-blue-600'}
      `}
      style={{ width: size + 8, height: size + 8, fontSize: size }}
      title={linkedAccountName ? `Transfer ${isOutgoing ? 'zu' : 'von'} ${linkedAccountName}` : `Transfer ${isOutgoing ? 'zu' : 'von'} anderem Konto`}
    >
      🔄
    </div>
  );
}
