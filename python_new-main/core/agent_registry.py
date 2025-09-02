"""
Agent Registry System
Automatically discovers and loads agents from the agents directory.
Provides centralized agent management without hardcoded configurations.
"""

import os
import importlib
import importlib.util
import inspect
import logging
from typing import Dict, List, Type, Any, Optional
from pathlib import Path
from core.base_agent import BaseAgent
from core.memory import MemoryManager

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Centralized registry for agent discovery and management"""
    
    def __init__(self, memory_manager: MemoryManager = None, agents_directory: str = "agents"):
        """
        Initialize the agent registry
        
        Args:
            memory_manager: Shared memory manager instance
            agents_directory: Directory containing agent modules
        """
        self.memory_manager = memory_manager
        self.agents_directory = agents_directory
        self.registered_agents: Dict[str, Type[BaseAgent]] = {}
        self.agent_instances: Dict[str, BaseAgent] = {}
        self.agent_metadata: Dict[str, Dict[str, Any]] = {}
        
        # Auto-discover agents on initialization
        self.discover_agents()
    
    def discover_agents(self):
        """Automatically discover and register all agents in the agents directory"""
        try:
            agents_path = Path(self.agents_directory)
            if not agents_path.exists():
                logger.warning(f"Agents directory '{self.agents_directory}' not found")
                return
            
            # Get all Python files in the agents directory
            agent_files = list(agents_path.glob("*.py"))
            agent_files = [f for f in agent_files if f.name != "__init__.py"]
            
            logger.info(f"Discovering agents in {len(agent_files)} files...")
            
            for agent_file in agent_files:
                self._load_agent_from_file(agent_file)
            
            logger.info(f"Successfully registered {len(self.registered_agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
    
    def _load_agent_from_file(self, agent_file: Path):
        """Load agent class from a specific file"""
        try:
            # Convert file path to module name
            module_name = f"{self.agents_directory}.{agent_file.stem}"
            
            # Import the module
            spec = importlib.util.spec_from_file_location(module_name, agent_file)
            if spec is None or spec.loader is None:
                logger.warning(f"Could not load spec for {agent_file}")
                return
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find agent classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, BaseAgent) and 
                    obj != BaseAgent and 
                    not name.startswith('_')):
                    
                    # Register the agent class
                    agent_name = self._extract_agent_name(name, obj)
                    self.registered_agents[agent_name] = obj
                    
                    # Create instance and store metadata
                    try:
                        instance = obj(memory_manager=self.memory_manager)
                        self.agent_instances[agent_name] = instance
                        
                        self.agent_metadata[agent_name] = {
                            "class_name": name,
                            "module_path": str(agent_file),
                            "description": instance.get_description(),
                            "capabilities": instance.get_capabilities(),
                            "keywords": instance.keywords,
                            "file_name": agent_file.name
                        }
                        
                        logger.info(f"Registered agent: {agent_name} ({name})")
                        
                    except Exception as e:
                        logger.error(f"Failed to instantiate agent {name}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to load agent from {agent_file}: {e}")
    
    def _extract_agent_name(self, class_name: str, agent_class: Type[BaseAgent]) -> str:
        """Extract a clean agent name from the class"""
        # Try to get name from the class instance
        try:
            temp_instance = agent_class(memory_manager=None)
            if hasattr(temp_instance, 'name'):
                return temp_instance.name
        except:
            pass
        
        # Fallback: clean up the class name
        name = class_name
        if name.endswith('Agent'):
            name = name[:-5]  # Remove 'Agent' suffix
        
        # Convert CamelCase to readable format
        import re
        name = re.sub('([A-Z][a-z]+)', r' \1', name).strip()
        name = re.sub('([a-z0-9])([A-Z])', r'\1 \2', name)
        
        # Convert to the format used in the system
        if 'Scenic' in name and 'Location' in name:
            return 'ScenicLocationFinder'
        elif 'Forest' in name:
            return 'ForestAnalyzer'
        elif 'Water' in name:
            return 'WaterBodyAnalyzer'
        elif 'Search' in name:
            return 'SearchAgent'
        
        # Default: remove spaces and return
        return name.replace(' ', '')
    
    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Get an agent instance by name"""
        return self.agent_instances.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, BaseAgent]:
        """Get all registered agent instances"""
        return self.agent_instances.copy()
    
    def get_agent_names(self) -> List[str]:
        """Get list of all registered agent names"""
        return list(self.registered_agents.keys())
    
    def get_agent_metadata(self, agent_name: str = None) -> Dict[str, Any]:
        """Get metadata for a specific agent or all agents"""
        if agent_name:
            return self.agent_metadata.get(agent_name, {})
        return self.agent_metadata.copy()
    
    def find_best_agent(self, query: str) -> Optional[str]:
        """Find the best agent to handle a specific query"""
        best_agent = None
        best_confidence = 0.0
        
        for agent_name, agent_instance in self.agent_instances.items():
            try:
                confidence = agent_instance.can_handle(query)
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_agent = agent_name
            except Exception as e:
                logger.warning(f"Error checking if {agent_name} can handle query: {e}")
        
        logger.info(f"Best agent for '{query[:50]}...': {best_agent} (confidence: {best_confidence:.2f})")
        return best_agent if best_confidence > 0.3 else None  # Minimum confidence threshold
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have a specific capability"""
        matching_agents = []
        
        for agent_name, metadata in self.agent_metadata.items():
            capabilities = metadata.get("capabilities", [])
            if capability in capabilities:
                matching_agents.append(agent_name)
        
        return matching_agents
    
    def get_agents_by_keyword(self, keyword: str) -> List[str]:
        """Get agents that respond to a specific keyword"""
        matching_agents = []
        keyword_lower = keyword.lower()
        
        for agent_name, metadata in self.agent_metadata.items():
            keywords = metadata.get("keywords", [])
            if any(keyword_lower == kw.lower() for kw in keywords):
                matching_agents.append(agent_name)
        
        return matching_agents
    
    def reload_agents(self):
        """Reload all agents (useful for development)"""
        logger.info("Reloading all agents...")
        
        # Clear existing registrations
        self.registered_agents.clear()
        self.agent_instances.clear()
        self.agent_metadata.clear()
        
        # Rediscover agents
        self.discover_agents()
    
    def add_agent_dynamically(self, agent_class: Type[BaseAgent], agent_name: str = None):
        """Add an agent class dynamically at runtime"""
        try:
            if not agent_name:
                agent_name = self._extract_agent_name(agent_class.__name__, agent_class)
            
            # Register the class
            self.registered_agents[agent_name] = agent_class
            
            # Create instance
            instance = agent_class(memory_manager=self.memory_manager)
            self.agent_instances[agent_name] = instance
            
            # Store metadata
            self.agent_metadata[agent_name] = {
                "class_name": agent_class.__name__,
                "module_path": "dynamically_added",
                "description": instance.get_description(),
                "capabilities": instance.get_capabilities(),
                "keywords": instance.keywords,
                "file_name": "dynamic"
            }
            
            logger.info(f"Dynamically added agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add agent dynamically: {e}")
            return False
    
    def remove_agent(self, agent_name: str) -> bool:
        """Remove an agent from the registry"""
        try:
            if agent_name in self.registered_agents:
                del self.registered_agents[agent_name]
            if agent_name in self.agent_instances:
                del self.agent_instances[agent_name]
            if agent_name in self.agent_metadata:
                del self.agent_metadata[agent_name]
            
            logger.info(f"Removed agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove agent {agent_name}: {e}")
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the registry"""
        total_capabilities = set()
        total_keywords = set()
        
        for metadata in self.agent_metadata.values():
            total_capabilities.update(metadata.get("capabilities", []))
            total_keywords.update(metadata.get("keywords", []))
        
        return {
            "total_agents": len(self.registered_agents),
            "agent_names": list(self.registered_agents.keys()),
            "total_unique_capabilities": len(total_capabilities),
            "total_unique_keywords": len(total_keywords),
            "agents_directory": self.agents_directory,
            "memory_manager_available": self.memory_manager is not None
        }
    
    def __str__(self) -> str:
        return f"AgentRegistry(agents={len(self.registered_agents)}, directory='{self.agents_directory}')"
    
    def __repr__(self) -> str:
        return self.__str__()
