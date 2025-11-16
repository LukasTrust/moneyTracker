"""
Migration Runner - Automatic Database Migrations
=================================================

This script:
1. Creates a schema_migrations tracking table
2. Discovers all migration files in migrations/ directory
3. Merges them into a single migration if needed
4. Executes pending migrations in order
5. Records executed migrations in tracking table

Supports both Python (.py) and SQL (.sql) migration files.
All migrations are idempotent (safe to run multiple times).
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime
import importlib.util
import re

# Database configuration
DB_PATH = os.getenv("DATABASE_URL", "sqlite:///./moneytracker.db").replace("sqlite:///", "")
MIGRATIONS_DIR = Path(__file__).parent
MERGED_MIGRATION_FILE = MIGRATIONS_DIR / "_merged_migration.sql"


class MigrationRunner:
    """Handles database migrations with tracking and merging"""
    
    def __init__(self, db_path: str, migrations_dir: Path):
        self.db_path = db_path
        self.migrations_dir = migrations_dir
        self.conn = None
        
    def connect(self):
        """Connect to database and enable foreign keys"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def create_migrations_table(self):
        """Create schema_migrations tracking table if not exists"""
        print("📊 Creating migration tracking table...")
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum VARCHAR(64),
                execution_time_ms INTEGER
            )
        """)
        self.conn.commit()
        print("   ✅ Migration tracking table ready")
    
    def get_applied_migrations(self):
        """Get list of already applied migration versions"""
        cursor = self.conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        )
        return {row['version'] for row in cursor.fetchall()}
    
    def discover_migration_files(self):
        """
        Discover all migration files in migrations directory
        Returns list of tuples: (version, filepath, description)
        """
        migrations = []
        
        # Pattern: 001_description.py or 001_description.sql
        pattern = re.compile(r'^(\d+)_(.+)\.(py|sql)$')
        
        for file in sorted(self.migrations_dir.iterdir()):
            if file.name.startswith('_') or file.name == 'run_migrations.py':
                continue  # Skip special files
            
            match = pattern.match(file.name)
            if match:
                version = match.group(1)
                description = match.group(2).replace('_', ' ').title()
                migrations.append((version, file, description, match.group(3)))
        
        return sorted(migrations, key=lambda x: x[0])
    
    def merge_migrations(self, migration_files):
        """
        Merge all migration files into a single SQL file
        Handles both .py and .sql files
        """
        print("\n🔀 Merging migrations...")
        
        merged_sql = []
        merged_sql.append("-- Merged Migration File")
        merged_sql.append(f"-- Generated: {datetime.now().isoformat()}")
        merged_sql.append("-- DO NOT EDIT MANUALLY\n")
        
        for version, filepath, description, file_type in migration_files:
            merged_sql.append(f"\n-- ==========================================")
            merged_sql.append(f"-- Migration {version}: {description}")
            merged_sql.append(f"-- Source: {filepath.name}")
            merged_sql.append(f"-- ==========================================\n")
            
            if file_type == 'sql':
                # Direct SQL file
                with open(filepath, 'r', encoding='utf-8') as f:
                    merged_sql.append(f.read())
            
            elif file_type == 'py':
                # Python migration - extract SQL or run function
                print(f"   ⚠️  Python migration detected: {filepath.name}")
                print(f"      Running directly (cannot merge to SQL)")
                # We'll execute Python migrations separately
                continue
        
        # Write merged file
        merged_content = '\n'.join(merged_sql)
        
        if merged_content.strip():
            with open(MERGED_MIGRATION_FILE, 'w', encoding='utf-8') as f:
                f.write(merged_content)
            print(f"   ✅ Merged SQL saved to: {MERGED_MIGRATION_FILE.name}")
            return MERGED_MIGRATION_FILE
        
        return None
    
    def execute_python_migration(self, filepath: Path, version: str):
        """Execute a Python migration file"""
        print(f"\n🐍 Executing Python migration: {filepath.name}")
        
        try:
            # Import the migration module
            spec = importlib.util.spec_from_file_location(f"migration_{version}", filepath)
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"migration_{version}"] = module
            spec.loader.exec_module(module)
            
            # Look for common migration functions
            start_time = datetime.now()
            
            if hasattr(module, 'upgrade'):
                # Alembic-style upgrade function
                module.upgrade(self.conn)
            elif hasattr(module, 'migrate'):
                # Custom migrate function
                module.migrate()
            elif hasattr(module, 'run'):
                # Generic run function
                module.run()
            else:
                # Just execute the module (runs at import)
                print(f"   ℹ️  No explicit function found, module executed at import")
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.conn.commit()
            
            return execution_time
            
        except Exception as e:
            self.conn.rollback()
            print(f"   ❌ Error executing Python migration: {e}")
            raise
    
    def execute_sql_migration(self, filepath: Path):
        """Execute a SQL migration file"""
        print(f"\n📄 Executing SQL migration: {filepath.name}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            start_time = datetime.now()
            
            # Execute all statements
            self.conn.executescript(sql)
            
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.conn.commit()
            
            return execution_time
            
        except Exception as e:
            self.conn.rollback()
            print(f"   ❌ Error executing SQL migration: {e}")
            raise
    
    def record_migration(self, version: str, description: str, execution_time: int):
        """Record a migration as applied"""
        self.conn.execute("""
            INSERT INTO schema_migrations (version, description, execution_time_ms)
            VALUES (?, ?, ?)
        """, (version, description, execution_time))
        self.conn.commit()
    
    def run(self):
        """Main migration runner"""
        print("\n" + "="*50)
        print("🔄 DATABASE MIGRATION RUNNER")
        print("="*50)
        
        try:
            # Connect to database
            self.connect()
            
            # Create tracking table
            self.create_migrations_table()
            
            # Get already applied migrations
            applied = self.get_applied_migrations()
            print(f"\n📋 Already applied migrations: {len(applied)}")
            for version in sorted(applied):
                print(f"   ✅ {version}")
            
            # Discover migration files
            migrations = self.discover_migration_files()
            print(f"\n📂 Found {len(migrations)} migration file(s)")
            
            # Filter pending migrations
            pending = [m for m in migrations if m[0] not in applied]
            
            if not pending:
                print("\n✅ No pending migrations - database is up to date!")
                return
            
            print(f"\n⏳ Pending migrations: {len(pending)}")
            for version, filepath, description, _ in pending:
                print(f"   🔜 {version}: {description}")
            
            # Merge migrations (SQL only)
            sql_migrations = [m for m in pending if m[3] == 'sql']
            py_migrations = [m for m in pending if m[3] == 'py']
            
            # Execute merged SQL migrations
            if sql_migrations:
                merged_file = self.merge_migrations(sql_migrations)
                if merged_file and merged_file.exists():
                    print(f"\n🚀 Executing merged SQL migrations...")
                    execution_time = self.execute_sql_migration(merged_file)
                    
                    # Record all SQL migrations as applied
                    for version, _, description, _ in sql_migrations:
                        self.record_migration(version, description, execution_time)
                        print(f"   ✅ Recorded: {version}")
            
            # Execute Python migrations individually
            for version, filepath, description, _ in py_migrations:
                execution_time = self.execute_python_migration(filepath, version)
                self.record_migration(version, description, execution_time)
                print(f"   ✅ Recorded: {version}")
            
            print("\n" + "="*50)
            print("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"\n❌ MIGRATION FAILED: {e}")
            raise
        
        finally:
            self.close()


def main():
    """Entry point"""
    runner = MigrationRunner(DB_PATH, MIGRATIONS_DIR)
    runner.run()


if __name__ == "__main__":
    main()
