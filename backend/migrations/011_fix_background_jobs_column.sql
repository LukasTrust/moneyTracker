-- Migration: Fix Background Jobs Column Name
-- Version: 011
-- Description: Renames job_type to task_type in background_jobs table if needed
-- Author: System
-- Date: 2025-12-06

-- Check if we need to migrate (SQLite doesn't support ALTER COLUMN directly)
-- We need to recreate the table

-- Create temporary table with correct schema
CREATE TABLE IF NOT EXISTS background_jobs_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'queued',
    account_id INTEGER,
    import_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    meta TEXT
);

-- Copy data from old table if it exists (handle both old and new column names)
INSERT INTO background_jobs_new (id, task_type, status, account_id, import_id, created_at, started_at, finished_at, meta)
SELECT id, 
       COALESCE(task_type, job_type) as task_type,
       status, 
       account_id, 
       import_id, 
       created_at, 
       started_at, 
       COALESCE(finished_at, completed_at) as finished_at,
       COALESCE(meta, result) as meta
FROM background_jobs
WHERE EXISTS (SELECT 1 FROM sqlite_master WHERE type='table' AND name='background_jobs');

-- Drop old table
DROP TABLE IF EXISTS background_jobs;

-- Rename new table
ALTER TABLE background_jobs_new RENAME TO background_jobs;

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_background_jobs_task_type ON background_jobs(task_type);
CREATE INDEX IF NOT EXISTS idx_background_jobs_created_at ON background_jobs(created_at DESC);
