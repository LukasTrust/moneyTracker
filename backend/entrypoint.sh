#!/bin/bash
# Entrypoint script for Money Tracker Backend
# Handles database initialization, migrations, and server startup

set -e  # Exit on error

echo "🚀 Money Tracker Backend - Starting..."
echo "======================================="
echo ""

# Environment variables
DB_PATH="${DATABASE_URL#sqlite:///}"  # Extract path from sqlite:///path
DB_DIR=$(dirname "$DB_PATH")
MIGRATIONS_DIR="/app/migrations"
MIGRATION_RUNNER="$MIGRATIONS_DIR/run_migrations.py"

echo "📋 Configuration:"
echo "   Database: $DB_PATH"
echo "   Migrations: $MIGRATIONS_DIR"
echo "   Environment: ${ENV:-production}"
echo ""

# ============================================
# Step 1: Ensure database directory exists
# ============================================
echo "📁 Step 1: Checking database directory..."
if [ ! -d "$DB_DIR" ]; then
    echo "   Creating directory: $DB_DIR"
    mkdir -p "$DB_DIR"
    chmod 755 "$DB_DIR"
fi
echo "   ✅ Database directory ready"
echo ""

# ============================================
# Step 2: Check if database exists
# ============================================
echo "🗄️  Step 2: Checking database..."
if [ ! -f "$DB_PATH" ]; then
    echo "   📝 Database does not exist - will be created by SQLAlchemy"
else
    DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
    echo "   ✅ Database exists ($DB_SIZE)"
fi
echo ""

# ============================================
# Step 3: Run migrations automatically
# ============================================
echo "🔄 Step 3: Running database migrations..."
if [ -f "$MIGRATION_RUNNER" ]; then
    python "$MIGRATION_RUNNER"
    if [ $? -eq 0 ]; then
        echo "   ✅ Migrations completed successfully"
    else
        echo "   ❌ Migration failed!"
        exit 1
    fi
else
    echo "   ⚠️  Migration runner not found: $MIGRATION_RUNNER"
    echo "   Skipping migrations..."
fi
echo ""

# ============================================
# Step 4: Verify database integrity
# ============================================
echo "🔍 Step 4: Verifying database..."
if [ -f "$DB_PATH" ]; then
    # Check if database is accessible
    sqlite3 "$DB_PATH" "PRAGMA integrity_check;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ Database integrity OK"
        
        # Show table count
        TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
        echo "   📊 Tables: $TABLE_COUNT"
    else
        echo "   ❌ Database integrity check failed!"
        exit 1
    fi
else
    echo "   ⚠️  Database not yet created (will be initialized on first request)"
fi
echo ""

# ============================================
# Step 5: Start application
# ============================================
echo "🌟 Step 5: Starting application..."
echo "   Command: $@"
echo ""
echo "✅ Initialization complete!"
echo "======================================="
echo ""

# Execute the command passed to docker run or CMD in Dockerfile
exec "$@"
