#!/bin/bash
# Apply Transfer Migration (007)
# Adds transfers table and "Transfer" category

set -e  # Exit on error

echo "🚀 Transfer Migration (007)"
echo "==========================="
echo ""

# Check if running in Docker container
if [ -f "/.dockerenv" ]; then
    DB_PATH="/app/data/moneytracker.db"
else
    DB_PATH="backend/data/moneytracker.db"
fi

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "❌ Error: Database not found at $DB_PATH"
    exit 1
fi

# Step 1: Create backup
echo "📦 Step 1: Creating backup..."
BACKUP_FILE="${DB_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
cp "$DB_PATH" "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"
echo ""

# Step 2: Run migration
echo "🔄 Step 2: Running migration..."
if [ -f "/.dockerenv" ]; then
    sqlite3 "$DB_PATH" < /app/migrations/007_add_transfers.sql
else
    sqlite3 "$DB_PATH" < backend/migrations/007_add_transfers.sql
fi
echo "✅ Migration completed"
echo ""

# Step 3: Verify
echo "✅ Step 3: Verifying migration..."
sqlite3 "$DB_PATH" <<EOF
.mode column
.headers on

-- Check if transfers table exists
SELECT name FROM sqlite_master WHERE type='table' AND name='transfers';

-- Check if Transfer category exists
SELECT id, name, color, icon FROM categories WHERE name='Transfer';
EOF
echo ""

echo "🎉 Migration 007 completed successfully!"
echo ""
echo "Next steps:"
echo "  1. Restart your application"
echo "  2. Go to Dashboard > Transfers tab"
echo "  3. Click 'Auto-Detect Transfers' to find matching transactions"
