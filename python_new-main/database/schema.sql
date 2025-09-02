-- Database schema for LangGraph AI System

CREATE DATABASE IF NOT EXISTS `langgraph_ai_system`;
USE `langgraph_ai_system`;

-- Users table for authentication
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `username` VARCHAR(50) UNIQUE NOT NULL,
    `email` VARCHAR(100) UNIQUE NOT NULL,
    `hashed_password` VARCHAR(255) NOT NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `last_login` TIMESTAMP NULL,
    INDEX idx_username (username),
    INDEX idx_email (email)
);

-- User sessions for tracking recent usage
CREATE TABLE IF NOT EXISTS `user_sessions` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `session_token` VARCHAR(255) NOT NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `expires_at` TIMESTAMP NOT NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_token (session_token)
);

-- Agent interactions history
CREATE TABLE IF NOT EXISTS `agent_interactions` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `agent_name` VARCHAR(100) NOT NULL,
    `query` TEXT NOT NULL,
    `response` TEXT NOT NULL,
    `interaction_type` ENUM('single', 'orchestrated') DEFAULT 'single',
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_agent (user_id, agent_name),
    INDEX idx_timestamp (timestamp),
    INDEX idx_agent_name (agent_name)
);

-- Long-term memory grouped by agent
CREATE TABLE IF NOT EXISTS `ltm_by_agent` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `agent_name` VARCHAR(100) NOT NULL,
    `user_id` INT NOT NULL,
    `memory_key` VARCHAR(255) NOT NULL,
    `memory_value` TEXT NOT NULL,
    `context_metadata` JSON,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_agent_user_key (agent_name, user_id, memory_key),
    INDEX idx_agent_name (agent_name),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- Vector embeddings storage for similarity search
CREATE TABLE IF NOT EXISTS `vector_embeddings` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `agent_name` VARCHAR(100) NOT NULL,
    `content` TEXT NOT NULL,
    `embedding` JSON NOT NULL,
    `metadata` JSON,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_agent (user_id, agent_name),
    INDEX idx_created_at (created_at)
);

-- Agent configurations - dynamic nodes and edges
CREATE TABLE IF NOT EXISTS `agent_configurations` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `agent_name` VARCHAR(100) UNIQUE NOT NULL,
    `module_path` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `capabilities` JSON,
    `dependencies` JSON,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_agent_name (agent_name),
    INDEX idx_is_active (is_active)
);

-- Graph edges configuration
CREATE TABLE IF NOT EXISTS `graph_edges` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `source_agent` VARCHAR(100) NOT NULL,
    `target_agent` VARCHAR(100) NOT NULL,
    `condition` TEXT,
    `weight` INT DEFAULT 1,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_edge (source_agent, target_agent),
    INDEX idx_source_agent (source_agent),
    INDEX idx_target_agent (target_agent),
    INDEX idx_is_active (is_active)
);

-- Usage analytics
CREATE TABLE IF NOT EXISTS `usage_analytics` (
    `id` INT PRIMARY KEY AUTO_INCREMENT,
    `user_id` INT NOT NULL,
    `agent_name` VARCHAR(100) NOT NULL,
    `query_type` VARCHAR(50),
    `execution_time_ms` INT,
    `success` BOOLEAN DEFAULT TRUE,
    `timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_agent_name (agent_name),
    INDEX idx_timestamp (timestamp)
);

-- Insert default agent configurations
INSERT INTO `agent_configurations` (`agent_name`, `module_path`, `description`, `capabilities`, `dependencies`) VALUES
('SearchAgent', 'core.agents.search_agent', 'Vector-based similarity search agent for history matching', '["similarity_search", "vector_embedding", "json_response"]', '[]'),
('ScenicLocationFinder', 'core.plugins.scenic_agent', 'Finds scenic locations based on user preferences', '["location_search", "scenic_analysis"]', '[]'),
('ForestAnalyzer', 'core.plugins.forest_analyzer', 'Analyzes forest data and characteristics', '["forest_analysis", "environmental_data"]', '[]'),
('WaterBodyAnalyzer', 'core.plugins.waterbody_analyzer', 'Analyzes water bodies and related information', '["water_analysis", "hydrology"]', '[]'),
('OrchestratorAgent', 'core.agents.orchestrator_agent', 'Intelligently routes queries to appropriate agents', '["query_routing", "multi_agent_coordination"]', '[]');

-- Insert default graph edges
INSERT INTO `graph_edges` (`source_agent`, `target_agent`, `condition`, `weight`) VALUES
('OrchestratorAgent', 'SearchAgent', 'search_required', 1),
('OrchestratorAgent', 'ScenicLocationFinder', 'scenic_query', 1),
('OrchestratorAgent', 'ForestAnalyzer', 'forest_query', 1),
('OrchestratorAgent', 'WaterBodyAnalyzer', 'water_query', 1),
('ScenicLocationFinder', 'WaterBodyAnalyzer', 'water_nearby', 2),
('ForestAnalyzer', 'ScenicLocationFinder', 'scenic_forest', 2);
