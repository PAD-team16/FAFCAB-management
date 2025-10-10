-- Check-in Service Database Schema
-- Database is created by Docker environment variables, so we just connect to it

\c checkin_service;

-- Drop existing tables if they exist (for clean Docker builds)
DROP TABLE IF EXISTS unknown_detections CASCADE;
DROP TABLE IF EXISTS checkins CASCADE;
DROP TABLE IF EXISTS temp_guests CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Users table (minimal info, main data is in User Management Service)
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    has_key BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Check-ins table to track entries and exits
CREATE TABLE checkins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    temp_user_name VARCHAR(255), -- For guests
    action_type VARCHAR(20) NOT NULL CHECK (action_type IN ('entry', 'exit')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_guest BOOLEAN DEFAULT FALSE,
    registered_by UUID REFERENCES users(id), -- Who registered the guest
    description TEXT,
    confidence_score DECIMAL(3,2), -- From facial recognition (0.00-1.00)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Temporary guests table
CREATE TABLE temp_guests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    registered_by UUID NOT NULL REFERENCES users(id),
    time_slot VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    checked_in BOOLEAN DEFAULT FALSE,
    checked_in_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unknown persons detected
CREATE TABLE unknown_detections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score DECIMAL(3,2),
    image_url VARCHAR(500),
    admin_notified BOOLEAN DEFAULT FALSE,
    resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes and constraints (fixed partial index)
CREATE UNIQUE INDEX idx_temp_guests_unique_active 
ON temp_guests (name, time_slot, registered_by) 
WHERE is_active = true;

CREATE INDEX idx_checkins_user_id ON checkins(user_id);
CREATE INDEX idx_checkins_timestamp ON checkins(timestamp);
CREATE INDEX idx_checkins_action_type ON checkins(action_type);
CREATE INDEX idx_temp_guests_expires_at ON temp_guests(expires_at);
CREATE INDEX idx_temp_guests_checked_in ON temp_guests(checked_in);
CREATE INDEX idx_unknown_detections_resolved ON unknown_detections(resolved);

-- Views for common queries
DROP VIEW IF EXISTS current_occupants CASCADE;
DROP VIEW IF EXISTS key_status CASCADE;

CREATE VIEW current_occupants AS
WITH latest_checkins AS (
  SELECT DISTINCT ON (user_id) user_id, action_type, timestamp
  FROM checkins 
  WHERE user_id IS NOT NULL
  ORDER BY user_id, timestamp DESC
)
SELECT u.id, u.name, u.has_key, lc.timestamp as last_seen
FROM users u
JOIN latest_checkins lc ON u.id = lc.user_id
WHERE lc.action_type = 'entry' AND u.is_active = true;

CREATE VIEW key_status AS
SELECT 
  COUNT(*) as key_holders_inside,
  CASE 
    WHEN COUNT(*) > 0 THEN 'secure'
    ELSE 'no_key_holder_inside'
  END as status
FROM current_occupants 
WHERE has_key = true;