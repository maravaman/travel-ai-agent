"""
Dynamic agent management system for LangGraph
Constraint: Perfect nodes and edges that can be updated for any agent directly
"""
import json
import importlib
import logging
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
import mysql.connector

try:
    from database.connection import get_mysql_conn
except ImportError:
    get_mysql_conn = None

logger = logging.getLogger(__name__)

class DynamicAgentManager:
    """Manages dynamic loading and configuration of agents"""
    
    def __init__(self):
        self.agents = {}
        self.agent_configs = {}
        self.edges = {}
        self.db_conn = None
        if get_mysql_conn:
            try:
                self.db_conn = get_mysql_conn()
            except Exception as e:
                logger.warning(f"Could not connect to MySQL: {e}")
        
        # Try loading from database first
        if self.db_conn:
            self.load_agent_configurations()
        
        # If no agents were loaded from DB, try loading from JSON file
        if not self.agent_configs:
            self.load_from_json_file()
    
    def load_agent_configurations(self):
        """Load agent configurations from database"""
        if not self.db_conn:
            logger.warning("No database connection available")
            return
            
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT agent_name, module_path, description, capabilities, dependencies, is_active
                FROM agent_configurations
                WHERE is_active = TRUE
            """)
            configs = cursor.fetchall()
            
            for config in configs:
                self.agent_configs[config['agent_name']] = {
                    'module_path': config['module_path'],
                    'description': config['description'],
                    'capabilities': json.loads(config['capabilities']) if config['capabilities'] else [],
                    'dependencies': json.loads(config['dependencies']) if config['dependencies'] else [],
                    'is_active': config['is_active']
                }
            
            cursor.close()
            logger.info(f"Loaded {len(self.agent_configs)} agent configurations")
            
        except Exception as e:
            logger.error(f"Error loading agent configurations: {e}")
    
    def load_graph_edges(self):
        """Load graph edges from database"""
        if not self.db_conn:
            logger.warning("No database connection available")
            return
            
        try:
            cursor = self.db_conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT source_agent, target_agent, edge_condition, weight
                FROM graph_edges
                WHERE is_active = TRUE
                ORDER BY weight ASC
            """)
            edges = cursor.fetchall()
            
            self.edges = {}
            for edge in edges:
                source = edge['source_agent']
                if source not in self.edges:
                    self.edges[source] = []
                
                self.edges[source].append({
                    'target': edge['target_agent'],
                    'condition': edge['edge_condition'],
                    'weight': edge['weight']
                })
            
            cursor.close()
            logger.info(f"Loaded {len(edges)} graph edges")
            
        except Exception as e:
            logger.error(f"Error loading graph edges: {e}")
    
    def load_agent(self, agent_name: str) -> Any:
        """Dynamically load an agent class"""
        if agent_name in self.agents:
            return self.agents[agent_name]
        
        if agent_name not in self.agent_configs:
            logger.error(f"Agent {agent_name} not found in configurations")
            return None
        
        try:
            config = self.agent_configs[agent_name]
            module_path = config['module_path']
            
            # Import the module dynamically
            module = importlib.import_module(module_path)
            
            # Get the agent class
            if hasattr(module, 'SearchAgent'):
                agent_class = module.SearchAgent
            elif hasattr(module, 'AgentClass'):
                agent_class = module.AgentClass
            elif hasattr(module, agent_name):
                agent_class = getattr(module, agent_name)
            else:
                # Try to find any class that looks like an agent
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, 'process') and 
                        not attr_name.startswith('_')):
                        agent_class = attr
                        break
                else:
                    raise ImportError(f"No agent class found in {module_path}")
            
            # Store the loaded agent
            self.agents[agent_name] = agent_class
            logger.info(f"Loaded agent: {agent_name}")
            return agent_class
            
        except Exception as e:
            logger.error(f"Error loading agent {agent_name}: {e}")
            return None
    
    def create_agent_instance(self, agent_name: str, memory_manager) -> Any:
        """Create an instance of an agent"""
        agent_class = self.load_agent(agent_name)
        if not agent_class:
            return None
        
        try:
            # Try different initialization patterns
            if agent_name == "SearchAgent":
                return agent_class(memory_manager)
            else:
                # Standard pattern for plugin agents
                return agent_class(name=agent_name, memory=memory_manager)
        except Exception as e:
            logger.error(f"Error creating agent instance {agent_name}: {e}")
            return None
    
    def add_agent(self, agent_name: str, module_path: str, description: str, 
                  capabilities: List[str], dependencies: List[str]) -> bool:
        """Add a new agent configuration"""
        if not self.db_conn:
            logger.warning("No database connection available")
            return False
            
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_configurations 
                (agent_name, module_path, description, capabilities, dependencies)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                module_path = VALUES(module_path),
                description = VALUES(description),
                capabilities = VALUES(capabilities),
                dependencies = VALUES(dependencies),
                updated_at = CURRENT_TIMESTAMP
                """,
                (agent_name, module_path, description, 
                 json.dumps(capabilities), json.dumps(dependencies))
            )
            cursor.close()
            
            # Reload configurations
            self.load_agent_configurations()
            logger.info(f"Added/updated agent configuration: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding agent configuration: {e}")
            return False
    
    def add_edge(self, source_agent: str, target_agent: str, 
                 condition: str = None, weight: int = 1) -> bool:
        """Add a new graph edge"""
        if not self.db_conn:
            logger.warning("No database connection available")
            return False
            
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                """
                INSERT INTO graph_edges (source_agent, target_agent, edge_condition, weight)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                edge_condition = VALUES(edge_condition),
                weight = VALUES(weight)
                """,
                (source_agent, target_agent, condition, weight)
            )
            cursor.close()
            
            # Reload edges
            self.load_graph_edges()
            logger.info(f"Added/updated edge: {source_agent} -> {target_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding graph edge: {e}")
            return False
    
    def remove_agent(self, agent_name: str) -> bool:
        """Deactivate an agent"""
        if not self.db_conn:
            logger.warning("No database connection available")
            return False
            
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "UPDATE agent_configurations SET is_active = FALSE WHERE agent_name = %s",
                (agent_name,)
            )
            cursor.close()
            
            # Remove from memory
            if agent_name in self.agents:
                del self.agents[agent_name]
            if agent_name in self.agent_configs:
                del self.agent_configs[agent_name]
            
            logger.info(f"Deactivated agent: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing agent: {e}")
            return False
    
    def remove_edge(self, source_agent: str, target_agent: str) -> bool:
        """Remove a graph edge"""
        if not self.db_conn:
            logger.warning("No database connection available")
            return False
            
        try:
            cursor = self.db_conn.cursor()
            cursor.execute(
                "UPDATE graph_edges SET is_active = FALSE WHERE source_agent = %s AND target_agent = %s",
                (source_agent, target_agent)
            )
            cursor.close()
            
            # Reload edges
            self.load_graph_edges()
            logger.info(f"Removed edge: {source_agent} -> {target_agent}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing graph edge: {e}")
            return False
    
    def get_agent_capabilities(self, agent_name: str) -> List[str]:
        """Get capabilities of an agent"""
        return self.agent_configs.get(agent_name, {}).get('capabilities', [])
    
    def get_agents_by_capability(self, capability: str) -> List[str]:
        """Get agents that have a specific capability"""
        matching_agents = []
        for agent_name, config in self.agent_configs.items():
            if capability in config.get('capabilities', []):
                matching_agents.append(agent_name)
        return matching_agents
    
    def get_all_agents(self) -> Dict[str, Dict]:
        """Get all active agent configurations"""
        return self.agent_configs.copy()
    
    def get_graph_edges(self) -> Dict[str, List]:
        """Get all graph edges"""
        if self.db_conn:
            self.load_graph_edges()
        return self.edges.copy()
    
    def validate_agent_dependencies(self, agent_name: str) -> bool:
        """Validate that agent dependencies are satisfied"""
        if agent_name not in self.agent_configs:
            return False
        
        dependencies = self.agent_configs[agent_name].get('dependencies', [])
        for dep in dependencies:
            if dep not in self.agent_configs:
                logger.warning(f"Agent {agent_name} depends on {dep} which is not available")
                return False
        
        return True
    
    def get_entry_point(self) -> Optional[str]:
        """Get the default entry point agent"""
        # Return orchestrator as default entry point
        if 'OrchestratorAgent' in self.agent_configs:
            return 'OrchestratorAgent'
        
        # Fallback to first available agent
        if self.agent_configs:
            return list(self.agent_configs.keys())[0]
        
        return None

    def load_from_json_file(self):
        """Load agent configurations from JSON file as fallback"""
        try:
            json_path = Path(__file__).parent / "agents.json"
            if not json_path.exists():
                logger.warning(f"Agent JSON file not found: {json_path}")
                return
                
            with open(json_path, 'r') as f:
                data = json.load(f)
                
            # Process agents
            for agent in data.get('agents', []):
                self.agent_configs[agent['id']] = {
                    'module_path': agent.get('module', f"agents.{agent['id'].lower()}"),
                    'description': agent.get('description', ''),
                    'capabilities': agent.get('capabilities', []),
                    'dependencies': [],
                    'is_active': True
                }
                
            # Process edges
            self.edges = {}
            for source, targets in data.get('edges', {}).items():
                self.edges[source] = [{'target': target, 'condition': '', 'weight': 1} for target in targets]
                
            logger.info(f"Loaded {len(self.agent_configs)} agents and {len(self.edges)} edges from JSON file")
            
        except Exception as e:
            logger.error(f"Error loading from JSON file: {e}")

# Global instance (created conditionally)
try:
    dynamic_agent_manager = DynamicAgentManager()
except Exception as e:
    logger.warning(f"Could not initialize DynamicAgentManager: {e}")
    dynamic_agent_manager = None
