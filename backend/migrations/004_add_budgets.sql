-- Migration: Add Budgets Table
-- Version: 004
-- Description: Creates budgets table for category-based budget management
-- Author: System
-- Date: 2025-11-16

-- Create budgets table
CREATE TABLE IF NOT EXISTS budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    period VARCHAR(20) NOT NULL DEFAULT 'monthly',
    amount NUMERIC(12, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    description VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Foreign key constraint
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    
    -- Constraints
    CHECK (amount > 0),
    CHECK (end_date >= start_date),
    CHECK (period IN ('monthly', 'yearly', 'quarterly', 'custom'))
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_budgets_category_id ON budgets(category_id);
CREATE INDEX IF NOT EXISTS idx_budgets_start_date ON budgets(start_date);
CREATE INDEX IF NOT EXISTS idx_budgets_end_date ON budgets(end_date);
CREATE INDEX IF NOT EXISTS idx_budgets_period ON budgets(period);

-- Composite index for date range queries
CREATE INDEX IF NOT EXISTS idx_budgets_date_range ON budgets(start_date, end_date);

-- Composite index for active budget lookups (category + date range)
CREATE INDEX IF NOT EXISTS idx_budgets_category_dates ON budgets(category_id, start_date, end_date);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS budgets_updated_at 
AFTER UPDATE ON budgets
FOR EACH ROW
BEGIN
    UPDATE budgets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
