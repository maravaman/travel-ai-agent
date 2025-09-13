"""
Dynamic Agent Loader using Reflection and JSON Configuration
Dynamically loads and executes .py agent files based on JSON configuration
"""

import json
import importlib
import importlib.util
import inspect
import logging
import os
import sys
from typing import Dict, Any, List, Optional, Type, Callable
from pathlib import Path
from datetime import datetime

from core.base_agent import BaseAgent, GraphState
from core.memory import MemoryManager

logger = logging.getLogger(__name__)


class DynamicAgentLoader:
    """
    Dynamic agent loader that uses reflection to load .py files from JSON configuration
    Supports both module imports and direct file execution
    """
    
    def __init__(self, config_file: str = "core/dynamic_agents.json", memory_manager: MemoryManager = None):
        """
        Initialize dynamic agent loader
        
        Args:
            config_file: Path to JSON configuration file
            memory_manager: Shared memory manager instance
        """
        self.config_file = config_file
        self.memory_manager = memory_manager
        self.loaded_agents: Dict[str, BaseAgent] = {}
        self.agent_modules: Dict[str, Any] = {}
        self.execution_log: List[Dict[str, Any]] = []
        
        # Load configuration
        self.config = self._load_config()
        
        # Initialize agents from configuration
        self._initialize_agents()
        
        logger.info(f"DynamicAgentLoader initialized with {len(self.loaded_agents)} agents")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from JSON file"""
        try:
            config_path = Path(self.config_file)
            if not config_path.exists():
                logger.warning(f"Configuration file {self.config_file} not found, creating default")
                self._create_default_config()
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"Loaded configuration from {self.config_file}")
            return config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return self._get_default_config()
    
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = self._get_default_config()
        
        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"Created default configuration at {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to create default configuration: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure"""
        return {
            "version": "1.0.0",
            "description": "Dynamic Agent Configuration for Travel Assistant",
            "agents": [
                {
                    "name": "TextTripAnalyzer",
                    "file_path": "agents/text_trip_analyzer.py",
                    "class_name": "TextTripAnalyzerAgent",
                    "enabled": True,
                    "priority": 1,
                    "entry_point": "main",
                    "description": "Analyzes trip planning text to extract goals and constraints",
                    "capabilities": ["text_analysis", "goal_extraction", "constraint_identification"],
                    "keywords": ["plan", "trip", "travel", "vacation", "goal", "constraint"]
                },
                {
                    "name": "TripMoodDetector", 
                    "file_path": "agents/trip_mood_detector.py",
                    "class_name": "TripMoodDetectorAgent",
                    "enabled": True,
                    "priority": 2,
                    "entry_point": "main",
                    "description": "Detects emotional states in travel planning conversations",
                    "capabilities": ["mood_detection", "emotion_analysis", "stress_identification"],
                    "keywords": ["excited", "nervous", "stressed", "worried", "feeling"]
                },
                {
                    "name": "TripCommsCoach",
                    "file_path": "agents/trip_comms_coach.py", 
                    "class_name": "TripCommsCoachAgent",
                    "enabled": True,
                    "priority": 2,
                    "entry_point": "main",
                    "description": "Provides communication tips for travel interactions",
                    "capabilities": ["communication_coaching", "phrasing_suggestions"],
                    "keywords": ["communicate", "talk", "ask", "hotel", "guide"]
                },
                {
                    "name": "TripBehaviorGuide",
                    "file_path": "agents/trip_behavior_guide.py",
                    "class_name": "TripBehaviorGuideAgent", 
                    "enabled": True,
                    "priority": 2,
                    "entry_point": "main",
                    "description": "Provides behavioral guidance and next steps",
                    "capabilities": ["behavioral_guidance", "next_step_planning"],
                    "keywords": ["next", "step", "action", "help", "guide"]
                },
                {
                    "name": "TripCalmPractice",
                    "file_path": "agents/trip_calm_practice.py",
                    "class_name": "TripCalmPracticeAgent",
                    "enabled": True,
                    "priority": 2, 
                    "entry_point": "main",
                    "description": "Provides calming techniques for travel stress",
                    "capabilities": ["stress_relief", "calming_techniques"],
                    "keywords": ["calm", "relax", "stress", "anxiety", "overwhelmed"]
                },
                {
                    "name": "TripSummarySynth",
                    "file_path": "agents/trip_summary_synth.py",
                    "class_name": "TripSummarySynthAgent",
                    "enabled": True,
                    "priority": 1,
                    "entry_point": "main", 
                    "description": "Synthesizes multi-agent outputs and updates profiles",
                    "capabilities": ["response_synthesis", "profile_updating"],
                    "keywords": ["summary", "synthesize", "combine", "profile"]
                }
            ],
            "execution_settings": {
                "max_concurrent_agents": 3,
                "timeout_seconds": 30,
                "retry_attempts": 2,
                "enable_logging": True
            },
            "routing_rules": {
                "default_agent": "TextTripAnalyzer",
                "fallback_agent": "TripSummarySynth",
                "multi_agent_threshold": 2
            }
        }
    
    def _initialize_agents(self):
        """Initialize all enabled agents from configuration"""
        agents_config = self.config.get("agents", [])
        
        for agent_config in agents_config:
            if not agent_config.get("enabled", True):
                logger.info(f"Skipping disabled agent: {agent_config['name']}")
                continue
            
            try:
                agent_instance = self._load_agent_from_config(agent_config)
                if agent_instance:
                    self.loaded_agents[agent_config["name"]] = agent_instance
                    logger.info(f"Successfully loaded agent: {agent_config['name']}")
                else:
                    logger.warning(f"Failed to load agent: {agent_config['name']}")
                    
            except Exception as e:
                logger.error(f"Error loading agent {agent_config['name']}: {e}")
    
    def _load_agent_from_config(self, agent_config: Dict[str, Any]) -> Optional[BaseAgent]:
        """
        Load agent from configuration using reflection
        
        Args:
            agent_config: Agent configuration dictionary
            
        Returns:
            Loaded agent instance or None
        """
        file_path = agent_config["file_path"]
        class_name = agent_config["class_name"]
        agent_name = agent_config["name"]
        
        try:
            # Method 1: Try module import first
            module_path = file_path.replace("/", ".").replace(".py", "")
            try:
                module = importlib.import_module(module_path)
                logger.debug(f"Imported module {module_path} for agent {agent_name}")
            except ImportError:
                # Method 2: Direct file loading using importlib.util
                full_path = Path(file_path)
                if not full_path.exists():
                    logger.error(f"Agent file not found: {file_path}")
                    return None
                
                spec = importlib.util.spec_from_file_location(agent_name, full_path)
                if spec is None or spec.loader is None:
                    logger.error(f"Could not create spec for {file_path}")
                    return None
                
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug(f"Loaded module from file {file_path} for agent {agent_name}")
            
            # Store module reference
            self.agent_modules[agent_name] = module
            
            # Get agent class using reflection
            if hasattr(module, class_name):
                agent_class = getattr(module, class_name)
            else:
                # Try to find any class that inherits from BaseAgent
                agent_class = self._find_agent_class_in_module(module)
                if not agent_class:
                    logger.error(f"No suitable agent class found in {file_path}")
                    return None
            
            # Validate that it's a BaseAgent subclass
            if not (inspect.isclass(agent_class) and issubclass(agent_class, BaseAgent)):
                logger.error(f"Class {class_name} in {file_path} does not inherit from BaseAgent")
                return None
            
            # Create agent instance
            agent_instance = agent_class(memory_manager=self.memory_manager)
            
            # Store additional metadata
            agent_instance._config = agent_config
            agent_instance._loaded_at = datetime.now()
            
            return agent_instance
            
        except Exception as e:
            logger.error(f"Failed to load agent {agent_name} from {file_path}: {e}")
            return None
    
    def _find_agent_class_in_module(self, module) -> Optional[Type[BaseAgent]]:
        """
        Find agent class in module using reflection
        
        Args:
            module: Imported module
            
        Returns:
            Agent class if found, None otherwise
        """
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if (issubclass(obj, BaseAgent) and 
                obj != BaseAgent and 
                obj.__module__ == module.__name__):
                return obj
        return None
    
    def execute_agent(self, agent_name: str, query: str, user_id: int = 0) -> Dict[str, Any]:
        """
        Execute specific agent with query
        
        Args:
            agent_name: Name of agent to execute
            query: Query to process
            user_id: User identifier
            
        Returns:
            Execution result
        """
        if agent_name not in self.loaded_agents:
            return {
                "success": False,
                "error": f"Agent {agent_name} not found",
                "agent": agent_name
            }
        
        try:
            agent = self.loaded_agents[agent_name]
            
            # Create state for agent
            state = GraphState(
                user=f"user_{user_id}",
                user_id=user_id,
                question=query,
                agent=agent_name,
                response=""
            )
            
            # Execute agent
            start_time = datetime.now()
            result_state = agent.process(state)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            # Log execution
            execution_record = {
                "agent": agent_name,
                "query": query,
                "user_id": user_id,
                "success": not result_state.get("error", False),
                "processing_time": processing_time,
                "timestamp": start_time.isoformat(),
                "response_length": len(result_state.get("response", ""))
            }
            self.execution_log.append(execution_record)
            
            return {
                "success": True,
                "agent": agent_name,
                "response": result_state.get("response", ""),
                "processing_time": processing_time,
                "state": result_state,
                "execution_record": execution_record
            }
            
        except Exception as e:
            logger.error(f"Error executing agent {agent_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": agent_name
            }
    
    def execute_multiple_agents(self, agent_names: List[str], query: str, user_id: int = 0) -> Dict[str, Any]:
        """
        Execute multiple agents with the same query
        
        Args:
            agent_names: List of agent names to execute
            query: Query to process
            user_id: User identifier
            
        Returns:
            Combined execution results
        """
        results = []
        successful_executions = 0
        total_processing_time = 0
        
        for agent_name in agent_names:
            result = self.execute_agent(agent_name, query, user_id)
            results.append(result)
            
            if result["success"]:
                successful_executions += 1
                total_processing_time += result.get("processing_time", 0)
        
        return {
            "query": query,
            "user_id": user_id,
            "agents_executed": agent_names,
            "successful_executions": successful_executions,
            "total_processing_time": total_processing_time,
            "individual_results": results,
            "timestamp": datetime.now().isoformat()
        }
    
    def execute_by_capability(self, capability: str, query: str, user_id: int = 0) -> Dict[str, Any]:
        """
        Execute agents that have a specific capability
        
        Args:
            capability: Capability to search for
            query: Query to process
            user_id: User identifier
            
        Returns:
            Execution results from matching agents
        """
        matching_agents = []
        
        for agent_name, agent_config in self._get_agent_configs().items():
            if capability in agent_config.get("capabilities", []):
                matching_agents.append(agent_name)
        
        if not matching_agents:
            return {
                "success": False,
                "error": f"No agents found with capability: {capability}",
                "capability": capability
            }
        
        logger.info(f"Executing {len(matching_agents)} agents with capability '{capability}'")
        return self.execute_multiple_agents(matching_agents, query, user_id)
    
    def execute_by_keywords(self, query: str, user_id: int = 0, max_agents: int = 3) -> Dict[str, Any]:
        """
        Execute agents based on keyword matching in query
        
        Args:
            query: Query to analyze and process
            user_id: User identifier
            max_agents: Maximum number of agents to execute
            
        Returns:
            Execution results from matching agents
        """
        query_lower = query.lower()
        agent_scores = {}
        
        # Score agents based on keyword matches
        for agent_name, agent_config in self._get_agent_configs().items():
            score = 0
            keywords = agent_config.get("keywords", [])
            
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    score += 1
            
            if score > 0:
                agent_scores[agent_name] = score
        
        # Select top scoring agents
        if not agent_scores:
            # Fallback to default agent
            default_agent = self.config.get("routing_rules", {}).get("default_agent")
            if default_agent and default_agent in self.loaded_agents:
                agent_scores[default_agent] = 1
        
        # Sort by score and take top agents
        sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
        selected_agents = [agent for agent, score in sorted_agents[:max_agents]]
        
        logger.info(f"Selected agents for query: {selected_agents}")
        return self.execute_multiple_agents(selected_agents, query, user_id)
    
    def execute_entry_point(self, agent_name: str, *args, **kwargs) -> Any:
        """
        Execute specific entry point function in agent module
        
        Args:
            agent_name: Name of agent
            *args: Arguments to pass to entry point
            **kwargs: Keyword arguments to pass to entry point
            
        Returns:
            Result from entry point execution
        """
        if agent_name not in self.agent_modules:
            logger.error(f"Agent module {agent_name} not loaded")
            return None
        
        module = self.agent_modules[agent_name]
        agent_config = self._get_agent_config(agent_name)
        entry_point = agent_config.get("entry_point", "main")
        
        try:
            if hasattr(module, entry_point):
                entry_function = getattr(module, entry_point)
                if callable(entry_function):
                    logger.info(f"Executing {entry_point}() in {agent_name}")
                    return entry_function(*args, **kwargs)
                else:
                    logger.error(f"{entry_point} in {agent_name} is not callable")
            else:
                logger.warning(f"No {entry_point} function found in {agent_name}")
                
        except Exception as e:
            logger.error(f"Error executing {entry_point} in {agent_name}: {e}")
        
        return None
    
    def reload_agent(self, agent_name: str) -> bool:
        """
        Reload specific agent from file
        
        Args:
            agent_name: Name of agent to reload
            
        Returns:
            True if successful, False otherwise
        """
        agent_config = self._get_agent_config(agent_name)
        if not agent_config:
            logger.error(f"No configuration found for agent {agent_name}")
            return False
        
        try:
            # Remove existing agent
            if agent_name in self.loaded_agents:
                del self.loaded_agents[agent_name]
            if agent_name in self.agent_modules:
                del self.agent_modules[agent_name]
            
            # Reload agent
            agent_instance = self._load_agent_from_config(agent_config)
            if agent_instance:
                self.loaded_agents[agent_name] = agent_instance
                logger.info(f"Successfully reloaded agent: {agent_name}")
                return True
            else:
                logger.error(f"Failed to reload agent: {agent_name}")
                return False
                
        except Exception as e:
            logger.error(f"Error reloading agent {agent_name}: {e}")
            return False
    
    def reload_all_agents(self) -> Dict[str, bool]:
        """
        Reload all agents from configuration
        
        Returns:
            Dictionary mapping agent names to reload success status
        """
        logger.info("Reloading all agents...")
        
        # Reload configuration
        self.config = self._load_config()
        
        # Clear existing agents
        self.loaded_agents.clear()
        self.agent_modules.clear()
        
        # Reload all agents
        reload_results = {}
        agents_config = self.config.get("agents", [])
        
        for agent_config in agents_config:
            if not agent_config.get("enabled", True):
                continue
                
            agent_name = agent_config["name"]
            try:
                agent_instance = self._load_agent_from_config(agent_config)
                if agent_instance:
                    self.loaded_agents[agent_name] = agent_instance
                    reload_results[agent_name] = True
                else:
                    reload_results[agent_name] = False
            except Exception as e:
                logger.error(f"Error reloading agent {agent_name}: {e}")
                reload_results[agent_name] = False
        
        successful_reloads = sum(1 for success in reload_results.values() if success)
        logger.info(f"Reloaded {successful_reloads}/{len(reload_results)} agents successfully")
        
        return reload_results
    
    def add_agent_dynamically(self, agent_config: Dict[str, Any]) -> bool:
        """
        Add new agent dynamically at runtime
        
        Args:
            agent_config: Agent configuration dictionary
            
        Returns:
            True if successful, False otherwise
        """
        agent_name = agent_config["name"]
        
        try:
            # Load agent from configuration
            agent_instance = self._load_agent_from_config(agent_config)
            if not agent_instance:
                return False
            
            # Add to loaded agents
            self.loaded_agents[agent_name] = agent_instance
            
            # Update configuration
            current_agents = self.config.get("agents", [])
            current_agents.append(agent_config)
            self.config["agents"] = current_agents
            
            # Save updated configuration
            self._save_config()
            
            logger.info(f"Successfully added agent dynamically: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding agent dynamically: {e}")
            return False
    
    def remove_agent(self, agent_name: str) -> bool:
        """
        Remove agent from loader
        
        Args:
            agent_name: Name of agent to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove from loaded agents
            if agent_name in self.loaded_agents:
                del self.loaded_agents[agent_name]
            
            if agent_name in self.agent_modules:
                del self.agent_modules[agent_name]
            
            # Update configuration
            current_agents = self.config.get("agents", [])
            updated_agents = [a for a in current_agents if a["name"] != agent_name]
            self.config["agents"] = updated_agents
            
            # Save updated configuration
            self._save_config()
            
            logger.info(f"Successfully removed agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing agent {agent_name}: {e}")
            return False
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get loaded agent instance"""
        return self.loaded_agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """Get all loaded agent instances"""
        return self.loaded_agents.copy()
    
    def get_agent_names(self) -> List[str]:
        """Get list of all loaded agent names"""
        return list(self.loaded_agents.keys())
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have specific capability"""
        matching_agents = []
        
        for agent_name, agent_config in self._get_agent_configs().items():
            if capability in agent_config.get("capabilities", []):
                matching_agents.append(agent_name)
        
        return matching_agents
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get execution log"""
        return self.execution_log.copy()
    
    def clear_execution_log(self):
        """Clear execution log"""
        self.execution_log.clear()
        logger.info("Execution log cleared")
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded agents and executions"""
        total_executions = len(self.execution_log)
        successful_executions = sum(1 for log in self.execution_log if log["success"])
        
        agent_execution_counts = {}
        for log in self.execution_log:
            agent = log["agent"]
            agent_execution_counts[agent] = agent_execution_counts.get(agent, 0) + 1
        
        return {
            "total_agents_loaded": len(self.loaded_agents),
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "agent_execution_counts": agent_execution_counts,
            "loaded_agents": list(self.loaded_agents.keys()),
            "config_file": self.config_file
        }
    
    def _get_agent_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get agent configurations as dictionary"""
        configs = {}
        for agent_config in self.config.get("agents", []):
            configs[agent_config["name"]] = agent_config
        return configs
    
    def _get_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific agent"""
        for agent_config in self.config.get("agents", []):
            if agent_config["name"] == agent_name:
                return agent_config
        return None
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate current configuration
        
        Returns:
            Validation results
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "agent_validations": {}
        }
        
        agents_config = self.config.get("agents", [])
        
        for agent_config in agents_config:
            agent_name = agent_config["name"]
            agent_validation = {
                "file_exists": False,
                "class_exists": False,
                "inherits_base_agent": False,
                "has_entry_point": False
            }
            
            # Check file exists
            file_path = Path(agent_config["file_path"])
            if file_path.exists():
                agent_validation["file_exists"] = True
                
                # Check class exists and inheritance
                try:
                    if agent_name in self.agent_modules:
                        module = self.agent_modules[agent_name]
                    else:
                        # Load module temporarily for validation
                        spec = importlib.util.spec_from_file_location(agent_name, file_path)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                        else:
                            module = None
                    
                    if module:
                        class_name = agent_config["class_name"]
                        if hasattr(module, class_name):
                            agent_validation["class_exists"] = True
                            
                            agent_class = getattr(module, class_name)
                            if inspect.isclass(agent_class) and issubclass(agent_class, BaseAgent):
                                agent_validation["inherits_base_agent"] = True
                        
                        # Check entry point
                        entry_point = agent_config.get("entry_point", "main")
                        if hasattr(module, entry_point):
                            agent_validation["has_entry_point"] = True
                
                except Exception as e:
                    validation_results["errors"].append(f"Error validating {agent_name}: {e}")
            else:
                validation_results["errors"].append(f"File not found: {agent_config['file_path']}")
            
            validation_results["agent_validations"][agent_name] = agent_validation
            
            # Check for critical issues
            if not agent_validation["file_exists"]:
                validation_results["valid"] = False
            elif not agent_validation["inherits_base_agent"]:
                validation_results["warnings"].append(f"{agent_name} does not inherit from BaseAgent")
        
        return validation_results
    
    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about specific agent
        
        Args:
            agent_name: Name of agent
            
        Returns:
            Agent information dictionary
        """
        if agent_name not in self.loaded_agents:
            return None
        
        agent = self.loaded_agents[agent_name]
        agent_config = self._get_agent_config(agent_name)
        
        # Get execution statistics for this agent
        agent_executions = [log for log in self.execution_log if log["agent"] == agent_name]
        
        return {
            "name": agent_name,
            "class_name": agent.__class__.__name__,
            "description": agent.get_description(),
            "capabilities": agent.get_capabilities(),
            "keywords": getattr(agent, 'keywords', []),
            "file_path": agent_config.get("file_path") if agent_config else None,
            "loaded_at": getattr(agent, '_loaded_at', None),
            "execution_count": len(agent_executions),
            "success_rate": sum(1 for ex in agent_executions if ex["success"]) / len(agent_executions) if agent_executions else 0,
            "avg_processing_time": sum(ex["processing_time"] for ex in agent_executions) / len(agent_executions) if agent_executions else 0,
            "enabled": agent_config.get("enabled", True) if agent_config else True,
            "priority": agent_config.get("priority", 99) if agent_config else 99
        }
    
    def list_available_functions(self, agent_name: str) -> List[str]:
        """
        List all available functions in agent module using reflection
        
        Args:
            agent_name: Name of agent
            
        Returns:
            List of function names
        """
        if agent_name not in self.agent_modules:
            return []
        
        module = self.agent_modules[agent_name]
        functions = []
        
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj) and not name.startswith('_'):
                functions.append(name)
        
        return functions
    
    def execute_agent_function(self, agent_name: str, function_name: str, *args, **kwargs) -> Any:
        """
        Execute specific function in agent module using reflection
        
        Args:
            agent_name: Name of agent
            function_name: Name of function to execute
            *args: Arguments to pass to function
            **kwargs: Keyword arguments to pass to function
            
        Returns:
            Function execution result
        """
        if agent_name not in self.agent_modules:
            logger.error(f"Agent module {agent_name} not loaded")
            return None
        
        module = self.agent_modules[agent_name]
        
        try:
            if hasattr(module, function_name):
                function = getattr(module, function_name)
                if callable(function):
                    logger.info(f"Executing {function_name}() in {agent_name}")
                    return function(*args, **kwargs)
                else:
                    logger.error(f"{function_name} in {agent_name} is not callable")
            else:
                logger.error(f"Function {function_name} not found in {agent_name}")
                
        except Exception as e:
            logger.error(f"Error executing {function_name} in {agent_name}: {e}")
        
        return None


# Global dynamic agent loader instance
dynamic_agent_loader = None

def get_dynamic_agent_loader(memory_manager: MemoryManager = None) -> DynamicAgentLoader:
    """Get or create global dynamic agent loader instance"""
    global dynamic_agent_loader
    if dynamic_agent_loader is None:
        dynamic_agent_loader = DynamicAgentLoader(memory_manager=memory_manager)
    return dynamic_agent_loader

def load_agent_by_name(agent_name: str) -> Optional[BaseAgent]:
    """Helper function to load agent by name"""
    loader = get_dynamic_agent_loader()
    return loader.get_agent(agent_name)

def execute_agents_by_query(query: str, user_id: int = 0) -> Dict[str, Any]:
    """Helper function to execute agents based on query"""
    loader = get_dynamic_agent_loader()
    return loader.execute_by_keywords(query, user_id)