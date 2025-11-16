#!/bin/bash
# Migration Script - DataRow Refactoring
# Führt die Migration aus und erstellt ein Backup

set -e  # Exit on error

echo "🚀 DataRow Refactoring Migration"
echo "================================="
echo ""

# Check if running in correct directory
if [ ! -f "backend/data/moneytracker.db" ]; then
    echo "❌ Error: Database not found!"
    echo "   Please run this script from the project root directory."
    exit 1
fi

# Step 1: Create backup
echo "📦 Step 1: Creating backup..."
BACKUP_FILE="backend/data/moneytracker.db.backup.$(date +%Y%m%d_%H%M%S)"
cp backend/data/moneytracker.db "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"
echo ""

# Step 2: Run migration
echo "🔄 Step 2: Running migration..."
cd backend
python migrations/003_refactor_datarow_structured_fields.py
cd ..
echo ""

# Step 3: Verify
echo "✅ Step 3: Verifying migration..."
sqlite3 backend/data/moneytracker.db <<EOF
.mode column
.headers on
SELECT 
    COUNT(*) as total_rows,
    COUNT(transaction_date) as rows_with_date,
    COUNT(amount) as rows_with_amount,
    COUNT(recipient) as rows_with_recipient
FROM data_rows;
EOF
echo ""

# Step 4: Check indexes
echo "📊 Step 4: Checking indexes..."
sqlite3 backend/data/moneytracker.db <<EOF
.indexes data_rows
EOF
echo ""

echo "✅ Migration completed!"
echo ""
echo "📋 Next steps:"
echo "   1. Restart backend: docker-compose restart backend"
echo "   2. Test API: curl http://localhost:8000/api/v1/dashboard/summary"
echo "   3. Check logs: docker-compose logs -f backend"
echo ""
echo "💡 Rollback (if needed):"
echo "   cp $BACKUP_FILE backend/data/moneytracker.db"
echo ""
