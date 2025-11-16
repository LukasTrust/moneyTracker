"""
Migration Script: Add Performance Indexes to DataRow
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from sqlalchemy import text

def migrate_indexes():
    """
    Add optimized indexes to data_rows table
    """
    with engine.connect() as conn:
        print("🔍 Checking existing indexes...")
        
        # Check existing indexes
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='data_rows'"
        ))
        existing_indexes = {row[0] for row in result}
        print(f"   Existing indexes: {existing_indexes}")
        
        # Define new indexes
        new_indexes = [
            ("idx_account_category", "CREATE INDEX IF NOT EXISTS idx_account_category ON data_rows (account_id, category_id)"),
            ("idx_created_at", "CREATE INDEX IF NOT EXISTS idx_created_at ON data_rows (created_at)"),
            ("idx_category_created", "CREATE INDEX IF NOT EXISTS idx_category_created ON data_rows (category_id, created_at)"),
            ("idx_account_created", "CREATE INDEX IF NOT EXISTS idx_account_created ON data_rows (account_id, created_at)"),
        ]
        
        # Create new indexes
        print("\n📊 Creating performance indexes...")
        for idx_name, idx_sql in new_indexes:
            if idx_name not in existing_indexes:
                print(f"   Creating {idx_name}...")
                conn.execute(text(idx_sql))
                conn.commit()
                print(f"   ✅ {idx_name} created")
            else:
                print(f"   ⏭️  {idx_name} already exists")
        
        # Verify new indexes
        print("\n🔍 Verifying indexes...")
        result = conn.execute(text(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='data_rows'"
        ))
        all_indexes = [row[0] for row in result]
        print(f"   Total indexes: {len(all_indexes)}")
        for idx in sorted(all_indexes):
            print(f"      - {idx}")
        
        print("\n✅ Index migration completed!")


if __name__ == "__main__":
    migrate_indexes()
