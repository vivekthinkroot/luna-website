-- Create skus table
CREATE TABLE IF NOT EXISTS skus (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku_id VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    validity INTEGER NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create user_purchases table
CREATE TABLE IF NOT EXISTS user_purchases (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    sku_id VARCHAR(50) NOT NULL,
    payment_link_id VARCHAR(255) UNIQUE NOT NULL,
    status VARCHAR(50) NOT NULL,
    valid_till TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Insert basic SKU (ID 1)
INSERT INTO skus (name, sku_id, amount, validity, currency, created_at, updated_at)
VALUES ('Basic Kundli Plan', '1', 100.0, 30, 'INR', NOW(), NOW())
ON CONFLICT (sku_id) DO NOTHING;
