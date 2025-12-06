-- Migration: Add Data Rows Table
-- Version: 002
-- Description: Creates data_rows table for transaction data
-- Author: System
-- Date: 2025-12-06

-- =====================================================
-- DATA_ROWS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS data_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    row_hash VARCHAR(64) NOT NULL UNIQUE,
    transaction_date DATE NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    recipient VARCHAR(200),
    purpose TEXT,
    valuta_date DATE,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    raw_data TEXT,
    category_id INTEGER,
    recipient_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    FOREIGN KEY (recipient_id) REFERENCES recipients(id) ON DELETE SET NULL
);

-- Core indexes
CREATE INDEX IF NOT EXISTS idx_data_rows_account_id ON data_rows(account_id);
CREATE INDEX IF NOT EXISTS idx_data_rows_row_hash ON data_rows(row_hash);
CREATE INDEX IF NOT EXISTS idx_data_rows_transaction_date ON data_rows(transaction_date);
CREATE INDEX IF NOT EXISTS idx_data_rows_category_id ON data_rows(category_id);
CREATE INDEX IF NOT EXISTS idx_data_rows_recipient_id ON data_rows(recipient_id);

-- Composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_account_date_range ON data_rows(account_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_category_date ON data_rows(category_id, transaction_date);
CREATE INDEX IF NOT EXISTS idx_account_category ON data_rows(account_id, category_id);
CREATE INDEX IF NOT EXISTS idx_recipient_search ON data_rows(recipient);
CREATE INDEX IF NOT EXISTS idx_date_amount ON data_rows(transaction_date, amount);
CREATE INDEX IF NOT EXISTS idx_created_at ON data_rows(created_at);
