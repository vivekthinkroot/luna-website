#!/usr/bin/env python3
"""
Fix database schema issues by creating missing tables and columns.
"""

import sys
from pathlib import Path

# Add the Backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from data.db import get_session
from sqlalchemy import text
from data.models import TCities, TProfile, TUserPurchase, TSku
from sqlalchemy import create_engine
from config.settings import get_settings

def fix_database_schema():
    """Fix all database schema issues."""
    print("🔧 Fixing Database Schema Issues...")
    
    settings = get_settings()
    engine = create_engine(settings.DB_URL)
    
    try:
        with engine.connect() as conn:
            # Start transaction
            trans = conn.begin()
            
            try:
                print("\n1️⃣ Adding ID column to cities table...")
                # Add id column to cities table if it doesn't exist
                conn.execute(text("""
                    DO $$ 
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM information_schema.columns 
                            WHERE table_name = 'cities' AND column_name = 'id'
                        ) THEN
                            ALTER TABLE cities ADD COLUMN id SERIAL PRIMARY KEY;
                        END IF;
                    END $$;
                """))
                print("✅ Cities table ID column added")
                
                print("\n2️⃣ Creating user_purchases table...")
                # Create user_purchases table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS user_purchases (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(100) NOT NULL,
                        sku_id VARCHAR(50) NOT NULL,
                        payment_link_id VARCHAR(100),
                        status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                        amount DECIMAL(10,2),
                        currency VARCHAR(3) DEFAULT 'INR',
                        valid_till TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                print("✅ user_purchases table created")
                
                print("\n3️⃣ Creating skus table...")
                # Create skus table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS skus (
                        sku_id VARCHAR(50) PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        price DECIMAL(10,2) NOT NULL,
                        currency VARCHAR(3) DEFAULT 'INR',
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """))
                print("✅ skus table created")
                
                print("\n4️⃣ Inserting sample SKU data...")
                # Insert sample SKU data
                conn.execute(text("""
                    INSERT INTO skus (sku_id, name, description, price, currency, is_active)
                    VALUES 
                        ('kundli_basic', 'Basic Kundli', 'Basic Kundli generation service', 99.00, 'INR', TRUE),
                        ('kundli_premium', 'Premium Kundli', 'Premium Kundli with detailed analysis', 199.00, 'INR', TRUE),
                        ('kundli_advanced', 'Advanced Kundli', 'Advanced Kundli with predictions', 299.00, 'INR', TRUE)
                    ON CONFLICT (sku_id) DO NOTHING;
                """))
                print("✅ Sample SKU data inserted")
                
                print("\n5️⃣ Creating indexes for performance...")
                # Create indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_user_purchases_user_id ON user_purchases(user_id);
                    CREATE INDEX IF NOT EXISTS idx_user_purchases_status ON user_purchases(status);
                    CREATE INDEX IF NOT EXISTS idx_cities_city ON cities(city);
                    CREATE INDEX IF NOT EXISTS idx_cities_country ON cities(country);
                """))
                print("✅ Performance indexes created")
                
                # Commit transaction
                trans.commit()
                print("\n🎉 Database schema fixes completed successfully!")
                
            except Exception as e:
                trans.rollback()
                print(f"❌ Error fixing schema: {e}")
                raise
                
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    return True

def verify_schema_fixes():
    """Verify that all schema fixes are working."""
    print("\n🔍 Verifying Schema Fixes...")
    
    try:
        with get_session() as session:
            # Test cities table
            result = session.execute(text("SELECT COUNT(*) FROM cities LIMIT 1"))
            cities_count = result.scalar()
            print(f"✅ Cities table accessible: {cities_count} records")
            
            # Test user_purchases table
            result = session.execute(text("SELECT COUNT(*) FROM user_purchases"))
            purchases_count = result.scalar()
            print(f"✅ user_purchases table accessible: {purchases_count} records")
            
            # Test skus table
            result = session.execute(text("SELECT COUNT(*) FROM skus"))
            skus_count = result.scalar()
            print(f"✅ skus table accessible: {skus_count} records")
            
            # Test cities ID column
            result = session.execute(text("SELECT id FROM cities LIMIT 1"))
            cities_id = result.scalar()
            print(f"✅ Cities ID column working: {cities_id}")
            
    except Exception as e:
        print(f"❌ Schema verification failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Database Schema Fixes")
    print("=" * 50)
    
    if fix_database_schema():
        if verify_schema_fixes():
            print("\n🎉 All database schema issues have been resolved!")
        else:
            print("\n⚠️ Schema fixes applied but verification failed")
    else:
        print("\n❌ Failed to fix database schema")
