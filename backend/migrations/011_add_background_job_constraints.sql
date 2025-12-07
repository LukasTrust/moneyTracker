-- Migration: Add Foreign Key Constraints to Background Jobs
-- Version: 011
-- Description: Adds proper foreign key constraints to background_jobs table for data integrity
-- Author: System
-- Date: 2025-12-07

-- Note: SQLite does not support adding foreign keys to existing tables directly.
-- We need to recreate the table with the constraints.

-- Step 1: Create a new table with foreign key constraints
CREATE TABLE IF NOT EXISTS background_jobs_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'queued',
    account_id INTEGER,
    import_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    meta TEXT,
    
    -- Add foreign key constraints
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE,
    FOREIGN KEY (import_id) REFERENCES import_history(id) ON DELETE SET NULL
);

-- Step 2: Copy data from old table to new table
INSERT INTO background_jobs_new (id, task_type, status, account_id, import_id, created_at, started_at, finished_at, meta)
SELECT id, task_type, status, account_id, import_id, created_at, started_at, finished_at, meta
FROM background_jobs;

-- Step 3: Drop old table
DROP TABLE background_jobs;

-- Step 4: Rename new table to original name
ALTER TABLE background_jobs_new RENAME TO background_jobs;

-- Step 5: Recreate indexes
CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_background_jobs_task_type ON background_jobs(task_type);
CREATE INDEX IF NOT EXISTS idx_background_jobs_created_at ON background_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_background_jobs_account_id ON background_jobs(account_id);
CREATE INDEX IF NOT EXISTS idx_background_jobs_import_id ON background_jobs(import_id);
