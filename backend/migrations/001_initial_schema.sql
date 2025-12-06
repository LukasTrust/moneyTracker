-- Migration: Initial Schema
-- Version: 001
-- Description: Creates base tables for accounts, categories, mappings, and recipients
-- Author: System
-- Date: 2025-12-06

-- =====================================================
-- ACCOUNTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    bank_name VARCHAR(100),
    account_number VARCHAR(50),
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    description TEXT,
    initial_balance DECIMAL(15, 2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_accounts_name ON accounts(name);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS accounts_updated_at 
AFTER UPDATE ON accounts 
FOR EACH ROW 
BEGIN
    UPDATE accounts SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- =====================================================
-- CATEGORIES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) NOT NULL DEFAULT '#3b82f6',
    icon VARCHAR(10),
    mappings TEXT NOT NULL DEFAULT '{"patterns":[]}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS categories_updated_at 
AFTER UPDATE ON categories 
FOR EACH ROW 
BEGIN
    UPDATE categories SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- =====================================================
-- MAPPINGS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    csv_header VARCHAR(100) NOT NULL,
    standard_field VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_mappings_account_id ON mappings(account_id);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS mappings_updated_at 
AFTER UPDATE ON mappings 
FOR EACH ROW 
BEGIN
    UPDATE mappings SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- =====================================================
-- RECIPIENTS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS recipients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(200) NOT NULL,
    normalized_name VARCHAR(200) NOT NULL UNIQUE,
    aliases VARCHAR(500),
    transaction_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_recipient_normalized ON recipients(normalized_name);
CREATE INDEX IF NOT EXISTS idx_recipient_name ON recipients(name);

-- Trigger to update updated_at timestamp
CREATE TRIGGER IF NOT EXISTS recipients_updated_at 
AFTER UPDATE ON recipients 
FOR EACH ROW 
BEGIN
    UPDATE recipients SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;
