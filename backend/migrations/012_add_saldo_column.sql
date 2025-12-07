-- Migration: Add Saldo Column to Data Rows
-- Version: 012
-- Description: Adds saldo (balance) column to data_rows table for storing the account balance at transaction time
-- Author: System
-- Date: 2025-12-07

-- =====================================================
-- ADD SALDO COLUMN TO DATA_ROWS
-- =====================================================
-- Add saldo column to store the account balance at the time of each transaction
ALTER TABLE data_rows ADD COLUMN saldo DECIMAL(15, 2);

-- Create index for saldo queries (optional, for performance)
CREATE INDEX IF NOT EXISTS idx_data_rows_saldo ON data_rows(saldo);

-- Note: Existing rows will have NULL saldo values
-- The saldo will be populated during CSV import for new transactions
