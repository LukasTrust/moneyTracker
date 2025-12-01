-- Migration: Add unique constraint for import deduplication
-- Audit reference: 01_backend_action_plan.md - P0 Import dedupe at DB level
-- Date: 2025-12-01
-- Description: Adds unique constraint on (account_id, file_hash) to prevent duplicate imports

-- Create unique index if not exists (PostgreSQL and SQLite compatible syntax varies)
-- For SQLite:
CREATE UNIQUE INDEX IF NOT EXISTS idx_import_history_account_file_hash 
ON import_history(account_id, file_hash);

-- For PostgreSQL (use this version if target DB is PostgreSQL):
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_import_history_account_file_hash 
-- ON import_history(account_id, file_hash) 
-- WHERE file_hash IS NOT NULL;

-- Note: This migration should be applied after data cleanup if there are existing duplicates
-- Check for duplicates before applying:
-- SELECT account_id, file_hash, COUNT(*) 
-- FROM import_history 
-- WHERE file_hash IS NOT NULL
-- GROUP BY account_id, file_hash 
-- HAVING COUNT(*) > 1;
