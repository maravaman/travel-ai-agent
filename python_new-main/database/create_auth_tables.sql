-- =============================================
-- User Authentication Database Schema
-- =============================================
USE langgraph_ai_system;

-- Users table - stores user accounts
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    profile_data JSON DEFAULT NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- User sessions table - tracks active sessions
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    ip_address VARCHAR(45) NULL,
    user_agent TEXT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);

-- User activity log - tracks all user interactions
CREATE TABLE IF NOT EXISTS user_activity (
    activity_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id VARCHAR(255) NULL,
    activity_type ENUM('login', 'logout', 'query', 'register') NOT NULL,
    activity_data JSON DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45) NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_activity_type (activity_type)
);

-- User query history - detailed query tracking
CREATE TABLE IF NOT EXISTS user_queries (
    query_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_id VARCHAR(255) NULL,
    question TEXT NOT NULL,
    agent_used VARCHAR(100) NOT NULL,
    response_text LONGTEXT NOT NULL,
    edges_traversed JSON DEFAULT NULL,
    processing_time DECIMAL(10,3) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES user_sessions(session_id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    INDEX idx_agent_used (agent_used),
    FULLTEXT INDEX idx_question_response (question, response_text)
);

-- Update existing LTM table to include user_id reference  
-- (Skip if ltm table doesn't exist yet)
SET @exist := (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'langgraph_ai_system' AND table_name = 'ltm');
SET @sqlstmt := IF(@exist > 0, 'ALTER TABLE ltm ADD COLUMN IF NOT EXISTS user_id INT NULL', 'SELECT "LTM table not found, skipping" as Status');
PREPARE stmt FROM @sqlstmt;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Clean up expired sessions automatically
CREATE EVENT IF NOT EXISTS cleanup_expired_sessions
ON SCHEDULE EVERY 1 HOUR
DO
  DELETE FROM user_sessions WHERE expires_at < NOW();

-- Sample default admin user (password: admin123)
INSERT IGNORE INTO users (username, email, hashed_password, is_active) VALUES
('admin', 'admin@langgraph.local', '$2b$12$rQZYjKyJzGkYYX.jZvB1VebZe4qJZGYjXJ6W3Qx.2x1FGr2vNjh5e', TRUE);

-- Display created tables
SHOW TABLES;

SELECT 'Database schema created successfully!' as Status;
