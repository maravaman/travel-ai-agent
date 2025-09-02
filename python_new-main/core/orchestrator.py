from typing import TypedDict, Dict, Any
from core.memory import MemoryManager
from core.agent_registry import AgentRegistry
from core.config_loader import get_config
from langgraph.graph import StateGraph
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

# ✅ Step 1: Define the state structure
class GraphState(TypedDict, total=False):
    user: str
    user_id: int
    question: str
    agent: str
    response: str
    orchestration: dict

# Simple in-memory agent configuration (no database dependency)
STATIC_AGENT_CONFIGS = {
    "ScenicLocationFinder": {
        "description": "Scenic location finding agent for beautiful places",
        "system_prompt": "You are ScenicLocationFinder. Provide detailed recommendations for scenic locations with practical information, cultural insights, and photography tips.",
        "keywords": ["scenic", "mountain", "landscape", "beautiful", "view", "tourist", "visit", "travel", "place", "location", "destination"]
    },
    "ForestAnalyzer": {
        "description": "Forest ecosystem analysis agent",
        "system_prompt": "You are ForestAnalyzer. Analyze forest ecosystems, biodiversity, conservation status, and provide scientific insights with practical recommendations.",
        "keywords": ["forest", "tree", "woodland", "ecosystem", "biodiversity", "conservation", "wildlife", "nature", "jungle"]
    },
    "WaterBodyAnalyzer": {
        "description": "Water body and aquatic systems analysis agent",
        "system_prompt": "You are WaterBodyAnalyzer. Analyze water bodies, hydrological features, aquatic ecosystems, and provide insights about water resources and activities.",
        "keywords": ["water", "lake", "river", "ocean", "sea", "pond", "backwater", "aquatic", "marine", "coastal", "dam"]
    },
    "SearchAgent": {
        "description": "Vector-based similarity search agent for history matching",
        "system_prompt": "You are SearchAgent, specialized in finding similar content from user history. Analyze patterns and return insights in JSON format.",
        "keywords": ["search", "history", "previous", "before", "recall", "remember", "similar", "past"]
    }
}

# Simplified agent class for LangGraph integration
class SimpleGraphAgent:
    def __init__(self, name: str, config: Dict[str, Any], memory: MemoryManager):
        self.name = name
        self.config = config
        self.memory = memory
    
    def process(self, state: GraphState) -> GraphState:
        """Process state and return updated state"""
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            # Use the Ollama client directly for text responses
            from core.ollama_client import ollama_client, prompt_manager
            
            # Get agent-specific prompt and system message
            prompt_data = prompt_manager.get_prompt(self.name, query, "")
            
            # Generate response using Ollama (returns text, not JSON)
            response = ollama_client.generate_response(
                prompt=prompt_data["prompt"],
                system_prompt=prompt_data["system"]
            )
            
            # Ensure response is clean text (no JSON formatting)
            if response.startswith('{') and response.endswith('}'):
                try:
                    # If it's JSON, extract the content
                    json_response = json.loads(response)
                    if "response" in json_response:
                        response = json_response["response"]
                    elif "content" in json_response:
                        response = json_response["content"]
                    elif "text" in json_response:
                        response = json_response["text"]
                except json.JSONDecodeError:
                    # If not valid JSON, use as is
                    pass
            
            # Store in memory for future reference
            self.memory.set_ltm(str(user_id), self.name, f"Query: {query}\nResponse: {response}")
            
            # Update state
            updated_state = state.copy()
            updated_state["agent"] = self.name
            updated_state["response"] = response
            updated_state["orchestration"] = {
                "strategy": "langgraph_single_agent",
                "selected_agents": [self.name],
                "timestamp": datetime.now().isoformat()
            }
            
            return updated_state
            
        except Exception as e:
            logger.error(f"Error in {self.name}: {e}")
            updated_state = state.copy()
            updated_state["agent"] = self.name
            updated_state["response"] = f"I apologize, but I encountered an issue processing your request. Please try again or rephrase your question."
            return updated_state

# Global registry instance
_agent_registry = None

def get_agent_registry():
    """Get or create the global agent registry"""
    global _agent_registry
    if _agent_registry is None:
        memory = MemoryManager()
        config = get_config()
        agents_dir = config.get("agent_registry.agents_directory", "agents")
        _agent_registry = AgentRegistry(memory_manager=memory, agents_directory=agents_dir)
    return _agent_registry

def build_dynamic_graph(question: str = ""):
    """Build graph using the agent registry system"""
    try:
        config = get_config()
        registry = get_agent_registry()
        builder = StateGraph(GraphState)
        
        # Get all available agents
        available_agents = registry.get_all_agents()
        logger.info(f"Building graph with {len(available_agents)} registered agents")
        
        if not available_agents:
            logger.error("No agents available in registry")
            return None
        
        # Add nodes for all registered agents
        for agent_name, agent_instance in available_agents.items():
            try:
                # Create a wrapper function that calls the agent's process method
                def create_agent_wrapper(agent):
                    def wrapper(state: GraphState) -> GraphState:
                        return agent.process(state)
                    return wrapper
                
                builder.add_node(agent_name, create_agent_wrapper(agent_instance))
                logger.info(f"Added node: {agent_name}")
            except Exception as e:
                logger.error(f"Failed to add agent {agent_name}: {e}")
        
        # Smart entry point selection using agent registry
        fallback_agent = config.get("orchestration.fallback_agent", "ScenicLocationFinder")
        entry_point = fallback_agent
        
        if question:
            # Use agent registry to find the best agent
            best_agent = registry.find_best_agent(question)
            if best_agent and best_agent in available_agents:
                entry_point = best_agent
                logger.info(f"Selected best agent: {entry_point}")
            else:
                logger.info(f"Using fallback agent: {entry_point}")
        
        builder.set_entry_point(entry_point)
        logger.info(f"Set entry point: {entry_point}")
        
        return builder.compile()
        
    except Exception as e:
        logger.error(f"Error building graph: {e}")
        return None

