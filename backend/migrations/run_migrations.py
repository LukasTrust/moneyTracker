#!/usr/bin/env python3
"""
Database migration runner for Money Tracker.
Applies SQL migrations in order based on filename numbering.
"""

import os
import sqlite3
import sys
from pathlib import Path


def get_database_path():
    """Get database path from environment variable."""
    db_url = os.getenv("DATABASE_URL", "sqlite:////app/data/moneytracker.db")
    # Strip sqlite:/// prefix
    if db_url.startswith("sqlite:///"):
        return db_url[10:]  # Remove "sqlite:///"
    elif db_url.startswith("sqlite://"):
        return db_url[9:]   # Remove "sqlite://"
    return db_url


def ensure_migrations_table(cursor):
    """Create migrations tracking table if it doesn't exist."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


def get_applied_migrations(cursor):
    """Get list of already applied migrations."""
    cursor.execute("SELECT version FROM schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def get_migration_files(migrations_dir):
    """Get sorted list of migration SQL files."""
    sql_files = sorted([
        f for f in os.listdir(migrations_dir)
        if f.endswith('.sql') and not f.startswith('_')
    ])
    return sql_files


def apply_migration(cursor, migration_file, migrations_dir):
    """Apply a single migration file."""
    migration_path = os.path.join(migrations_dir, migration_file)
    
    print(f"   📝 Applying migration: {migration_file}")
    
    with open(migration_path, 'r') as f:
        sql = f.read()
    
    # Execute the entire SQL file as a script
    # This handles complex statements like triggers correctly
    try:
        cursor.executescript(sql)
    except sqlite3.Error as e:
        print(f"   ⚠️  Error executing migration script")
        raise e
    
    # Record migration as applied
    version = migration_file.replace('.sql', '')
    cursor.execute(
        "INSERT INTO schema_migrations (version) VALUES (?)",
        (version,)
    )
    
    print(f"   ✅ Applied: {migration_file}")


def run_migrations():
    """Main migration runner."""
    migrations_dir = Path(__file__).parent
    db_path = get_database_path()
    
    print(f"🔄 Starting database migrations")
    print(f"   Database: {db_path}")
    print(f"   Migrations directory: {migrations_dir}")
    print()
    
    # Ensure database directory exists
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
    except sqlite3.Error as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)
    
    try:
        # Setup migrations tracking
        ensure_migrations_table(cursor)
        conn.commit()
        
        # Get migrations status
        applied = get_applied_migrations(cursor)
        available = get_migration_files(migrations_dir)
        
        pending = [m for m in available if m.replace('.sql', '') not in applied]
        
        if not pending:
            print("✅ All migrations already applied. Database is up to date.")
            return 0
        
        print(f"📊 Found {len(available)} total migrations")
        print(f"   ✅ Applied: {len(applied)}")
        print(f"   📝 Pending: {len(pending)}")
        print()
        
        # Apply pending migrations
        for migration_file in pending:
            try:
                apply_migration(cursor, migration_file, migrations_dir)
                conn.commit()
            except Exception as e:
                print(f"❌ Migration failed: {migration_file}")
                print(f"   Error: {e}")
                conn.rollback()
                sys.exit(1)
        
        print()
        print(f"✅ Successfully applied {len(pending)} migration(s)")
        return 0
        
    except Exception as e:
        print(f"❌ Migration process failed: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(run_migrations())
