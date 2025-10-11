
INSERT INTO users (id, name, email, has_key, is_active) VALUES 
('550e8400-e29b-41d4-a716-446655440001', 'Vlad Test User', 'vlad@faf.com', true, true),
('550e8400-e29b-41d4-a716-446655440002', 'Guest User', 'guest@faf.com', false, true),
('550e8400-e29b-41d4-a716-446655440003', 'Admin User', 'admin@faf.com', true, true),
('550e8400-e29b-41d4-a716-446655440004', 'Unknown Person', 'unknown@example.com', false, false)
ON CONFLICT (id) DO NOTHING;

INSERT INTO checkins (user_id, action_type, confidence_score) VALUES 
('550e8400-e29b-41d4-a716-446655440001', 'entry', 1.0),
('550e8400-e29b-41d4-a716-446655440003', 'entry', 0.95)
ON CONFLICT DO NOTHING;


INSERT INTO temp_guests (name, registered_by, time_slot, description, expires_at) VALUES 
('John Doe', '550e8400-e29b-41d4-a716-446655440001', '9:00-9:30', 'Study session', NOW() + INTERVAL '2 hours'),
('Jane Smith', '550e8400-e29b-41d4-a716-446655440001', '10:00-10:30', 'Project meeting', NOW() + INTERVAL '3 hours')
ON CONFLICT DO NOTHING;