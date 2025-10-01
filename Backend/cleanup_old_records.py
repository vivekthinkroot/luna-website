#!/usr/bin/env python3
"""
Clean up old user purchase records that might have invalid status values.
"""

import sys
import os
from datetime import datetime, timezone

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.db import get_session
from sqlalchemy import text
from utils.logger import get_logger

logger = get_logger()

def cleanup_old_records():
    """Clean up old user purchase records."""
    print("Cleaning up old user purchase records")
    print("=" * 40)
    
    try:
        with get_session() as db:
            # Check what records exist
            result = db.exec(text("SELECT id, user_id, status FROM user_purchases ORDER BY id"))
            records = result.fetchall()
            
            print(f"Found {len(records)} records:")
            for record in records:
                print(f"  ID: {record.id}, User: {record.user_id}, Status: {record.status}")
            
            # Delete records with id = 0 (these are problematic)
            print("\nDeleting records with id = 0...")
            result = db.exec(text("DELETE FROM user_purchases WHERE id = 0"))
            deleted_count = result.rowcount
            print(f"Deleted {deleted_count} records with id = 0")
            
            # Check remaining records
            result = db.exec(text("SELECT id, user_id, status FROM user_purchases ORDER BY id"))
            records = result.fetchall()
            
            print(f"\nRemaining {len(records)} records:")
            for record in records:
                print(f"  ID: {record.id}, User: {record.user_id}, Status: {record.status}")
            
            return True
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function to clean up old records."""
    print("Cleanup Old Records")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    if cleanup_old_records():
        print("\nSUCCESS: Cleanup completed!")
    else:
        print("\nERROR: Cleanup failed!")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
