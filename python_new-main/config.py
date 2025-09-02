"""
Configuration Management System
Centralized configuration with environment variables and validation
"""

import os
from typing import Optional
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")

class Config:
    """Centralized configuration class"""
    
    # Application Settings
    APP_HOST: str = os.getenv('APP_HOST', 'localhost')
    APP_PORT: int = int(os.getenv('APP_PORT', '8000'))
    DEBUG: bool = os.getenv('DEBUG', 'False').lower() == 'true'
    APP_TITLE: str = os.getenv('APP_TITLE', 'Travel Assistant - Multi-Agent System')
    APP_DESCRIPTION: str = os.getenv('APP_DESCRIPTION', 'AI-powered travel planning assistant with specialized agents')
    APP_VERSION: str = os.getenv('APP_VERSION', '3.0.0-travel')
    
    # Security Settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'change-this-secret-key-in-production')
    ALGORITHM: str = os.getenv('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '480'))
    
    # Database Configuration
    MYSQL_HOST: str = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER: str = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD: str = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE: str = os.getenv('MYSQL_DATABASE', 'travel_assistant')
    MYSQL_PORT: int = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_CONNECT_TIMEOUT: int = int(os.getenv('MYSQL_CONNECT_TIMEOUT', '10'))
    MYSQL_CHARSET: str = os.getenv('MYSQL_CHARSET', 'utf8mb4')
    
    # Redis Configuration
    REDIS_HOST: str = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT: int = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_DB: int = int(os.getenv('REDIS_DB', '0'))
    REDIS_SOCKET_TIMEOUT: int = int(os.getenv('REDIS_SOCKET_TIMEOUT', '5'))
    REDIS_SOCKET_CONNECT_TIMEOUT: int = int(os.getenv('REDIS_SOCKET_CONNECT_TIMEOUT', '5'))
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_DEFAULT_MODEL: str = os.getenv('OLLAMA_DEFAULT_MODEL', 'llama3:latest')
    OLLAMA_TIMEOUT: int = int(os.getenv('OLLAMA_TIMEOUT', '30'))  # Optimized for travel assistant
    OLLAMA_CONNECTION_TIMEOUT: int = int(os.getenv('OLLAMA_CONNECTION_TIMEOUT', '10'))  # Connection timeout
    OLLAMA_READ_TIMEOUT: int = int(os.getenv('OLLAMA_READ_TIMEOUT', '30'))  # Read timeout for responses
    OLLAMA_MAX_RETRIES: int = int(os.getenv('OLLAMA_MAX_RETRIES', '3'))  # Number of retry attempts
    OLLAMA_RETRY_DELAY: float = float(os.getenv('OLLAMA_RETRY_DELAY', '2.0'))  # Initial retry delay in seconds
    OLLAMA_MAX_TOKENS: int = int(os.getenv('OLLAMA_MAX_TOKENS', '2000'))
    OLLAMA_TEMPERATURE: float = float(os.getenv('OLLAMA_TEMPERATURE', '0.7'))
    
    # Travel Agent Configuration
    TRAVEL_CHAT_SLA_SECONDS: int = int(os.getenv('TRAVEL_CHAT_SLA_SECONDS', '3'))
    TRAVEL_BATCH_SLA_SECONDS: int = int(os.getenv('TRAVEL_BATCH_SLA_SECONDS', '60'))
    TRAVEL_MAX_AGENTS_CHAT: int = int(os.getenv('TRAVEL_MAX_AGENTS_CHAT', '3'))
    TRAVEL_MAX_AGENTS_BATCH: int = int(os.getenv('TRAVEL_MAX_AGENTS_BATCH', '6'))
    TRAVEL_SESSION_TIMEOUT_MINUTES: int = int(os.getenv('TRAVEL_SESSION_TIMEOUT_MINUTES', '60'))
    
    # UI Configuration
    STATIC_DIR: str = os.getenv('STATIC_DIR', 'static')
    TEMPLATES_DIR: str = os.getenv('TEMPLATES_DIR', 'templates')
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: Optional[str] = os.getenv('LOG_FILE')
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate critical configuration values"""
        issues = []
        
        # Check critical settings
        if cls.SECRET_KEY == 'change-this-secret-key-in-production':
            issues.append("⚠️ SECRET_KEY is using default value - change in production!")
        
        if not cls.MYSQL_DATABASE:
            issues.append("❌ MYSQL_DATABASE is required")
            
        if not cls.OLLAMA_BASE_URL:
            issues.append("❌ OLLAMA_BASE_URL is required")
            
        # Check port ranges
        if not (1 <= cls.APP_PORT <= 65535):
            issues.append(f"❌ APP_PORT {cls.APP_PORT} is not a valid port number")
            
        if not (1 <= cls.MYSQL_PORT <= 65535):
            issues.append(f"❌ MYSQL_PORT {cls.MYSQL_PORT} is not a valid port number")
            
        if not (1 <= cls.REDIS_PORT <= 65535):
            issues.append(f"❌ REDIS_PORT {cls.REDIS_PORT} is not a valid port number")
        
        # Report issues
        if issues:
            print("⚠️ Configuration Issues Found:")
            for issue in issues:
                print(f"   {issue}")
            return False
        
        print("✅ Configuration validation passed")
        return True
    
    @classmethod
    def get_mysql_connection_params(cls) -> dict:
        """Get MySQL connection parameters"""
        return {
            'host': cls.MYSQL_HOST,
            'user': cls.MYSQL_USER,
            'password': cls.MYSQL_PASSWORD,
            'database': cls.MYSQL_DATABASE,
            'port': cls.MYSQL_PORT,
            'connect_timeout': cls.MYSQL_CONNECT_TIMEOUT,
            'charset': cls.MYSQL_CHARSET,
            'autocommit': True
        }
    
    @classmethod
    def get_redis_connection_params(cls) -> dict:
        """Get Redis connection parameters"""
        return {
            'host': cls.REDIS_HOST,
            'port': cls.REDIS_PORT,
            'db': cls.REDIS_DB,
            'decode_responses': True,
            'socket_timeout': cls.REDIS_SOCKET_TIMEOUT,
            'socket_connect_timeout': cls.REDIS_SOCKET_CONNECT_TIMEOUT
        }
    
    @classmethod
    def get_ollama_config(cls) -> dict:
        """Get Ollama configuration"""
        return {
            'base_url': cls.OLLAMA_BASE_URL,
            'default_model': cls.OLLAMA_DEFAULT_MODEL,
            'timeout': cls.OLLAMA_TIMEOUT,
            'connection_timeout': cls.OLLAMA_CONNECTION_TIMEOUT,
            'read_timeout': cls.OLLAMA_READ_TIMEOUT,
            'max_retries': cls.OLLAMA_MAX_RETRIES,
            'retry_delay': cls.OLLAMA_RETRY_DELAY,
            'max_tokens': cls.OLLAMA_MAX_TOKENS,
            'temperature': cls.OLLAMA_TEMPERATURE
        }
    
    @classmethod
    def display_config(cls) -> None:
        """Display current configuration (without sensitive data)"""
        print("📋 Current Configuration:")
        print(f"   App: {cls.APP_HOST}:{cls.APP_PORT} (Debug: {cls.DEBUG})")
        print(f"   Database: {cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}")
        print(f"   Redis: {cls.REDIS_HOST}:{cls.REDIS_PORT}")
        print(f"   Ollama: {cls.OLLAMA_BASE_URL} (Model: {cls.OLLAMA_DEFAULT_MODEL})")
        print(f"   Token Expire: {cls.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")

# Initialize configuration and validate
config = Config()

if __name__ == "__main__":
    # Test configuration
    config.display_config()
    config.validate_config()
