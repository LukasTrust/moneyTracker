#!/usr/bin/env bash
# Entrypoint script for Money Tracker Backend
# Handles database initialization, migrations, and server startup

set -euo pipefail  # Exit on error, undefined vars, and pipe failures

echo "🚀 Money Tracker Backend - Starting..."
echo "======================================="
echo ""

# Validate required environment variables
: "${DATABASE_URL:?DATABASE_URL must be set}"

# Environment variables with defaults
DB_PATH="${DATABASE_URL#sqlite:///}"  # Extract path from sqlite:///path
DB_DIR=$(dirname "$DB_PATH")
MIGRATIONS_DIR="/app/migrations"
MIGRATION_RUNNER="$MIGRATIONS_DIR/run_migrations.py"
AUTO_MIGRATE="${AUTO_MIGRATE:-false}"
ENV="${ENV:-production}"

echo "📋 Configuration:"
echo "   Database: $DB_PATH"
echo "   Migrations: $MIGRATIONS_DIR"
echo "   Environment: $ENV"
echo "   Auto-migrate: $AUTO_MIGRATE"
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
# Step 3: Run migrations (if enabled)
# ============================================
if [ "$AUTO_MIGRATE" = "true" ]; then
    echo "🔄 Step 3: Running database migrations..."
    if [ -f "$MIGRATION_RUNNER" ]; then
        # Try to acquire lock if flock is available
        if command -v flock >/dev/null 2>&1; then
            LOCK_FILE="/tmp/moneytracker-migrate.lock"
            exec 9>"$LOCK_FILE"
            if flock -n 9; then
                echo "   🔒 Lock acquired, running migrations..."
                python "$MIGRATION_RUNNER"
                if [ $? -eq 0 ]; then
                    echo "   ✅ Migrations completed successfully"
                else
                    echo "   ❌ Migration failed!"
                    exit 1
                fi
            else
                echo "   ⏳ Another migration is running, skipping..."
            fi
        else
            # No flock available, run without lock
            echo "   ⚠️  flock not available, running migrations without lock..."
            python "$MIGRATION_RUNNER"
            if [ $? -eq 0 ]; then
                echo "   ✅ Migrations completed successfully"
            else
                echo "   ❌ Migration failed!"
                exit 1
            fi
        fi
    else
        echo "   ⚠️  Migration runner not found: $MIGRATION_RUNNER"
        echo "   Skipping migrations..."
    fi
    echo ""
else
    echo "🔄 Step 3: Auto-migrate disabled (set AUTO_MIGRATE=true to enable)"
    echo ""
fi

# ============================================
# Step 4: Basic database check (skip integrity check)
# ============================================
echo "🔍 Step 4: Checking database accessibility..."
if [ -f "$DB_PATH" ]; then
    # Quick check - just count tables without full integrity check
    if TABLE_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='table';" 2>&1); then
        echo "   ✅ Database accessible"
        echo "   📊 Tables: $TABLE_COUNT"
    else
        echo "   ❌ Database not accessible!"
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
