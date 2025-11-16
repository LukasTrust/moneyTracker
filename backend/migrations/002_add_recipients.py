"""
Migration: Add Recipients Table and Link to DataRows

Creates:
- recipients table with normalization and aliases
- recipient_id foreign key in data_rows
- Indexes for performance
- Migration script for existing data
"""
from sqlalchemy import text


def upgrade_recipients_table(db_session):
    """
    Add recipients table and migrate existing data
    
    Steps:
    1. Create recipients table
    2. Add recipient_id column to data_rows
    3. Migrate existing data (extract recipients from data->>'recipient')
    4. Add indexes and constraints
    """
    
    # Step 1: Create recipients table
    print("📊 Creating recipients table...")
    db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS recipients (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL,
            normalized_name VARCHAR(200) NOT NULL UNIQUE,
            aliases VARCHAR(500),
            transaction_count INTEGER DEFAULT 0 NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """))
    
    # Step 2: Add indexes to recipients
    print("📇 Creating indexes on recipients...")
    db_session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_recipient_normalized 
        ON recipients(normalized_name);
    """))
    
    db_session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_recipient_name 
        ON recipients(name);
    """))
    
    # Step 3: Add recipient_id column to data_rows
    print("🔗 Adding recipient_id to data_rows...")
    db_session.execute(text("""
        ALTER TABLE data_rows 
        ADD COLUMN IF NOT EXISTS recipient_id INTEGER 
        REFERENCES recipients(id) ON DELETE SET NULL;
    """))
    
    # Step 4: Create index on data_rows.recipient_id
    print("📇 Creating index on data_rows.recipient_id...")
    db_session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_data_row_recipient 
        ON data_rows(recipient_id);
    """))
    
    db_session.commit()
    
    # Step 5: Migrate existing data
    print("🔄 Migrating existing recipients from data_rows...")
    migrate_existing_recipients(db_session)
    
    print("✅ Recipients table migration completed!")


def migrate_existing_recipients(db_session):
    """
    Extract unique recipients from existing data_rows and create recipient records
    """
    # Get unique recipient names from data column
    print("   📝 Extracting unique recipients...")
    result = db_session.execute(text("""
        SELECT DISTINCT data->>'recipient' as recipient_name, COUNT(*) as count
        FROM data_rows
        WHERE data->>'recipient' IS NOT NULL 
          AND data->>'recipient' != ''
        GROUP BY data->>'recipient'
        ORDER BY count DESC;
    """))
    
    recipients = result.fetchall()
    print(f"   Found {len(recipients)} unique recipients")
    
    # Create recipient records
    created_count = 0
    for row in recipients:
        recipient_name = row[0]
        transaction_count = row[1]
        
        if not recipient_name or not recipient_name.strip():
            continue
        
        # Normalize name (lowercase, trim, collapse spaces)
        normalized_name = ' '.join(recipient_name.lower().strip().split())
        
        # Check if already exists
        existing = db_session.execute(text("""
            SELECT id FROM recipients WHERE normalized_name = :normalized
        """), {"normalized": normalized_name}).fetchone()
        
        if not existing:
            # Insert new recipient
            db_session.execute(text("""
                INSERT INTO recipients (name, normalized_name, transaction_count)
                VALUES (:name, :normalized, :count)
            """), {
                "name": recipient_name.strip(),
                "normalized": normalized_name,
                "count": transaction_count
            })
            created_count += 1
    
    db_session.commit()
    print(f"   ✅ Created {created_count} recipient records")
    
    # Link data_rows to recipients
    print("   🔗 Linking data_rows to recipients...")
    db_session.execute(text("""
        UPDATE data_rows
        SET recipient_id = (
            SELECT r.id
            FROM recipients r
            WHERE r.normalized_name = LOWER(TRIM(REGEXP_REPLACE(
                data_rows.data->>'recipient', 
                '\\s+', 
                ' ', 
                'g'
            )))
        )
        WHERE data->>'recipient' IS NOT NULL 
          AND data->>'recipient' != '';
    """))
    
    db_session.commit()
    
    # Count linked rows
    linked = db_session.execute(text("""
        SELECT COUNT(*) FROM data_rows WHERE recipient_id IS NOT NULL
    """)).scalar()
    
    print(f"   ✅ Linked {linked} data_rows to recipients")


def downgrade_recipients_table(db_session):
    """
    Remove recipients table and related columns
    """
    print("🔄 Rolling back recipients migration...")
    
    # Remove recipient_id column from data_rows
    db_session.execute(text("""
        ALTER TABLE data_rows DROP COLUMN IF EXISTS recipient_id;
    """))
    
    # Drop recipients table
    db_session.execute(text("""
        DROP TABLE IF EXISTS recipients CASCADE;
    """))
    
    db_session.commit()
    print("✅ Recipients migration rolled back")


if __name__ == "__main__":
    """
    Run migration manually
    
    Usage:
        python backend/migrations/002_add_recipients.py
    """
    import sys
    sys.path.append('backend')
    
    from app.database import SessionLocal
    
    print("🚀 Starting Recipients Migration...")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        upgrade_recipients_table(db)
        print("=" * 60)
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()
