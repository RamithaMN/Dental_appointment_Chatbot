-- ================================================================
-- Dental Chatbot Database Schema
-- PostgreSQL 15+
-- ================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ================================================================
-- 1. USERS TABLE
-- Stores user profiles and authentication information
-- ================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    address TEXT,
    
    -- Profile metadata
    role VARCHAR(20) DEFAULT 'patient' CHECK (role IN ('patient', 'dentist', 'admin', 'staff')),
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false,
    phone_verified BOOLEAN DEFAULT false,
    
    -- Medical information
    insurance_provider VARCHAR(100),
    insurance_policy_number VARCHAR(50),
    medical_notes TEXT,
    allergies TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Soft delete
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for users table
CREATE INDEX idx_users_username ON users(username) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_created_at ON users(created_at DESC);
CREATE INDEX idx_users_last_login ON users(last_login_at DESC NULLS LAST);

-- ================================================================
-- 2. APPOINTMENTS TABLE
-- Stores appointment scheduling data and status
-- ================================================================

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Patient information
    patient_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    patient_name VARCHAR(100) NOT NULL,
    patient_email VARCHAR(255),
    patient_phone VARCHAR(20),
    
    -- Appointment details
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    appointment_type VARCHAR(50) NOT NULL CHECK (appointment_type IN (
        'checkup', 'cleaning', 'filling', 'root_canal', 'extraction', 
        'whitening', 'orthodontics', 'emergency', 'consultation', 'follow_up'
    )),
    
    -- Assigned dentist
    dentist_id UUID REFERENCES users(id) ON DELETE SET NULL,
    dentist_name VARCHAR(100),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'scheduled' CHECK (status IN (
        'scheduled', 'confirmed', 'in_progress', 'completed', 
        'cancelled', 'no_show', 'rescheduled'
    )),
    
    -- Additional information
    reason_for_visit TEXT NOT NULL,
    notes TEXT,
    symptoms TEXT[],
    
    -- Reminder tracking
    reminder_sent BOOLEAN DEFAULT false,
    reminder_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Cancellation tracking
    cancelled_by UUID REFERENCES users(id),
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    -- Session tracking (from chatbot)
    chat_session_id UUID,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for appointments table
CREATE INDEX idx_appointments_patient ON appointments(patient_id);
CREATE INDEX idx_appointments_dentist ON appointments(dentist_id);
CREATE INDEX idx_appointments_date ON appointments(appointment_date);
CREATE INDEX idx_appointments_datetime ON appointments(appointment_date, appointment_time);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_appointments_type ON appointments(appointment_type);
CREATE INDEX idx_appointments_chat_session ON appointments(chat_session_id);
CREATE INDEX idx_appointments_upcoming ON appointments(appointment_date, status) 
    WHERE status IN ('scheduled', 'confirmed');

-- Composite index for availability queries
CREATE INDEX idx_appointments_availability ON appointments(appointment_date, appointment_time, dentist_id, status);

-- ================================================================
-- 3. CHAT SESSIONS TABLE
-- Stores conversation logs and metadata for analytics
-- ================================================================

CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User information
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(50),
    
    -- Session metadata
    session_token VARCHAR(255) UNIQUE,
    ip_address INET,
    user_agent TEXT,
    
    -- Conversation metrics
    message_count INTEGER DEFAULT 0,
    total_tokens_used INTEGER DEFAULT 0,
    
    -- Session status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'ended', 'timeout', 'error')),
    
    -- Intent tracking (what user was trying to do)
    primary_intent VARCHAR(50) CHECK (primary_intent IN (
        'appointment_scheduling', 'service_inquiry', 'office_hours', 
        'pricing', 'insurance', 'emergency', 'general_question', 'other'
    )),
    intent_confidence DECIMAL(3, 2),
    
    -- Outcome tracking
    appointment_created BOOLEAN DEFAULT false,
    appointment_id UUID REFERENCES appointments(id),
    user_satisfied BOOLEAN,
    feedback_rating INTEGER CHECK (feedback_rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP WITH TIME ZONE,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Session duration in seconds
    duration_seconds INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (COALESCE(ended_at, CURRENT_TIMESTAMP) - started_at))::INTEGER
    ) STORED
);

-- Indexes for chat_sessions table
CREATE INDEX idx_chat_sessions_user ON chat_sessions(user_id);
CREATE INDEX idx_chat_sessions_token ON chat_sessions(session_token);
CREATE INDEX idx_chat_sessions_started ON chat_sessions(started_at DESC);
CREATE INDEX idx_chat_sessions_status ON chat_sessions(status);
CREATE INDEX idx_chat_sessions_intent ON chat_sessions(primary_intent);
CREATE INDEX idx_chat_sessions_appointment ON chat_sessions(appointment_id);
CREATE INDEX idx_chat_sessions_active ON chat_sessions(last_activity_at DESC) 
    WHERE status = 'active';

