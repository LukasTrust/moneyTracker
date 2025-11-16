-- Migration: Add Recurring Transactions (Contracts/Verträge)
-- Version: 005
-- Description: Creates recurring_transactions table for automatic detection of recurring payments
-- Author: System
-- Date: 2025-11-16

-- Create recurring_transactions table
CREATE TABLE IF NOT EXISTS recurring_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    recipient VARCHAR(200) NOT NULL,
    average_amount NUMERIC(12, 2) NOT NULL,
    average_interval_days INTEGER NOT NULL,
    first_occurrence DATE NOT NULL,
    last_occurrence DATE NOT NULL,
    occurrence_count INTEGER NOT NULL DEFAULT 0,
    category_id INTEGER,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    is_manually_overridden BOOLEAN NOT NULL DEFAULT 0,
    next_expected_date DATE,
    confidence_score NUMERIC(3, 2) DEFAULT 1.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    
    -- Constraints
    CHECK (average_amount != 0),
    CHECK (average_interval_days > 0),
    CHECK (occurrence_count >= 3),
    CHECK (last_occurrence >= first_occurrence),
    CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Create junction table for linking recurring transactions to actual data_rows
CREATE TABLE IF NOT EXISTS recurring_transaction_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recurring_transaction_id INTEGER NOT NULL,
    data_row_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (recurring_transaction_id) REFERENCES recurring_transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (data_row_id) REFERENCES data_rows(id) ON DELETE CASCADE,
    
    -- Unique constraint: one data_row can only belong to one recurring transaction
    UNIQUE(data_row_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_recurring_account_id ON recurring_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_recurring_recipient ON recurring_transactions(recipient);
CREATE INDEX IF NOT EXISTS idx_recurring_category_id ON recurring_transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_recurring_is_active ON recurring_transactions(is_active);
CREATE INDEX IF NOT EXISTS idx_recurring_next_expected ON recurring_transactions(next_expected_date);
CREATE INDEX IF NOT EXISTS idx_recurring_last_occurrence ON recurring_transactions(last_occurrence);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_recurring_account_active ON recurring_transactions(account_id, is_active);
CREATE INDEX IF NOT EXISTS idx_recurring_account_category ON recurring_transactions(account_id, category_id);

-- Indexes for junction table
CREATE INDEX IF NOT EXISTS idx_recurring_links_recurring_id ON recurring_transaction_links(recurring_transaction_id);
CREATE INDEX IF NOT EXISTS idx_recurring_links_data_row_id ON recurring_transaction_links(data_row_id);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS recurring_transactions_updated_at 
AFTER UPDATE ON recurring_transactions
FOR EACH ROW
BEGIN
    UPDATE recurring_transactions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
