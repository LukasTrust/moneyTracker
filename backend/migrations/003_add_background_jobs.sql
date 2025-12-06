-- Migration: Add Background Jobs Table
-- Version: 003
-- Description: Creates background_jobs table for async job tracking
-- Author: System
-- Date: 2025-12-06

-- =====================================================
-- BACKGROUND_JOBS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS background_jobs (
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

CREATE INDEX IF NOT EXISTS idx_background_jobs_status ON background_jobs(status);
CREATE INDEX IF NOT EXISTS idx_background_jobs_task_type ON background_jobs(task_type);
CREATE INDEX IF NOT EXISTS idx_background_jobs_created_at ON background_jobs(created_at DESC);