-- ================================================================
-- 4. CHAT MESSAGES TABLE
-- Stores individual messages for detailed analytics
-- ================================================================

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Session reference
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    
    -- Message details
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'bot', 'system')),
    message_text TEXT NOT NULL,
    
    -- Metadata
    tokens_used INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    llm_model VARCHAR(50),
    
    -- Intent analysis
    detected_intent VARCHAR(50),
    intent_confidence DECIMAL(3, 2),
    entities JSONB,
    
    -- Error tracking
    error_occurred BOOLEAN DEFAULT false,
    error_message TEXT,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Message sequence in session
    sequence_number INTEGER NOT NULL
);

-- Indexes for chat_messages table
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX idx_chat_messages_role ON chat_messages(role);
CREATE INDEX idx_chat_messages_created ON chat_messages(created_at DESC);
CREATE INDEX idx_chat_messages_session_sequence ON chat_messages(session_id, sequence_number);
CREATE INDEX idx_chat_messages_intent ON chat_messages(detected_intent);
CREATE INDEX idx_chat_messages_entities ON chat_messages USING gin(entities);

-- ================================================================
-- 5. AUDIT LOG TABLE
-- Tracks all system actions for security and compliance
-- ================================================================

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Actor information
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    username VARCHAR(50),
    
    -- Action details
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    
    -- Request details
    ip_address INET,
    user_agent TEXT,
    request_method VARCHAR(10),
    request_path TEXT,
    
    -- Change tracking
    old_values JSONB,
    new_values JSONB,
    
    -- Status
    status VARCHAR(20) CHECK (status IN ('success', 'failure', 'error')),
    error_message TEXT,
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit_log table
CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);
CREATE INDEX idx_audit_log_created ON audit_log(created_at DESC);
CREATE INDEX idx_audit_log_status ON audit_log(status);

-- ================================================================
-- TRIGGERS
-- ================================================================

-- Update updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ================================================================
-- VIEWS FOR ANALYTICS
-- ================================================================

-- Active appointments view
CREATE VIEW v_upcoming_appointments AS
SELECT 
    a.*,
    u.full_name as patient_full_name,
    u.phone as patient_phone_number,
    u.email as patient_email_address
FROM appointments a
JOIN users u ON a.patient_id = u.id
WHERE a.appointment_date >= CURRENT_DATE
    AND a.status IN ('scheduled', 'confirmed')
ORDER BY a.appointment_date, a.appointment_time;

-- Chat analytics view
CREATE VIEW v_chat_analytics AS
SELECT 
    DATE(cs.started_at) as date,
    COUNT(*) as total_sessions,
    COUNT(*) FILTER (WHERE cs.appointment_created = true) as appointments_created,
    AVG(cs.message_count) as avg_messages_per_session,
    AVG(cs.duration_seconds) as avg_duration_seconds,
    AVG(cs.feedback_rating) as avg_rating,
    COUNT(*) FILTER (WHERE cs.primary_intent = 'appointment_scheduling') as appointment_intents,
    COUNT(*) FILTER (WHERE cs.primary_intent = 'service_inquiry') as service_inquiries
FROM chat_sessions cs
GROUP BY DATE(cs.started_at)
ORDER BY date DESC;

-- Daily appointment statistics
CREATE VIEW v_daily_appointment_stats AS
SELECT 
    appointment_date,
    COUNT(*) as total_appointments,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
    COUNT(*) FILTER (WHERE status = 'no_show') as no_shows,
    COUNT(DISTINCT patient_id) as unique_patients,
    COUNT(DISTINCT appointment_type) as different_types
FROM appointments
GROUP BY appointment_date
ORDER BY appointment_date DESC;

-- ================================================================
-- SAMPLE DATA INSERTIONS
-- ================================================================

-- Insert sample users (passwords are bcrypt hashed versions of 'demo123' and 'admin123')
INSERT INTO users (username, email, password_hash, full_name, phone, role) VALUES
('demo', 'demo@example.com', '$2b$12$hLUsVYTWOIBfIM8Qrx8Nh.wzP6wCGbat5OpwULDYp5KV/6PP4vki2', 'Demo User', '555-0101', 'patient'),
('admin', 'admin@example.com', '$2b$12$t/OvQZ/qKMQR5mfbiliW2uAtfHIRjdEb5HQ55W1CJgtLRjZE6dWhe', 'Admin User', '555-0100', 'admin'),
('dr_smith', 'dr.smith@dental.com', '$2b$12$hLUsVYTWOIBfIM8Qrx8Nh.wzP6wCGbat5OpwULDYp5KV/6PP4vki2', 'Dr. Sarah Smith', '555-0201', 'dentist'),
('dr_jones', 'dr.jones@dental.com', '$2b$12$hLUsVYTWOIBfIM8Qrx8Nh.wzP6wCGbat5OpwULDYp5KV/6PP4vki2', 'Dr. Michael Jones', '555-0202', 'dentist'),
('john_doe', 'john.doe@email.com', '$2b$12$hLUsVYTWOIBfIM8Qrx8Nh.wzP6wCGbat5OpwULDYp5KV/6PP4vki2', 'John Doe', '555-1001', 'patient'),
('jane_smith', 'jane.smith@email.com', '$2b$12$hLUsVYTWOIBfIM8Qrx8Nh.wzP6wCGbat5OpwULDYp5KV/6PP4vki2', 'Jane Smith', '555-1002', 'patient');

