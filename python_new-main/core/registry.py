"""
Enhanced agent registry system for LangGraph
Constraint: Supports individual agent files with BaseAgent inheritance
"""
import json
import importlib
import logging
import inspect
import os
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from .base_agent import BaseAgent
from .memory import MemoryManager

logger = logging.getLogger(__name__)

class AgentRegistry:
    """
    Agent registry system for managing and loading agents inheriting from BaseAgent
    
    This system allows:
    - Auto-discovery of agent classes
    - Dynamic loading of agent modules
    - Consistent initialization with memory management
    - Standardized agent capabilities and metadata
    """
    
    def __init__(self, registry_file: str = "core/agents.json"):
        """
        Initialize registry with configuration file
        
        Args:
            registry_file: Path to agent registry JSON file
        """
        self.registry_file = registry_file
        self.agents_config = self._load_config()
        self.registered_agents = {}
        self.agent_instances = {}
        
        # Auto-discover agent classes in agents directory
        self.discovered_agents = self._discover_agent_classes()
        
        logger.info(f"AgentRegistry initialized with {len(self.agents_config.get('agents', []))} configured agents")
        logger.info(f"Discovered {len(self.discovered_agents)} agent classes")
    
    def _load_config(self) -> Dict:
        """
        Load agent configuration from registry file
        
        Returns:
            Dict containing agent configuration
        """
        try:
            with open(self.registry_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load agent registry from {self.registry_file}: {e}")
            return {"agents": [], "edges": {}, "version": "1.0.0"}
    
    def _discover_agent_classes(self) -> Dict[str, Dict]:
        """
        Auto-discover agent classes in the agents directory
        
        Returns:
            Dict mapping agent IDs to their metadata
        """
        discovered = {}
        agents_dir = Path("core/agents")
        
        if not agents_dir.exists():
            logger.warning(f"Agents directory not found: {agents_dir}")
            return discovered
        
        # Find all Python files in agents directory
        for file_path in agents_dir.glob("*_agent.py"):
            if file_path.name.startswith("__"):
                continue
                
            module_name = file_path.stem
            try:
                # Import module dynamically
                module_path = f"core.agents.{module_name}"
                module = importlib.import_module(module_path)
                
                # Find classes inheriting from BaseAgent
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseAgent) and 
                        obj.__module__ == module.__name__ and
                        obj != BaseAgent):
                        
                        # Create agent metadata
                        agent_id = name
                        discovered[agent_id] = {
                            "class": obj,
                            "module_path": module_path,
                            "file_path": str(file_path),
                            "class_name": name
                        }
                        logger.info(f"Discovered agent class: {name} in {module_path}")
            
            except Exception as e:
                logger.warning(f"Error discovering agent in {file_path}: {e}")
        
        return discovered
    
    def register_agent(self, agent_id: str, module_path: str, 
                      class_name: str, description: str = None,
                      capabilities: List[str] = None) -> bool:
        """
        Register a new agent in the registry
        
        Args:
            agent_id: Unique ID for the agent
            module_path: Import path to the module
            class_name: Name of the agent class
            description: Description of the agent
            capabilities: List of agent capabilities
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            if not issubclass(agent_class, BaseAgent):
                logger.error(f"Agent class {class_name} must inherit from BaseAgent")
                return False
            
            self.registered_agents[agent_id] = {
                "class": agent_class,
                "module_path": module_path,
                "class_name": class_name,
                "description": description or getattr(agent_class, "_description", ""),
                "capabilities": capabilities or []
            }
            
            logger.info(f"Registered agent: {agent_id} from {module_path}.{class_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    def get_agent_class(self, agent_id: str) -> Optional[Type[BaseAgent]]:
        """
        Get agent class by ID
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent class if found, None otherwise
        """
        # Check in registered agents
        if agent_id in self.registered_agents:
            return self.registered_agents[agent_id]["class"]
        
        # Check in discovered agents
        if agent_id in self.discovered_agents:
            return self.discovered_agents[agent_id]["class"]
        
        # Check in configured agents
        for agent_config in self.agents_config.get("agents", []):
            if agent_config["id"] == agent_id:
                try:
                    # Try to import dynamically
                    module_path = f"core.{agent_config['module']}"
                    module = importlib.import_module(module_path)
                    
                    # Try different class naming patterns
                    class_names = [
                        agent_id,  # Exact ID
                        f"{agent_id}Agent",  # ID + Agent suffix
                        agent_id.replace("Agent", ""),  # Remove Agent suffix if present
                        "AgentClass"  # Generic class name
                    ]
                    
                    for class_name in class_names:
                        if hasattr(module, class_name):
                            agent_class = getattr(module, class_name)
                            if issubclass(agent_class, BaseAgent):
                                self.registered_agents[agent_id] = {
                                    "class": agent_class,
                                    "module_path": module_path,
                                    "class_name": class_name
                                }
                                return agent_class
                            
                except Exception as e:
                    logger.warning(f"Failed to load agent class for {agent_id}: {e}")
        
        logger.warning(f"Agent class not found for ID: {agent_id}")
        return None
    
    def create_agent_instance(self, agent_id: str, memory_manager: MemoryManager) -> Optional[BaseAgent]:
        """
        Create an instance of an agent by ID
        
        Args:
            agent_id: Agent identifier
            memory_manager: MemoryManager for the agent
            
        Returns:
            Instantiated agent if successful, None otherwise
        """
        # Check if we already have an instance
        if agent_id in self.agent_instances:
            return self.agent_instances[agent_id]
        
        agent_class = self.get_agent_class(agent_id)
        if not agent_class:
            logger.error(f"No agent class found for {agent_id}")
            return None
        
        try:
            # Create instance passing memory_manager
            agent_instance = agent_class(memory_manager)
            self.agent_instances[agent_id] = agent_instance
            logger.info(f"Created agent instance: {agent_id}")
            return agent_instance
            
        except Exception as e:
            logger.error(f"Failed to create agent instance for {agent_id}: {e}")
            return None
    
    def get_all_agents(self) -> Dict[str, Dict]:
        """
        Get all available agents (configured, registered, and discovered)
        
        Returns:
            Dict mapping agent IDs to their metadata
        """
        all_agents = {}
        
        # Add configured agents
        for agent_config in self.agents_config.get("agents", []):
            agent_id = agent_config["id"]
            all_agents[agent_id] = {
                "id": agent_id,
                "name": agent_config.get("name", agent_id),
                "module": agent_config.get("module", ""),
                "description": agent_config.get("description", ""),
                "capabilities": agent_config.get("capabilities", []),
                "priority": agent_config.get("priority", 99),
                "source": "config"
            }
        
        # Add registered agents
        for agent_id, agent_data in self.registered_agents.items():
            all_agents[agent_id] = {
                "id": agent_id,
                "name": agent_id,
                "module": agent_data["module_path"],
                "class_name": agent_data["class_name"],
                "description": agent_data.get("description", ""),
                "capabilities": agent_data.get("capabilities", []),
                "source": "registered"
            }
        
        # Add discovered agents
        for agent_id, agent_data in self.discovered_agents.items():
            if agent_id not in all_agents:  # Don't override existing entries
                all_agents[agent_id] = {
                    "id": agent_id,
                    "name": agent_id,
                    "module": agent_data["module_path"],
                    "class_name": agent_data["class_name"],
                    "description": getattr(agent_data["class"], "_description", ""),
                    "capabilities": getattr(agent_data["class"], "_capabilities", []),
                    "source": "discovered"
                }
        
        return all_agents
    
    def get_agent_by_capability(self, capability: str) -> List[str]:
        """
        Find agents that have a specific capability
        
        Args:
            capability: Capability to search for
            
        Returns:
            List of agent IDs with the specified capability
        """
        matching_agents = []
        
        # Check all agents for the capability
        all_agents = self.get_all_agents()
        for agent_id, agent_data in all_agents.items():
            if capability in agent_data.get("capabilities", []):
                matching_agents.append(agent_id)
        
        return matching_agents
    
    def get_agent_capabilities(self, agent_id: str) -> List[str]:
        """
        Get capabilities of a specific agent
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            List of agent capabilities
        """
        # Try to get from agent instances first
        if agent_id in self.agent_instances:
            return self.agent_instances[agent_id].get_capabilities()
        
        # Check in all agents
        all_agents = self.get_all_agents()
        if agent_id in all_agents:
            return all_agents[agent_id].get("capabilities", [])
        
        return []
    
    def save_config(self, file_path: str = None) -> bool:
        """
        Save current agent configuration to file
        
        Args:
            file_path: Path to save to (defaults to original registry file)
            
        Returns:
            True if successful, False otherwise
        """
        save_path = file_path or self.registry_file
        
        try:
            # Build config from current state
            config = {
                "version": self.agents_config.get("version", "1.0.0"),
                "entry_point": self.agents_config.get("entry_point", ""),
                "description": "LangGraph Multi-Agent System Configuration (Auto-updated)",
                "agents": []
            }
            
            # Add agents from registry
            all_agents = self.get_all_agents()
            for agent_id, agent_data in all_agents.items():
                config["agents"].append({
                    "id": agent_id,
                    "name": agent_data.get("name", agent_id),
                    "module": agent_data.get("module", ""),
                    "description": agent_data.get("description", ""),
                    "capabilities": agent_data.get("capabilities", []),
                    "priority": agent_data.get("priority", 99)
                })
            
            # Add edges if present
            if "edges" in self.agents_config:
                config["edges"] = self.agents_config["edges"]
            
            # Add edge_conditions if present
            if "edge_conditions" in self.agents_config:
                config["edge_conditions"] = self.agents_config["edge_conditions"]
            
            # Add memory_settings if present
            if "memory_settings" in self.agents_config:
                config["memory_settings"] = self.agents_config["memory_settings"]
            
            # Write to file
            with open(save_path, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"Saved agent configuration to {save_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save agent configuration: {e}")
            return False
    
    def refresh(self) -> None:
        """
        Refresh the registry by re-discovering agents and reloading config
        """
        self.agents_config = self._load_config()
        self.discovered_agents = self._discover_agent_classes()
        logger.info(f"Refreshed agent registry: {len(self.get_all_agents())} total agents available")

# Global instance
agent_registry = AgentRegistry()

def get_agent_class(agent_id: str) -> Optional[Type[BaseAgent]]:
    """
    Get agent class by ID (helper function)
    
    Args:
        agent_id: Agent identifier
        
    Returns:
        Agent class if found, None otherwise
    """
    return agent_registry.get_agent_class(agent_id)

def create_agent_instance(agent_id: str, memory_manager: MemoryManager) -> Optional[BaseAgent]:
    """
    Create an instance of an agent by ID (helper function)
    
    Args:
        agent_id: Agent identifier
        memory_manager: MemoryManager for the agent
        
    Returns:
        Instantiated agent if successful, None otherwise
    """
    return agent_registry.create_agent_instance(agent_id, memory_manager)

def get_all_agents() -> Dict[str, Dict]:
    """
    Get all available agents (helper function)
    
    Returns:
        Dict mapping agent IDs to their metadata
    """
    return agent_registry.get_all_agents()

def get_agent_by_capability(capability: str) -> List[str]:
    """
    Find agents that have a specific capability (helper function)
    
    Args:
        capability: Capability to search for
        
    Returns:
        List of agent IDs with the specified capability
    """
    return agent_registry.get_agent_by_capability(capability)

def register_agent(agent_id: str, module_path: str, class_name: str, 
                  description: str = None, capabilities: List[str] = None) -> bool:
    """
    Register a new agent in the registry (helper function)
    
    Args:
        agent_id: Unique ID for the agent
        module_path: Import path to the module
        class_name: Name of the agent class
        description: Description of the agent
        capabilities: List of agent capabilities
        
    Returns:
        True if registration successful, False otherwise
    """
    return agent_registry.register_agent(
        agent_id, module_path, class_name, description, capabilities
    )

def refresh_registry() -> None:
    """
    Refresh the registry (helper function)
    """
    agent_registry.refresh()
