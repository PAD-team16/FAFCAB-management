-- Data Warehouse Schema for FAFCAB Management Platform

-- Connect to data warehouse database
\c fafcab_dw;

-- Dimension Tables

-- Time Dimension
CREATE TABLE dim_time (
    time_id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    year INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(10) NOT NULL,
    month_name VARCHAR(10) NOT NULL,
    is_weekend BOOLEAN NOT NULL
);

-- Users Dimension
CREATE TABLE dim_users (
    user_id UUID PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    roles TEXT[], -- Array of roles
    is_active BOOLEAN DEFAULT TRUE,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    user_type VARCHAR(50) -- 'student', 'FAF_NGO_Member', 'admin', etc.
);

-- Services Dimension
CREATE TABLE dim_services (
    service_id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    service_description TEXT,
    technology_stack VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

-- Resources Dimension
CREATE TABLE dim_resources (
    resource_id SERIAL PRIMARY KEY,
    resource_name VARCHAR(255) NOT NULL,
    resource_type VARCHAR(100) NOT NULL, -- 'consumable', 'shared_item', 'booking', 'fundraising_campaign'
    category VARCHAR(100),
    owner VARCHAR(255),
    status VARCHAR(50) -- 'available', 'taken', 'unavailable'
);

-- Locations Dimension
CREATE TABLE dim_locations (
    location_id SERIAL PRIMARY KEY,
    location_name VARCHAR(100) NOT NULL, -- 'main_room', 'kitchen', 'entry_point'
    location_description TEXT,
    capacity INTEGER
);

-- Categories Dimension
CREATE TABLE dim_categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    category_type VARCHAR(50) NOT NULL, -- 'activity', 'resource', 'financial'
    description TEXT
);

-- Fact Tables

-- User Activities Fact Table
CREATE TABLE fact_user_activities (
    activity_id SERIAL PRIMARY KEY,
    time_id INTEGER REFERENCES dim_time(time_id),
    user_id UUID REFERENCES dim_users(user_id),
    service_id INTEGER REFERENCES dim_services(service_id),
    activity_type VARCHAR(100) NOT NULL, -- 'login', 'create_post', 'send_message', 'book_room', etc.
    activity_description TEXT,
    timestamp TIMESTAMP NOT NULL,
    session_id VARCHAR(255) -- For grouping related activities
);

-- Financial Transactions Fact Table
CREATE TABLE fact_financial_transactions (
    transaction_id SERIAL PRIMARY KEY,
    time_id INTEGER REFERENCES dim_time(time_id),
    user_id UUID REFERENCES dim_users(user_id), -- NULL for external entities
    resource_id INTEGER REFERENCES dim_resources(resource_id), -- Related resource if applicable
    service_id INTEGER REFERENCES dim_services(service_id),
    transaction_type VARCHAR(50) NOT NULL, -- 'donation', 'expense', 'debt', 'refund'
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'MDL',
    description TEXT,
    transaction_status VARCHAR(50) DEFAULT 'completed', -- 'completed', 'pending', 'cancelled'
    timestamp TIMESTAMP NOT NULL
);

-- Resource Usage Fact Table
CREATE TABLE fact_resource_usage (
    usage_id SERIAL PRIMARY KEY,
    time_id INTEGER REFERENCES dim_time(time_id),
    user_id UUID REFERENCES dim_users(user_id),
    resource_id INTEGER REFERENCES dim_resources(resource_id),
    service_id INTEGER REFERENCES dim_services(service_id),
    location_id INTEGER REFERENCES dim_locations(location_id),
    usage_type VARCHAR(50) NOT NULL, -- 'borrow', 'consume', 'book', 'restock'
    quantity INTEGER DEFAULT 1,
    duration_minutes INTEGER, -- For bookings and borrowed items
    timestamp TIMESTAMP NOT NULL,
    returned_timestamp TIMESTAMP -- For borrowed items
);