-- Insert sample appointments
INSERT INTO appointments (patient_id, patient_name, patient_email, patient_phone, appointment_date, appointment_time, 
    appointment_type, dentist_id, dentist_name, status, reason_for_visit) 
SELECT 
    (SELECT id FROM users WHERE username = 'demo'),
    'Demo User',
    'demo@example.com',
    '555-0101',
    CURRENT_DATE + INTERVAL '3 days',
    '10:00:00',
    'checkup',
    (SELECT id FROM users WHERE username = 'dr_smith'),
    'Dr. Sarah Smith',
    'scheduled',
    'Regular 6-month checkup';

INSERT INTO appointments (patient_id, patient_name, patient_email, patient_phone, appointment_date, appointment_time, 
    appointment_type, dentist_id, dentist_name, status, reason_for_visit) 
SELECT 
    (SELECT id FROM users WHERE username = 'john_doe'),
    'John Doe',
    'john.doe@email.com',
    '555-1001',
    CURRENT_DATE + INTERVAL '5 days',
    '14:00:00',
    'cleaning',
    (SELECT id FROM users WHERE username = 'dr_jones'),
    'Dr. Michael Jones',
    'confirmed',
    'Teeth cleaning and fluoride treatment';

INSERT INTO appointments (patient_id, patient_name, patient_email, patient_phone, appointment_date, appointment_time, 
    appointment_type, dentist_id, dentist_name, status, reason_for_visit) 
SELECT 
    (SELECT id FROM users WHERE username = 'jane_smith'),
    'Jane Smith',
    'jane.smith@email.com',
    '555-1002',
    CURRENT_DATE - INTERVAL '2 days',
    '15:30:00',
    'filling',
    (SELECT id FROM users WHERE username = 'dr_smith'),
    'Dr. Sarah Smith',
    'completed',
    'Cavity filling on lower left molar';

-- Insert sample chat sessions
INSERT INTO chat_sessions (user_id, username, session_token, message_count, status, primary_intent, appointment_created)
SELECT 
    (SELECT id FROM users WHERE username = 'demo'),
    'demo',
    'session_' || uuid_generate_v4(),
    8,
    'ended',
    'appointment_scheduling',
    true;

INSERT INTO chat_sessions (user_id, username, session_token, message_count, status, primary_intent, feedback_rating)
SELECT 
    (SELECT id FROM users WHERE username = 'john_doe'),
    'john_doe',
    'session_' || uuid_generate_v4(),
    5,
    'ended',
    'service_inquiry',
    5;

-- ================================================================
-- UTILITY FUNCTIONS
-- ================================================================

-- Function to get available appointment slots
CREATE OR REPLACE FUNCTION get_available_slots(
    p_date DATE,
    p_dentist_id UUID DEFAULT NULL
)
RETURNS TABLE (
    slot_time TIME,
    dentist_id UUID,
    dentist_name VARCHAR
) AS $$
DECLARE
    start_time TIME := '08:00:00';
    end_time TIME := '18:00:00';
    slot_duration INTERVAL := '30 minutes';
    current_slot TIME;
BEGIN
    current_slot := start_time;
    
    WHILE current_slot < end_time LOOP
        RETURN QUERY
        SELECT 
            current_slot,
            u.id,
            u.full_name
        FROM users u
        WHERE u.role = 'dentist'
            AND u.is_active = true
            AND (p_dentist_id IS NULL OR u.id = p_dentist_id)
            AND NOT EXISTS (
                SELECT 1 FROM appointments a
                WHERE a.dentist_id = u.id
                    AND a.appointment_date = p_date
                    AND a.appointment_time = current_slot
                    AND a.status NOT IN ('cancelled', 'no_show')
            );
        
        current_slot := current_slot + slot_duration;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- COMMENTS
-- ================================================================

COMMENT ON TABLE users IS 'Stores user profiles and authentication information';
COMMENT ON TABLE appointments IS 'Stores appointment scheduling data and status';
COMMENT ON TABLE chat_sessions IS 'Stores conversation sessions and analytics metadata';
COMMENT ON TABLE chat_messages IS 'Stores individual chat messages for detailed analysis';
COMMENT ON TABLE audit_log IS 'Tracks all system actions for security and compliance';

COMMENT ON COLUMN users.allergies IS 'Array of known allergies';
COMMENT ON COLUMN appointments.symptoms IS 'Array of reported symptoms';
COMMENT ON COLUMN chat_messages.entities IS 'JSON object containing extracted entities like dates, names, etc.';

-- ================================================================
-- GRANT PERMISSIONS
-- ================================================================

-- Grant appropriate permissions to application user
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO dental_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO dental_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO dental_user;

-- ================================================================
-- COMPLETION MESSAGE
-- ================================================================

DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Dental Chatbot Database initialized successfully!';
    RAISE NOTICE 'Database: dental_chatbot';
    RAISE NOTICE 'Sample users created: demo, admin, dr_smith, dr_jones';
    RAISE NOTICE 'Sample appointments created: 3';
    RAISE NOTICE 'Sample chat sessions created: 2';
    RAISE NOTICE '========================================';
END $$;

