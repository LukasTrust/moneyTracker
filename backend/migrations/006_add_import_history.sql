-- Migration: Add Import History & Rollback
-- Version: 006
-- Description: Creates import_history table to track CSV imports and enable rollback functionality
-- Author: System
-- Date: 2025-11-16

-- Create import_history table
CREATE TABLE IF NOT EXISTS import_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    row_count INTEGER NOT NULL DEFAULT 0,
    rows_inserted INTEGER NOT NULL DEFAULT 0,
    rows_duplicated INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    
    -- Constraints
    CHECK (status IN ('success', 'partial', 'failed')),
    CHECK (row_count >= 0),
    CHECK (rows_inserted >= 0),
    CHECK (rows_duplicated >= 0)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_import_history_account_id ON import_history(account_id);
CREATE INDEX IF NOT EXISTS idx_import_history_uploaded_at ON import_history(uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_import_history_status ON import_history(status);

-- Add import_id column to data_rows table (nullable for existing rows)
ALTER TABLE data_rows ADD COLUMN import_id INTEGER REFERENCES import_history(id) ON DELETE SET NULL;

-- Create index for import_id lookups
CREATE INDEX IF NOT EXISTS idx_data_rows_import_id ON data_rows(import_id);

-- Populate existing data_rows with NULL import_id (they were imported before this feature)
-- No action needed, column is already nullable
