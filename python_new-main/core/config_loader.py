"""
Configuration Loader
Loads configuration from YAML files and provides typed access to settings
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Centralized configuration management"""
    
    def __init__(self, config_file: str = "config/agent_config.yml"):
        """
        Initialize configuration loader
        
        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                logger.warning(f"Configuration file {self.config_file} not found, using defaults")
                self._load_default_config()
                return
            
            with open(config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file) or {}
            
            logger.info(f"Configuration loaded from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._load_default_config()
    
    def _load_default_config(self):
        """Load default configuration as fallback"""
        self.config = {
            "agent_registry": {
                "agents_directory": "agents",
                "auto_discovery": True,
                "minimum_confidence_threshold": 0.3,
                "max_agents_per_query": 5
            },
            "memory": {
                "stm_default_expiry_hours": 1,
                "ltm_retention_days": 365,
                "vector_search_limit": 10,
                "cross_agent_search_enabled": True
            },
            "orchestration": {
                "default_strategy": "auto_select_best_agent",
                "fallback_agent": "ScenicLocationFinder",
                "enable_multi_agent": False,
                "max_execution_time_seconds": 30
            },
            "llm": {
                "default_temperature": 0.7,
                "max_tokens": 2000,
                "timeout_seconds": 30,
                "enable_context_memory": True
            },
            "api": {
                "enable_authentication": False,
                "rate_limiting": False,
                "cors_enabled": True,
                "max_request_size_mb": 10
            },
            "logging": {
                "level": "INFO",
                "log_agent_interactions": True,
                "log_memory_operations": True,
                "log_search_queries": True
            }
        }
        logger.info("Using default configuration")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated path (e.g., 'agent_registry.auto_discovery')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """Get configuration for a specific agent"""
        return self.get(f"agents.{agent_name}", {})
    
    def get_agent_temperature(self, agent_name: str) -> float:
        """Get temperature setting for an agent"""
        agent_config = self.get_agent_config(agent_name)
        return agent_config.get("temperature", self.get("llm.default_temperature", 0.7))
    
    def get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Get capabilities for an agent"""
        agent_config = self.get_agent_config(agent_name)
        return agent_config.get("capabilities", [])
    
    def get_agent_keywords(self, agent_name: str) -> List[str]:
        """Get keywords for an agent"""
        agent_config = self.get_agent_config(agent_name)
        return agent_config.get("keywords", [])
    
    def get_registry_config(self) -> Dict[str, Any]:
        """Get agent registry configuration"""
        return self.get("agent_registry", {})
    
    def get_memory_config(self) -> Dict[str, Any]:
        """Get memory configuration"""
        return self.get("memory", {})
    
    def get_orchestration_config(self) -> Dict[str, Any]:
        """Get orchestration configuration"""
        return self.get("orchestration", {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.get("llm", {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration"""
        return self.get("api", {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get("logging", {})
    
    def reload_config(self):
        """Reload configuration from file"""
        logger.info("Reloading configuration...")
        self._load_config()
    
    def update_config(self, key_path: str, value: Any):
        """
        Update a configuration value
        
        Args:
            key_path: Dot-separated path
            value: New value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the final value
        config[keys[-1]] = value
        logger.info(f"Updated configuration: {key_path} = {value}")
    
    def save_config(self, output_file: str = None):
        """Save current configuration to file"""
        output_file = output_file or self.config_file
        
        try:
            # Ensure directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as file:
                yaml.safe_dump(self.config, file, default_flow_style=False, indent=2)
            
            logger.info(f"Configuration saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-style access"""
        return self.get(key)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists"""
        return self.get(key) is not None


# Global configuration instance
config = ConfigLoader()


def get_config() -> ConfigLoader:
    """Get the global configuration instance"""
    return config


def reload_config():
    """Reload global configuration"""
    global config
    config.reload_config()
