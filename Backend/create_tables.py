#!/usr/bin/env python3
"""
Create payment tables using SQL script.
"""

import sys
import os

# Add the Backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from data.db import get_session
from sqlalchemy import text

def create_tables():
    """Create the payment tables using SQL."""
    try:
        with get_session() as session:
            # Read and execute the SQL script
            with open('create_skus_table.sql', 'r') as f:
                sql_script = f.read()
            
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:
                    session.exec(text(statement))
            
            session.commit()
            print("SUCCESS: Payment tables created successfully!")
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to create tables: {e}")
        return False

def verify_tables():
    """Verify that the tables exist."""
    try:
        with get_session() as session:
            # Check if skus table exists
            result = session.exec(text("SELECT COUNT(*) FROM skus WHERE sku_id = '1'")).first()
            if result and result[0] > 0:
                print("SUCCESS: SKU ID 1 found in database")
                return True
            else:
                print("ERROR: SKU ID 1 not found")
                return False
                
    except Exception as e:
        print(f"ERROR: Failed to verify tables: {e}")
        return False

def main():
    """Main function."""
    print("Creating payment tables...")
    print("=" * 40)
    
    if create_tables():
        print("\nVerifying tables...")
        if verify_tables():
            print("\nSUCCESS: Payment tables setup completed!")
            print("The Pay Now button should now work with SKU ID 1!")
            return True
    
    print("\nERROR: Table creation failed")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
