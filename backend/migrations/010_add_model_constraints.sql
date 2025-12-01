-- Migration: Add check constraints to budgets and transfers
-- Audit reference: 04_backend_models.md - Add DB constraints
-- Date: 2025-12-01
-- Description: Adds validation constraints at database level

-- Add check constraints to budgets table
-- SQLite syntax (for reference - may need ALTER TABLE approach in some DBs)

-- For SQLite: Need to recreate table with constraints
-- Note: In production, use proper migration tool (Alembic) that handles this

-- Add constraint for budget amount (must be positive)
-- SQLite doesn't support ALTER TABLE ADD CONSTRAINT directly
-- This is a reference migration - actual implementation depends on DB type

-- PostgreSQL syntax (if using PostgreSQL):
-- ALTER TABLE budgets ADD CONSTRAINT check_budget_amount_positive CHECK (amount > 0);
-- ALTER TABLE budgets ADD CONSTRAINT check_budget_date_range CHECK (start_date <= end_date);

-- SQLite: Constraints must be added during table creation
-- Use Alembic migration for safe schema changes
CREATE TABLE IF NOT EXISTS budgets_new (
    id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL,
    period TEXT NOT NULL DEFAULT 'monthly',
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL CHECK (start_date <= end_date),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
);

-- Note: This is a reference migration showing the constraints
-- In practice, use Alembic to generate and apply migrations safely
-- The constraints are defined in the models and will be applied when
-- Base.metadata.create_all() is called or via Alembic migrations
