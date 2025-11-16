-- Migration: Add Transfers for Inter-Account Transactions
-- Version: 007
-- Description: Creates transfers table to link transactions between accounts and exclude them from statistics
-- Author: System
-- Date: 2025-11-16

-- Create transfers table
CREATE TABLE IF NOT EXISTS transfers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign keys to data_rows (the two transactions that form a transfer)
    from_transaction_id INTEGER NOT NULL,
    to_transaction_id INTEGER NOT NULL,
    
    -- Transfer metadata
    amount DECIMAL(12, 2) NOT NULL,
    transfer_date DATE NOT NULL,
    notes TEXT,
    
    -- Detection metadata
    is_auto_detected BOOLEAN NOT NULL DEFAULT 0,
    confidence_score DECIMAL(3, 2),  -- 0.00 to 1.00 for auto-detection confidence
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (from_transaction_id) REFERENCES data_rows(id) ON DELETE CASCADE,
    FOREIGN KEY (to_transaction_id) REFERENCES data_rows(id) ON DELETE CASCADE,
    
    -- Constraints
    CHECK (from_transaction_id != to_transaction_id),  -- Can't transfer to self
    CHECK (amount != 0),  -- Amount must be non-zero
    CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1))
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_transfers_from_transaction ON transfers(from_transaction_id);
CREATE INDEX IF NOT EXISTS idx_transfers_to_transaction ON transfers(to_transaction_id);
CREATE INDEX IF NOT EXISTS idx_transfers_date ON transfers(transfer_date);
CREATE INDEX IF NOT EXISTS idx_transfers_auto_detected ON transfers(is_auto_detected);

-- Create unique constraint to prevent duplicate transfer links
CREATE UNIQUE INDEX IF NOT EXISTS idx_transfers_unique_pair ON transfers(
    MIN(from_transaction_id, to_transaction_id),
    MAX(from_transaction_id, to_transaction_id)
);

-- Create "Transfer" category if it doesn't exist
INSERT OR IGNORE INTO categories (name, color, icon, mappings)
VALUES (
    'Transfer',
    '#6b7280',  -- Gray color to indicate neutral/internal transaction
    '🔄',
    '{"patterns": []}'  -- No automatic patterns - transfers are detected differently
);
