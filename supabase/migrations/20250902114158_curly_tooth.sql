-- Travel Assistant Database Schema
-- Enhanced schema for travel-specific functionality

USE travel_assistant;

-- User Travel Profiles table
CREATE TABLE IF NOT EXISTS user_travel_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    destinations_of_interest JSON DEFAULT NULL,
    cuisine_preferences JSON DEFAULT NULL,
    climate_tolerance JSON DEFAULT NULL,
    travel_pace ENUM('relaxed', 'balanced', 'packed') DEFAULT 'balanced',
    behavioral_notes JSON DEFAULT NULL,
    budget_patterns JSON DEFAULT NULL,
    group_preferences JSON DEFAULT NULL,
    activity_preferences JSON DEFAULT NULL,
    accommodation_preferences JSON DEFAULT NULL,
    profile_version VARCHAR(10) DEFAULT '1.0',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_profile (user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_updated_at (updated_at)
);

-- Travel Sessions table
CREATE TABLE IF NOT EXISTS travel_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    title VARCHAR(255) DEFAULT NULL,
    mode ENUM('chat', 'recording') NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP NULL,
    turn_count INT DEFAULT 0,
    total_processing_time DECIMAL(10,3) DEFAULT 0,
    agents_used JSON DEFAULT NULL,
    session_metadata JSON DEFAULT NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_started_at (started_at)
);

-- Travel Turns table (individual interactions)
CREATE TABLE IF NOT EXISTS travel_turns (
    id INT PRIMARY KEY AUTO_INCREMENT,
    turn_id VARCHAR(255) UNIQUE NOT NULL,
    session_id VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    role ENUM('user', 'assistant', 'agent') NOT NULL,
    agent_name VARCHAR(100) NULL,
    text LONGTEXT NOT NULL,
    processing_time DECIMAL(10,3) NULL,
    turn_metadata JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES travel_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_turn_id (turn_id),
    INDEX idx_created_at (created_at)
);

-- Travel Agent Executions table (for logging and analytics)
CREATE TABLE IF NOT EXISTS travel_agent_executions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    execution_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    session_id VARCHAR(255) NULL,
    agent_name VARCHAR(100) NOT NULL,
    query_text TEXT NOT NULL,
    response_text LONGTEXT NOT NULL,
    processing_time DECIMAL(10,3) NOT NULL,
    execution_order INT DEFAULT 1,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT NULL,
    execution_metadata JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES travel_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_agent_name (agent_name),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    INDEX idx_success (success)
);

-- Travel Insights table (extracted insights for analytics)
CREATE TABLE IF NOT EXISTS travel_insights (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    insight_type ENUM('destination', 'preference', 'constraint', 'goal', 'mood', 'behavior') NOT NULL,
    insight_value VARCHAR(255) NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.5,
    source_session VARCHAR(255) NULL,
    source_agent VARCHAR(100) NULL,
    insight_metadata JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_session) REFERENCES travel_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_insight_type (insight_type),
    INDEX idx_created_at (created_at)
);

-- Update existing tables to support travel functionality
-- Add travel-specific columns to existing agent_interactions table
ALTER TABLE agent_interactions 
ADD COLUMN IF NOT EXISTS travel_session_id VARCHAR(255) NULL,
ADD COLUMN IF NOT EXISTS travel_mode ENUM('chat', 'recording') NULL,
ADD COLUMN IF NOT EXISTS travel_metadata JSON DEFAULT NULL;

-- Add travel-specific indexes
CREATE INDEX IF NOT EXISTS idx_travel_session ON agent_interactions(travel_session_id);
CREATE INDEX IF NOT EXISTS idx_travel_mode ON agent_interactions(travel_mode);

-- Insert sample travel profile for testing
INSERT IGNORE INTO user_travel_profiles (user_id, destinations_of_interest, activity_preferences, travel_pace) 
VALUES (1000, '["Paris", "Tokyo", "New York"]', '["culture", "food", "photography"]', 'balanced');

-- Create views for analytics
CREATE OR REPLACE VIEW travel_analytics AS
SELECT 
    u.user_id,
    COUNT(DISTINCT s.session_id) as total_sessions,
    COUNT(DISTINCT t.turn_id) as total_turns,
    COUNT(DISTINCT e.agent_name) as agents_used,
    AVG(e.processing_time) as avg_processing_time,
    MAX(s.started_at) as last_session,
    p.travel_pace,
    JSON_LENGTH(p.destinations_of_interest) as destinations_count
FROM user_travel_profiles p
LEFT JOIN travel_sessions s ON p.user_id = s.user_id
LEFT JOIN travel_turns t ON s.session_id = t.session_id
LEFT JOIN travel_agent_executions e ON s.session_id = e.session_id
GROUP BY u.user_id;

SELECT 'Travel Assistant database schema created successfully!' as Status;