-- Communication Events Fact Table
CREATE TABLE fact_communication_events (
    event_id SERIAL PRIMARY KEY,
    time_id INTEGER REFERENCES dim_time(time_id),
    user_id UUID REFERENCES dim_users(user_id),
    service_id INTEGER REFERENCES dim_services(service_id),
    channel_id UUID, -- For channel-related events
    event_type VARCHAR(50) NOT NULL, -- 'message_sent', 'channel_created', 'user_joined', 'message_deleted'
    message_length INTEGER, -- Length of message content
    is_private BOOLEAN, -- Whether the communication was private
    timestamp TIMESTAMP NOT NULL
);

-- Check-in Events Fact Table
CREATE TABLE fact_checkin_events (
    checkin_id SERIAL PRIMARY KEY,
    time_id INTEGER REFERENCES dim_time(time_id),
    user_id UUID REFERENCES dim_users(user_id),
    location_id INTEGER REFERENCES dim_locations(location_id),
    action_type VARCHAR(20) NOT NULL, -- 'entry', 'exit'
    is_guest BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3,2), -- From facial recognition
    timestamp TIMESTAMP NOT NULL
);

-- Indexes for Performance
CREATE INDEX idx_fact_user_activities_time ON fact_user_activities(time_id);
CREATE INDEX idx_fact_user_activities_user ON fact_user_activities(user_id);
CREATE INDEX idx_fact_user_activities_service ON fact_user_activities(service_id);

CREATE INDEX idx_fact_financial_transactions_time ON fact_financial_transactions(time_id);
CREATE INDEX idx_fact_financial_transactions_user ON fact_financial_transactions(user_id);
CREATE INDEX idx_fact_financial_transactions_service ON fact_financial_transactions(service_id);

CREATE INDEX idx_fact_resource_usage_time ON fact_resource_usage(time_id);
CREATE INDEX idx_fact_resource_usage_user ON fact_resource_usage(user_id);
CREATE INDEX idx_fact_resource_usage_resource ON fact_resource_usage(resource_id);

CREATE INDEX idx_fact_communication_events_time ON fact_communication_events(time_id);
CREATE INDEX idx_fact_communication_events_user ON fact_communication_events(user_id);

CREATE INDEX idx_fact_checkin_events_time ON fact_checkin_events(time_id);
CREATE INDEX idx_fact_checkin_events_user ON fact_checkin_events(user_id);
CREATE INDEX idx_fact_checkin_events_location ON fact_checkin_events(location_id);

-- Initial data for dimensions
INSERT INTO dim_services (service_name, service_description, technology_stack) VALUES
('user-management-service', 'User authentication and management', 'Java/Spring Boot'),
('notification-service', 'Email and Discord notifications', 'Java/Spring Boot'),
('communication-service', 'Public and private chat channels', 'Elixir'),
('consumables-service', 'Tea and consumable item tracking', 'Elixir'),
('cab-booking-service', 'Room booking management', 'Node.js'),
('checkin-service', 'User check-in tracking', 'Node.js'),
('lostnfound-service', 'Lost and found item management', 'Elixir'),
('budgeting-service', 'Financial tracking and debt management', 'Elixir'),
('fundraising-service', 'Fundraising campaign management', 'Java/Spring Boot'),
('sharing-service', 'Shared item tracking', 'Java/Spring Boot');

INSERT INTO dim_locations (location_name, location_description, capacity) VALUES
('main_room', 'Main FAF Cab room', 20),
('kitchen', 'Kitchen area', 10),
('entry_point', 'Main entrance', NULL);

INSERT INTO dim_categories (category_name, category_type, description) VALUES
('user_management', 'activity', 'User authentication and profile activities'),
('communication', 'activity', 'Messaging and chat activities'),
('resource_booking', 'activity', 'Room and resource booking activities'),
('financial', 'activity', 'Financial transactions and donations'),
('checkin', 'activity', 'User entry and exit activities'),
('consumable', 'resource', 'Tea, sugar, and other consumable items'),
('shared_item', 'resource', 'Board games, chargers, and other shared items'),
('booking', 'resource', 'Room bookings for events and meetings'),
('fundraising', 'resource', 'Fundraising campaigns for specific items');