-- Enum types
CREATE TYPE channel_type AS ENUM ('TELEGRAM', 'WHATSAPP', 'PHONE', 'EMAIL', 'SMS');
CREATE TYPE gender AS ENUM ('MALE', 'FEMALE', 'OTHER');
CREATE TYPE house_sign AS ENUM (
  'ARIES', 'TAURUS', 'GEMINI', 'CANCER', 'LEO', 'VIRGO', 'LIBRA',
  'SCORPIO', 'SAGITTARIUS', 'CAPRICORN', 'AQUARIUS', 'PISCES'
);
CREATE TYPE relationship_type AS ENUM (
  'SELF', 'PARENT', 'CHILD', 'SIBLING', 'FRIEND', 'PARTNER', 'OTHER'
);
CREATE TYPE notification_type AS ENUM ('EMAIL', 'SMS', 'WHATSAPP', 'TELEGRAM', 'PHONE');
CREATE TYPE notification_frequency AS ENUM ('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY');

CREATE TYPE message_type AS ENUM (
    'INCOMING_TEXT',
    'INCOMING_VOICE',
    'OUTGOING_TEXT',
    'OUTGOING_VOICE',
    'INCOMING_DOCUMENT',
    'OUTGOING_DOCUMENT',
    'INCOMING_MEDIA',
    'OUTGOING_MEDIA'
);

CREATE TYPE payment_status AS ENUM ('pending', 'paid', 'failed', 'expired');

CREATE TYPE artifact_type AS ENUM ('kundli_pdf', 'report_image', 'chart_svg', 'other');

-- Users table
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX idx_users_user_id ON users(user_id);

-- UserChannels table
CREATE TABLE user_channels (
    channel_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    channel_type channel_type NOT NULL,
    user_identity TEXT NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Locations table  
CREATE TABLE locations (
    id BIGSERIAL PRIMARY KEY,
    source_id BIGINT UNIQUE,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100),
    province VARCHAR(100), 
    iso3 VARCHAR(3),
    lat DECIMAL(10, 8) NOT NULL,
    lng DECIMAL(11, 8) NOT NULL,
    timezone VARCHAR(50),
    population BIGINT
);

CREATE INDEX IF NOT EXISTS idx_locations_city ON locations (city);

-- Profiles table
CREATE TABLE profiles (
    profile_id UUID PRIMARY KEY,
    birth_datetime TIMESTAMPTZ,
    birth_place TEXT,
    birth_location_id BIGINT,
    name TEXT,
    gender gender,
    sun_sign house_sign,
    moon_sign house_sign,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (birth_location_id) REFERENCES locations(id)
);

-- UserProfileLinks table
CREATE TABLE user_profile_links (
    profile_id UUID NOT NULL,
    user_id UUID NOT NULL,
    relationship_type relationship_type NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (profile_id, user_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX idx_user_profile_links_profile_id ON user_profile_links(profile_id);

-- ProfileData table
CREATE TABLE profile_data (
    profile_id UUID PRIMARY KEY,
    kundli_data JSONB NOT NULL,
    horoscope_chart JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE
);

-- NotificationPreferences table
CREATE TABLE notification_preferences (
    preference_id UUID PRIMARY KEY,
    profile_id UUID NOT NULL,
    notification_type notification_type NOT NULL,
    frequency notification_frequency NOT NULL,
    channel TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(profile_id) ON DELETE CASCADE
);

-- Conversations table
CREATE TABLE conversations (
    message_id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    channel channel_type NOT NULL,
    message_type message_type NOT NULL,
    content TEXT NOT NULL,
    additional_info JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- SKU master table
CREATE TABLE skus (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    sku_id TEXT UNIQUE NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'INR',
    validity INTEGER NOT NULL,  -- validity in days
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);



-- User SKU Purchases table
CREATE TABLE user_purchases (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    payment_link_id TEXT NOT NULL,
    status payment_status NOT NULL,
    sku_id TEXT NOT NULL REFERENCES skus(sku_id),
    valid_till TIMESTAMPTZ, 
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


CREATE INDEX idx_user_purchases_user_id ON user_purchases(user_id);

-- Artifacts table
-- Stores generated outputs (HTML/PDF/SVG) per user
CREATE TABLE artifacts (
    artifact_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    s3_url TEXT NOT NULL,
    artifact_type artifact_type NOT NULL,
    content_type TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