# ✅ Step 3: Run the simplified graph
def run_dynamic_graph(user: str, user_id: int, question: str):
    """Run graph with simplified routing (fallback to multi_agent_system)"""
    try:
        graph = build_dynamic_graph(question)
        
        if not graph:
            logger.warning("Graph build failed, using direct Ollama fallback")
            # Fallback to direct Ollama response
            from core.ollama_client import ollama_client, prompt_manager
            
            # Use ScenicLocationFinder as default
            prompt_data = prompt_manager.get_prompt("ScenicLocationFinder", question, "")
            response = ollama_client.generate_response(
                prompt=prompt_data["prompt"],
                system_prompt=prompt_data["system"]
            )
            
            return {
                "user": user,
                "user_id": user_id,
                "question": question,
                "agent": "ScenicLocationFinder",
                "response": response,
                "orchestration": {"strategy": "fallback_direct", "timestamp": datetime.now().isoformat()}
            }
        
        state = {
            "user": user,
            "user_id": user_id,
            "question": question,
            "agent": "",
            "response": ""
        }
        
        result = graph.invoke(state)
        logger.info(f"Graph execution completed for user {user}")
        return result
        
    except Exception as e:
        logger.error(f"Error running graph: {e}")
        # Direct Ollama fallback for all errors
        try:
            from core.ollama_client import ollama_client, prompt_manager
            
            # Use ScenicLocationFinder as safe default
            prompt_data = prompt_manager.get_prompt("ScenicLocationFinder", question, "")
            response = ollama_client.generate_response(
                prompt=prompt_data["prompt"],
                system_prompt=prompt_data["system"]
            )
            
            return {
                "user": user,
                "user_id": user_id,
                "question": question,
                "agent": "ScenicLocationFinder",
                "response": response,
                "orchestration": {"strategy": "error_fallback", "timestamp": datetime.now().isoformat()},
                "fallback": True
            }
        except Exception as fallback_error:
            logger.error(f"Even Ollama fallback failed: {fallback_error}")
            return {
                "user": user,
                "user_id": user_id,
                "question": question,
                "agent": "ErrorHandler",
                "response": "I apologize, but I'm currently experiencing technical difficulties. Please try again later or contact support if the issue persists.",
                "error": True,
                "orchestration": {"strategy": "critical_error", "timestamp": datetime.now().isoformat()}
            }

# Legacy functions for backward compatibility
def build_graph():
    """Legacy function - redirects to dynamic graph"""
    return build_dynamic_graph()

def run_graph(user: str, question: str):
    """Legacy function - redirects to dynamic graph with user_id=0"""
    return run_dynamic_graph(user, 0, question)

# Simple direct orchestrator function
def run_direct_orchestrator(user: str, user_id: int, question: str):
    """Direct orchestrator that bypasses LangGraph for simpler execution"""
    try:
        config = get_config()
        registry = get_agent_registry()
        
        # Find the best agent for the question
        best_agent_name = registry.find_best_agent(question)
        fallback_agent = config.get("orchestration.fallback_agent", "ScenicLocationFinder")
        
        if not best_agent_name:
            best_agent_name = fallback_agent
        
        # Get the agent instance
        agent = registry.get_agent(best_agent_name)
        if not agent:
            logger.error(f"Agent {best_agent_name} not found in registry")
            agent = registry.get_agent(fallback_agent)
        
        if not agent:
            raise Exception(f"Neither best agent ({best_agent_name}) nor fallback agent ({fallback_agent}) found")
        
        logger.info(f"Using agent: {agent.get_name()} for query: {question[:50]}...")
        
        # Create state and process
        state = {
            "user": user,
            "user_id": user_id,
            "question": question,
            "agent": "",
            "response": ""
        }
        
        # Process the query directly
        result = agent.process(state)
        
        # Ensure the result has the required orchestration metadata
        if "orchestration" not in result:
            result["orchestration"] = {
                "strategy": "direct_orchestrator",
                "selected_agents": [agent.get_name()],
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Direct orchestrator completed for user {user}")
        return result
        
    except Exception as e:
        logger.error(f"Direct orchestrator failed: {e}")
        
        # Final fallback
        return {
            "user": user,
            "user_id": user_id,
            "question": question,
            "agent": "ErrorHandler",
            "response": "I apologize, but I'm currently experiencing technical difficulties. Please try again later.",
            "error": True,
            "orchestration": {
                "strategy": "direct_orchestrator_error", 
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
        }
