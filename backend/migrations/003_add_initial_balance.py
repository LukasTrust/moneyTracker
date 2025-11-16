"""
Migration: Add initial_balance to accounts

Adds initial_balance field to accounts table to track the starting balance
of each account. This is crucial for accurate balance calculations when
an account already has funds before the first transaction is recorded.
"""


def upgrade_initial_balance(db_session):
    """
    Add initial_balance column to accounts table
    
    Steps:
    1. Check if accounts table exists
    2. Add initial_balance column with default 0.00
    3. Update existing accounts to have explicit 0.00 if needed
    """
    
    # Step 1: Check if accounts table exists
    print("📊 Checking if accounts table exists...")
    cursor = db_session.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='accounts';
    """)
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("⚠️  Accounts table does not exist yet - skipping migration")
        print("   (Table will be created by SQLAlchemy with initial_balance field)")
        return
    
    # Step 2: Check if column already exists
    cursor = db_session.execute("PRAGMA table_info(accounts);")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'initial_balance' in columns:
        print("✅ Column initial_balance already exists - skipping")
        return
    
    # Step 3: Add initial_balance column
    print("📊 Adding initial_balance column to accounts table...")
    db_session.execute("""
        ALTER TABLE accounts 
        ADD COLUMN initial_balance REAL NOT NULL DEFAULT 0.0;
    """)
    
    # Step 4: Set default for existing rows
    print("📝 Setting default values for existing accounts...")
    db_session.execute("""
        UPDATE accounts 
        SET initial_balance = 0.0 
        WHERE initial_balance IS NULL;
    """)
    
    db_session.commit()
    print("✅ Migration completed: initial_balance added to accounts")


def downgrade_initial_balance(db_session):
    """
    Remove initial_balance column from accounts table
    
    WARNING: This will permanently delete all initial_balance data!
    """
    
    print("⚠️  Checking if accounts table exists...")
    cursor = db_session.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='accounts';
    """)
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        print("⚠️  Accounts table does not exist - skipping downgrade")
        return
    
    print("⚠️  Removing initial_balance column from accounts table...")
    # Note: SQLite doesn't support DROP COLUMN directly in older versions
    # This would require recreating the table, which is risky
    # For now, we'll just log a warning
    print("⚠️  WARNING: SQLite doesn't support DROP COLUMN easily.")
    print("   Manual intervention may be required to remove this column.")
    
    db_session.commit()
    print("✅ Downgrade completed (column not removed - manual cleanup needed)")


# Migration metadata
migration_id = "003"
migration_name = "add_initial_balance"
description = "Add initial_balance field to accounts table"


def upgrade(db_session):
    """Main upgrade function"""
    upgrade_initial_balance(db_session)


def downgrade(db_session):
    """Main downgrade function"""
    downgrade_initial_balance(db_session)


if __name__ == "__main__":
    print(f"Migration {migration_id}: {migration_name}")
    print(f"Description: {description}")
    print("\nThis script should be run via run_migrations.py")
