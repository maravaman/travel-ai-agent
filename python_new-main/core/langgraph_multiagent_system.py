"""
LangGraph Multiagent System
Advanced multiagent architecture with conditional routing, state management, and agent communication
Includes Weather Agent and Dining Agent for comprehensive functionality
"""

import json
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Literal
from datetime import datetime
from pathlib import Path
import operator

from langgraph.graph import StateGraph, END
from core.memory import MemoryManager
from core.ollama_client import ollama_client, prompt_manager

logger = logging.getLogger(__name__)

# Enhanced GraphState for multiagent communication
class MultiAgentState(TypedDict, total=False):
    """Enhanced state for multiagent LangGraph system"""
    user: str
    user_id: int
    question: str
    
    # Agent routing and communication
    current_agent: str
    next_agent: Optional[str]
    agent_chain: List[str]
    routing_decision: str
    
    # Responses and data
    response: str
    agent_responses: Dict[str, str]
    final_response: str
    
    # Context and memory
    context: Dict[str, Any]
    memory: Dict[str, Any]
    shared_data: Dict[str, Any]
    
    # Execution tracking
    edges_traversed: List[str]
    execution_path: List[Dict[str, Any]]
    timestamp: str
    
    # Agent-specific data
    weather_data: Optional[Dict[str, Any]]
    dining_data: Optional[Dict[str, Any]]
    location_data: Optional[Dict[str, Any]]
    forest_data: Optional[Dict[str, Any]]
    search_results: Optional[Dict[str, Any]]

class LangGraphMultiAgentSystem:
    """
    Advanced LangGraph Multiagent System
    Features:
    - Conditional agent routing based on query analysis
    - State management between agents
    - Memory integration (Redis STM + MySQL LTM)
    - Agent communication and data sharing
    - Dynamic execution paths
    """
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.agents_config = {}
        self.routing_rules = {}
        self.agent_capabilities = {}
        self.graph = None
        
        # Load configuration and initialize system
        self.load_agent_configuration()
        self.setup_routing_rules()
        
    def load_agent_configuration(self, json_path="core/agents.json"):
        """Load agent configuration from JSON file with fallback to hardcoded config"""
        try:
            # Attempt to load from JSON file
            if Path(json_path).exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_config = json.load(f)
                
                logger.info(f"📁 Loading agents from JSON: {json_path}")
                
                # Extract agents and configuration
                self.agents_config = {agent['id']: agent for agent in json_config['agents']}
                self.entry_point = json_config.get('entry_point', 'RouterAgent')
                
                # Load routing rules from JSON if available
                if 'routing_rules' in json_config:
                    self.routing_rules = json_config['routing_rules']
                
                # Build agent capabilities map
                for agent_id, config in self.agents_config.items():
                    self.agent_capabilities[agent_id] = {
                        'capabilities': config.get('capabilities', []),
                        'keywords': config.get('keywords', []),
                        'description': config.get('description', ''),
                        'priority': config.get('priority', 5),
                        'system_prompt_template': config.get('system_prompt_template', '')
                    }
                
                logger.info(f"✅ Successfully loaded {len(self.agents_config)} agents from JSON configuration")
                logger.info(f"🤖 Available agents: {list(self.agents_config.keys())}")
                
            else:
                logger.warning(f"⚠️ JSON config file not found: {json_path}")
                self._load_fallback_configuration()
                
        except Exception as e:
            logger.error(f"❌ Error loading JSON configuration: {e}")
            logger.info("🔄 Falling back to hardcoded configuration...")
            self._load_fallback_configuration()
    
    def _load_fallback_configuration(self):
        """Raise error if JSON configuration is not available"""
        error_msg = (
            "❌ No valid JSON configuration found. "
            "Please ensure 'core/agents.json' exists and is properly formatted. "
            "The system requires JSON configuration to operate."
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
        
    def setup_routing_rules(self):
        """Setup intelligent routing rules for agent communication from JSON or fallback"""
        # Use routing rules from JSON if available, otherwise use default rules
        if not hasattr(self, 'routing_rules') or not self.routing_rules:
            logger.info("Setting up default routing rules (JSON routing rules not found)")
            self.routing_rules = {
                "RouterAgent": {
                    "weather_query": ["WeatherAgent"],
                    "dining_query": ["DiningAgent"], 
                    "location_query": ["ScenicLocationFinderAgent"],
                    "forest_query": ["ForestAnalyzerAgent"],
                    "search_query": ["SearchAgent"],
                    "complex_travel": ["WeatherAgent", "DiningAgent", "ScenicLocationFinderAgent"],
                    "nature_exploration": ["ForestAnalyzerAgent", "WeatherAgent", "ScenicLocationFinderAgent"],
                    "default": ["ScenicLocationFinderAgent"]
                },
                "WeatherAgent": {
                    "needs_location": ["ScenicLocationFinderAgent"],
                    "needs_dining": ["DiningAgent"],
                    "end": []
                },
                "DiningAgent": {
                    "needs_weather": ["WeatherAgent"],
                    "needs_location": ["ScenicLocationFinderAgent"], 
                    "end": []
                },
                "ScenicLocationFinderAgent": {
                    "needs_weather": ["WeatherAgent"],
                    "needs_dining": ["DiningAgent"],
                    "needs_forest_info": ["ForestAnalyzerAgent"],
                    "end": []
                },
                "ForestAnalyzerAgent": {
                    "needs_location": ["ScenicLocationFinderAgent"],
                    "needs_weather": ["WeatherAgent"],
                    "end": []
                },
                "SearchAgent": {
                    "end": []
                }
            }
        
        logger.info(f"✅ Routing rules configured for {len(self.routing_rules)} agents")
        
    def build_langgraph(self) -> StateGraph:
        """Build the complete LangGraph dynamically from JSON configuration"""
        builder = StateGraph(MultiAgentState)
        
        # Create dynamic routing map for conditional edges
        routing_map = {}
        
        # Add all agent nodes dynamically from configuration
        for agent_id in self.agents_config.keys():
            if agent_id == "RouterAgent":
                # Router agent has special implementation
                builder.add_node("RouterAgent", self._router_agent_node)
                continue
                
            # Create dynamic agent node
            agent_method = self._create_dynamic_agent_node(agent_id)
            builder.add_node(agent_id, agent_method)
            
            # Add to routing map
            routing_map[self._get_routing_key(agent_id)] = agent_id
        
        # Add ResponseSynthesizer
        builder.add_node("ResponseSynthesizer", self._response_synthesizer_node)
        routing_map["synthesize"] = "ResponseSynthesizer"
        
        # Set entry point from configuration
        entry_point = getattr(self, 'entry_point', 'RouterAgent')
        builder.set_entry_point(entry_point)
        
        # Add conditional edges from RouterAgent
        builder.add_conditional_edges(
            "RouterAgent",
            self._route_from_router,
            routing_map
        )
        
        # Add conditional edges from each agent (except RouterAgent)
        for agent_id in self.agents_config.keys():
            if agent_id != "RouterAgent":
                builder.add_conditional_edges(
                    agent_id,
                    self._route_to_next_agent,
                    {**routing_map, "end": END}
                )
        
        # ResponseSynthesizer always ends
        builder.add_edge("ResponseSynthesizer", END)
        
        logger.info(f"🔗 Built LangGraph with {len(self.agents_config)} agents dynamically")
        return builder.compile()
    
    def _create_dynamic_agent_node(self, agent_id: str):
        """Create a dynamic agent node function for the specified agent"""
        def dynamic_agent_node(state: MultiAgentState) -> MultiAgentState:
            return self._generic_agent_processor(state, agent_id)
        return dynamic_agent_node
    
    def _generic_agent_processor(self, state: MultiAgentState, agent_id: str) -> MultiAgentState:
        """Generic agent processing method for JSON-configured agents"""
        try:
            question = state.get("question", "")
            user_id = state.get("user_id", 0)
            agent_config = self.agents_config.get(agent_id, {})
            
            if not question:
                logger.warning(f"Empty question in {agent_id}")
                question = f"General {agent_id} inquiry"
            
            # Build enhanced context based on other agents' data
            context = self._build_context_string(state.get("context", {}))
            enhanced_context = self._build_agent_context(state, agent_config, agent_id)
            
            # Generate response using agent's system prompt template
            response = None
            try:
                # Try using prompt manager first
                prompt_data = prompt_manager.get_prompt(agent_id, question, enhanced_context)
                if prompt_data and isinstance(prompt_data, dict) and "prompt" in prompt_data and "system" in prompt_data:
                    response = ollama_client.generate_response(
                        prompt=prompt_data["prompt"],
                        system_prompt=prompt_data["system"]
                    )
                else:
                    raise Exception("Invalid prompt data from prompt manager")
                    
            except Exception as prompt_error:
                logger.warning(f"{agent_id} prompt generation error: {prompt_error}")
                # Fallback to direct response with JSON system prompt template
                try:
                    system_prompt = self._get_agent_system_prompt(agent_id, agent_config)
                    response = ollama_client.generate_response(
                        prompt=f"{agent_config.get('name', agent_id)} Query: {question}\n\nContext: {enhanced_context}\n\nPlease provide a helpful response.",
                        system_prompt=system_prompt
                    )
                except Exception as fallback_error:
                    logger.error(f"{agent_id} fallback failed: {fallback_error}")
                    response = f"{agent_config.get('name', agent_id)} analysis is currently unavailable due to technical issues. Query was: {question}"
            
            # Ensure response is valid
            if not response or not isinstance(response, str):
                response = f"{agent_config.get('name', agent_id)} processed query: {question}, but no response was generated."
            
            # Update state
            updated_state = state.copy()
            updated_state["current_agent"] = agent_id
            
            # Update agent responses
            agent_responses = state.get("agent_responses", {})
            agent_responses[agent_id] = response
            updated_state["agent_responses"] = agent_responses
            
            # Update execution path
            execution_path = state.get("execution_path", [])
            execution_path.append({
                "agent": agent_id,
                "action": f"Provided {agent_config.get('name', agent_id)} analysis",
                "timestamp": datetime.now().isoformat()
            })
            updated_state["execution_path"] = execution_path
            
            # Store in memory
            self._store_agent_interaction(user_id, agent_id, question, response)
            
            logger.info(f"{agent_id} completed analysis")
            return updated_state
            
        except Exception as e:
            logger.error(f"{agent_id} error: {e}")
            updated_state = state.copy()
            updated_state["current_agent"] = agent_id
            updated_state["agent_responses"] = state.get("agent_responses", {})
            updated_state["agent_responses"][agent_id] = f"{agent_id} analysis currently unavailable: {str(e)}"
            return updated_state
    
    def _build_agent_context(self, state: MultiAgentState, agent_config: Dict[str, Any], agent_id: str) -> str:
        """Build enhanced context for agents based on other agents' data"""
        context_parts = []
        
        # Add basic context
        base_context = self._build_context_string(state.get("context", {}))
        if base_context and base_context != "No previous context available.":
            context_parts.append(base_context)
        
        # Add data from other agents
        weather_data = state.get("weather_data", {})
        dining_data = state.get("dining_data", {})
        location_data = state.get("location_data", {})
        forest_data = state.get("forest_data", {})
        
        # Add relevant context based on available agent data
        if weather_data and isinstance(weather_data, dict) and agent_id != "WeatherAgent":
            forecast = weather_data.get('forecast', '')
            if forecast and len(str(forecast)) > 100:
                forecast = str(forecast)[:100] + "..."
            context_parts.append(f"Weather Context: {forecast}")
        
        if dining_data and isinstance(dining_data, dict) and agent_id != "DiningAgent":
            recommendations = dining_data.get('recommendations', '')
            if recommendations and len(str(recommendations)) > 100:
                recommendations = str(recommendations)[:100] + "..."
            context_parts.append(f"Dining Context: {recommendations}")
        
        if location_data and isinstance(location_data, dict) and agent_id != "ScenicLocationFinderAgent":
            location_recs = location_data.get('recommendations', '')
            if location_recs and len(str(location_recs)) > 100:
                location_recs = str(location_recs)[:100] + "..."
            context_parts.append(f"Location Context: {location_recs}")
        
        if forest_data and isinstance(forest_data, dict) and agent_id != "ForestAnalyzerAgent":
            analysis = forest_data.get('analysis', '')
            if analysis and len(str(analysis)) > 100:
                analysis = str(analysis)[:100] + "..."
            context_parts.append(f"Forest Context: {analysis}")
        
        return "\n\n".join(context_parts) if context_parts else "No additional context available."
    
    def _get_agent_system_prompt(self, agent_id: str, agent_config: Dict[str, Any]) -> str:
        """Get system prompt for agent from JSON config or fallback"""
        # Try to get from JSON configuration first
        system_prompt_template = agent_config.get('system_prompt_template', '')
        
        if system_prompt_template:
            return system_prompt_template
        
        # Fallback to hardcoded prompts for known agents
        fallback_prompts = {
            "WeatherAgent": self._get_weather_system_prompt(),
            "DiningAgent": self._get_dining_system_prompt(),
            "ScenicLocationFinderAgent": self._get_scenic_system_prompt(),
            "ForestAnalyzerAgent": self._get_forest_system_prompt(),
            "SearchAgent": self._get_search_system_prompt()
        }
        
        if agent_id in fallback_prompts:
            return fallback_prompts[agent_id]
        
        # Generic fallback for unknown agents
        agent_name = agent_config.get('name', agent_id)
        capabilities = agent_config.get('capabilities', [])
        description = agent_config.get('description', 'specialized analysis')
        
        return f"""You are {agent_name}, specialized in {description}. Your capabilities include: {', '.join(capabilities)}.
Provide helpful, accurate, and detailed responses based on your expertise. Be professional and informative in your analysis."""
    
    def _get_routing_key(self, agent_id: str) -> str:
        """Convert agent ID to routing key"""
        routing_map = {
            "WeatherAgent": "weather",
            "DiningAgent": "dining",
            "ScenicLocationFinderAgent": "location",
            "ForestAnalyzerAgent": "forest",
            "SearchAgent": "search",
            "TravelAgent": "travel"
        }
        return routing_map.get(agent_id, agent_id.lower().replace("agent", ""))
    
    def _router_agent_node(self, state: MultiAgentState) -> MultiAgentState:
        """Router agent analyzes query and determines execution path"""
        question = state.get("question", "")
        
        # Analyze query to determine routing
        routing_decision = self._analyze_query_for_routing(question)
        
        # Update state
        updated_state = state.copy()
        updated_state["current_agent"] = "RouterAgent"
        updated_state["routing_decision"] = routing_decision
        updated_state["agent_chain"] = [routing_decision] if routing_decision != "synthesize" else []
        updated_state["edges_traversed"] = state.get("edges_traversed", []) + ["RouterAgent"]
        
        # Add execution path entry
        execution_path = state.get("execution_path", [])
        execution_path.append({
            "agent": "RouterAgent",
            "action": f"Routed query to {routing_decision}",
            "timestamp": datetime.now().isoformat()
        })
        updated_state["execution_path"] = execution_path
        
        logger.info(f"Router decided: {routing_decision} for query: {question[:50]}...")
        return updated_state
    
    def _weather_agent_node(self, state: MultiAgentState) -> MultiAgentState:
        """Weather agent provides weather information and forecasts"""
        try:
            question = state.get("question", "")
            user_id = state.get("user_id", 0)
            
            if not question:
                logger.warning("Empty question in weather agent")
                question = "General weather inquiry"
            
            # Build context for weather analysis with null safety
            context = self._build_context_string(state.get("context", {}))
            location_data = state.get("location_data", {})
            
            # Enhance question with location context if available
            enhanced_question = question
            if location_data and isinstance(location_data, dict):
                location = location_data.get('location', 'unknown')
                enhanced_question = f"{question} (considering location: {location})"
            
            # Generate weather response with comprehensive error handling
            response = None
            try:
                prompt_data = prompt_manager.get_prompt("WeatherAgent", enhanced_question, context)
                if not prompt_data or not isinstance(prompt_data, dict):
                    logger.warning("Invalid prompt data from prompt manager")
                    raise Exception("Invalid prompt data")
                
                if "prompt" not in prompt_data or "system" not in prompt_data:
                    logger.warning("Missing prompt or system key in prompt data")
                    raise Exception("Incomplete prompt data")
                    
                response = ollama_client.generate_response(
                    prompt=prompt_data["prompt"],
                    system_prompt=prompt_data["system"]
                )
            except Exception as prompt_error:
                logger.error(f"Weather agent prompt generation error: {prompt_error}")
                # Fallback to direct response with safe system prompt
                try:
                    response = ollama_client.generate_response(
                        prompt=f"Weather Query: {enhanced_question}\n\nContext: {context}\n\nPlease provide weather information.",
                        system_prompt=self._get_weather_system_prompt()
                    )
                except Exception as fallback_error:
                    logger.error(f"Weather agent fallback failed: {fallback_error}")
                    response = f"Weather information is currently unavailable due to technical issues. Query was: {enhanced_question}"
            
            # Ensure response is valid
            if not response or not isinstance(response, str):
                response = f"Weather agent processed query: {enhanced_question}, but no response was generated."
            
            # Store weather data for other agents
            weather_data = {
                "forecast": response,
                "location": location_data.get("location", "") if isinstance(location_data, dict) else "",
                "analysis_time": datetime.now().isoformat()
            }
            
            # Update state
            updated_state = state.copy()
            updated_state["current_agent"] = "WeatherAgent"
            updated_state["weather_data"] = weather_data
            
            # Update agent responses
            agent_responses = state.get("agent_responses", {})
            agent_responses["WeatherAgent"] = response
            updated_state["agent_responses"] = agent_responses
            
            # Update execution path
            execution_path = state.get("execution_path", [])
            execution_path.append({
                "agent": "WeatherAgent", 
                "action": "Provided weather analysis",
                "timestamp": datetime.now().isoformat()
            })
            updated_state["execution_path"] = execution_path
            
            # Store in memory
            self._store_agent_interaction(user_id, "WeatherAgent", question, response)
            
            logger.info("Weather agent completed analysis")
            return updated_state
            
        except Exception as e:
            logger.error(f"Weather agent error: {e}")
            updated_state = state.copy()
            updated_state["current_agent"] = "WeatherAgent"
            updated_state["agent_responses"] = state.get("agent_responses", {})
            updated_state["agent_responses"]["WeatherAgent"] = f"Weather information currently unavailable: {str(e)}"
            return updated_state
    
    def _dining_agent_node(self, state: MultiAgentState) -> MultiAgentState:
        """Dining agent provides restaurant and cuisine recommendations"""
        try:
            question = state.get("question", "")
            user_id = state.get("user_id", 0)
            
            if not question:
                logger.warning("Empty question in dining agent")
                question = "General dining inquiry"
            
            # Build context for dining recommendations with null safety
            context = self._build_context_string(state.get("context", {}))
            location_data = state.get("location_data", {})
            weather_data = state.get("weather_data", {})
            
            # Enhance question with available context
            enhanced_question = question
            context_parts = []
            
            if location_data and isinstance(location_data, dict):
                location = location_data.get('location', 'unknown')
                context_parts.append(f"Location: {location}")
            if weather_data and isinstance(weather_data, dict):
                forecast = weather_data.get('forecast', 'unknown')
                if forecast and len(str(forecast)) > 100:
                    forecast = str(forecast)[:100] + "..."
                context_parts.append(f"Weather: {forecast}")
                
            if context_parts:
                enhanced_question = f"{question} (Context: {'; '.join(context_parts)})"
            
            # Generate dining response with comprehensive error handling
            response = None
            try:
                prompt_data = prompt_manager.get_prompt("DiningAgent", enhanced_question, context)
                if not prompt_data or not isinstance(prompt_data, dict):
                    logger.warning("Invalid prompt data from prompt manager")
                    raise Exception("Invalid prompt data")
                
                if "prompt" not in prompt_data or "system" not in prompt_data:
                    logger.warning("Missing prompt or system key in prompt data")
                    raise Exception("Incomplete prompt data")
                    
                response = ollama_client.generate_response(
                    prompt=prompt_data["prompt"],
                    system_prompt=prompt_data["system"]
                )
            except Exception as prompt_error:
                logger.error(f"Dining agent prompt generation error: {prompt_error}")
                # Fallback to direct response with safe system prompt
                try:
                    response = ollama_client.generate_response(
                        prompt=f"Dining Query: {enhanced_question}\n\nContext: {context}\n\nPlease provide dining recommendations.",
                        system_prompt=self._get_dining_system_prompt()
                    )
                except Exception as fallback_error:
                    logger.error(f"Dining agent fallback failed: {fallback_error}")
                    response = f"Dining recommendations are currently unavailable due to technical issues. Query was: {enhanced_question}"
            
            # Ensure response is valid
            if not response or not isinstance(response, str):
                response = f"Dining agent processed query: {enhanced_question}, but no response was generated."
            
            # Store dining data for other agents
            dining_data = {
                "recommendations": response,
                "location": location_data.get("location", "") if isinstance(location_data, dict) else "",
                "weather_considered": bool(weather_data),
                "analysis_time": datetime.now().isoformat()
            }
            
            # Update state
            updated_state = state.copy()
            updated_state["current_agent"] = "DiningAgent"
            updated_state["dining_data"] = dining_data
            
            # Update agent responses
            agent_responses = state.get("agent_responses", {})
            agent_responses["DiningAgent"] = response
            updated_state["agent_responses"] = agent_responses
            
            # Update execution path
            execution_path = state.get("execution_path", [])
            execution_path.append({
                "agent": "DiningAgent",
                "action": "Provided dining recommendations", 
                "timestamp": datetime.now().isoformat()
            })
            updated_state["execution_path"] = execution_path
            
            # Store in memory
            self._store_agent_interaction(user_id, "DiningAgent", question, response)
            
            logger.info("Dining agent completed recommendations")
            return updated_state
            
        except Exception as e:
            logger.error(f"Dining agent error: {e}")
            updated_state = state.copy()
            updated_state["current_agent"] = "DiningAgent"
            updated_state["agent_responses"] = state.get("agent_responses", {})
            updated_state["agent_responses"]["DiningAgent"] = f"Dining recommendations currently unavailable: {str(e)}"
            return updated_state
    
    def _scenic_agent_node(self, state: MultiAgentState) -> MultiAgentState:
        """Scenic location finder agent with enhanced context awareness"""
        try:
            question = state.get("question", "")
            user_id = state.get("user_id", 0)
            
            if not question:
                logger.warning("Empty question in scenic location agent")
                question = "General location inquiry"
            
            # Build context with null safety
            context = self._build_context_string(state.get("context", {}))
            weather_data = state.get("weather_data", {})
            dining_data = state.get("dining_data", {})
            
            # Enhance question with weather and dining context
            enhanced_question = question
            context_parts = []
            
            if weather_data and isinstance(weather_data, dict):
                forecast = weather_data.get('forecast', 'unknown')
                if forecast and len(str(forecast)) > 100:
                    forecast = str(forecast)[:100] + "..."
                context_parts.append(f"Weather: {forecast}")
            if dining_data and isinstance(dining_data, dict):
                recommendations = dining_data.get('recommendations', 'unknown')
                if recommendations and len(str(recommendations)) > 100:
                    recommendations = str(recommendations)[:100] + "..."
                context_parts.append(f"Dining: {recommendations}")
                
            if context_parts:
                enhanced_question = f"{question} (Context: {'; '.join(context_parts)})"
            
            # Generate scenic location response with comprehensive error handling
            response = None
            try:
                prompt_data = prompt_manager.get_prompt("ScenicLocationFinder", enhanced_question, context)
                if not prompt_data or not isinstance(prompt_data, dict):
                    logger.warning("Invalid prompt data from prompt manager")
                    raise Exception("Invalid prompt data")
                
                if "prompt" not in prompt_data or "system" not in prompt_data:
                    logger.warning("Missing prompt or system key in prompt data")
                    raise Exception("Incomplete prompt data")
                    
                response = ollama_client.generate_response(
                    prompt=prompt_data["prompt"],
                    system_prompt=prompt_data["system"]
                )
            except Exception as prompt_error:
                logger.error(f"Scenic agent prompt generation error: {prompt_error}")
                # Fallback to direct response with safe system prompt
                try:
                    response = ollama_client.generate_response(
                        prompt=f"Location Query: {enhanced_question}\n\nContext: {context}\n\nPlease provide scenic location recommendations.",
                        system_prompt=self._get_scenic_system_prompt()
                    )
                except Exception as fallback_error:
                    logger.error(f"Scenic agent fallback failed: {fallback_error}")
                    response = f"Scenic location recommendations are currently unavailable due to technical issues. Query was: {enhanced_question}"
            
            # Ensure response is valid
            if not response or not isinstance(response, str):
                response = f"Scenic location agent processed query: {enhanced_question}, but no response was generated."
            
            # Store location data for other agents
            location_result_data = {
                "recommendations": response,
                "weather_integrated": bool(weather_data),
                "dining_integrated": bool(dining_data),
                "analysis_time": datetime.now().isoformat()
            }
            
            # Update state
            updated_state = state.copy()
            updated_state["current_agent"] = "ScenicLocationFinderAgent"
            updated_state["location_data"] = location_result_data
            
            # Update agent responses
            agent_responses = state.get("agent_responses", {})
            agent_responses["ScenicLocationFinderAgent"] = response
            updated_state["agent_responses"] = agent_responses
            
            # Update execution path
            execution_path = state.get("execution_path", [])
            execution_path.append({
                "agent": "ScenicLocationFinderAgent",
                "action": "Provided location recommendations",
                "timestamp": datetime.now().isoformat()
            })
            updated_state["execution_path"] = execution_path
            
            # Store in memory
            self._store_agent_interaction(user_id, "ScenicLocationFinderAgent", question, response)
            
            logger.info("Scenic location agent completed analysis")
            return updated_state
            
        except Exception as e:
            logger.error(f"Scenic location agent error: {e}")
            updated_state = state.copy()
            updated_state["current_agent"] = "ScenicLocationFinderAgent" 
            updated_state["agent_responses"] = state.get("agent_responses", {})
            updated_state["agent_responses"]["ScenicLocationFinderAgent"] = f"Location recommendations currently unavailable: {str(e)}"
            return updated_state
    
    def _forest_agent_node(self, state: MultiAgentState) -> MultiAgentState:
        """Forest analyzer agent with enhanced context"""
        try:
            question = state.get("question", "")
            user_id = state.get("user_id", 0)
            
            if not question:
                logger.warning("Empty question in forest agent")
                question = "General forest inquiry"
            
            # Build context with null safety
            context = self._build_context_string(state.get("context", {}))
            location_data = state.get("location_data", {})
            weather_data = state.get("weather_data", {})
            
            # Enhance with available context
            enhanced_question = question
            context_parts = []
            
            if location_data and isinstance(location_data, dict):
                recommendations = location_data.get('recommendations', 'unknown')
                if recommendations and len(str(recommendations)) > 100:
                    recommendations = str(recommendations)[:100] + "..."
                context_parts.append(f"Location: {recommendations}")
            if weather_data and isinstance(weather_data, dict):
                forecast = weather_data.get('forecast', 'unknown')
                if forecast and len(str(forecast)) > 100:
                    forecast = str(forecast)[:100] + "..."
                context_parts.append(f"Weather: {forecast}")
                
            if context_parts:
                enhanced_question = f"{question} (Context: {'; '.join(context_parts)})"
            
            # Generate forest analysis response with comprehensive error handling
            response = None
            try:
                prompt_data = prompt_manager.get_prompt("ForestAnalyzer", enhanced_question, context)
                if not prompt_data or not isinstance(prompt_data, dict):
                    logger.warning("Invalid prompt data from prompt manager")
                    raise Exception("Invalid prompt data")
                
                if "prompt" not in prompt_data or "system" not in prompt_data:
                    logger.warning("Missing prompt or system key in prompt data")
                    raise Exception("Incomplete prompt data")
                    
                response = ollama_client.generate_response(
                    prompt=prompt_data["prompt"],
                    system_prompt=prompt_data["system"]
                )
            except Exception as prompt_error:
                logger.error(f"Forest agent prompt generation error: {prompt_error}")
                # Fallback to direct response with safe system prompt
                try:
                    response = ollama_client.generate_response(
                        prompt=f"Forest Query: {enhanced_question}\n\nContext: {context}\n\nPlease provide forest ecosystem analysis.",
                        system_prompt=self._get_forest_system_prompt()
                    )
                except Exception as fallback_error:
                    logger.error(f"Forest agent fallback failed: {fallback_error}")
                    response = f"Forest analysis is currently unavailable due to technical issues. Query was: {enhanced_question}"
            
            # Ensure response is valid
            if not response or not isinstance(response, str):
                response = f"Forest agent processed query: {enhanced_question}, but no response was generated."
            
            # Store forest data
            forest_data = {
                "analysis": response,
                "location_considered": bool(location_data),
                "weather_considered": bool(weather_data),
                "analysis_time": datetime.now().isoformat()
            }
            
            # Update state
            updated_state = state.copy()
            updated_state["current_agent"] = "ForestAnalyzerAgent"
            updated_state["forest_data"] = forest_data
            
            # Update agent responses
            agent_responses = state.get("agent_responses", {})
            agent_responses["ForestAnalyzerAgent"] = response
            updated_state["agent_responses"] = agent_responses
            
            # Update execution path
            execution_path = state.get("execution_path", [])
            execution_path.append({
                "agent": "ForestAnalyzerAgent",
                "action": "Provided forest ecosystem analysis",
                "timestamp": datetime.now().isoformat()
            })
            updated_state["execution_path"] = execution_path
            
            # Store in memory
            self._store_agent_interaction(user_id, "ForestAnalyzerAgent", question, response)
            
            logger.info("Forest analyzer agent completed analysis")
            return updated_state
            
        except Exception as e:
            logger.error(f"Forest analyzer agent error: {e}")
            updated_state = state.copy()
            updated_state["current_agent"] = "ForestAnalyzerAgent"
            updated_state["agent_responses"] = state.get("agent_responses", {})
            updated_state["agent_responses"]["ForestAnalyzerAgent"] = f"Forest analysis currently unavailable: {str(e)}"
            return updated_state
    
    def _search_agent_node(self, state: MultiAgentState) -> MultiAgentState:
        """Search agent for memory and history analysis"""
        try:
            question = state.get("question", "")
            user_id = state.get("user_id", 0)
            
            if not question:
                logger.warning("Empty question in search agent")
                question = "General search inquiry"
            
            # Perform memory search with error handling
            try:
                search_results = self._perform_memory_search(question, user_id)
            except Exception as search_error:
                logger.error(f"Memory search failed: {search_error}")
                search_results = {"query": question, "matches": [], "total_found": 0, "error": str(search_error)}
            
            # Build context with null safety
            context = self._build_context_string(state.get("context", {}))
            
            # Generate search response with comprehensive error handling
            response = None
            try:
                search_context = f"{context}\n\nSearch Results: {search_results}"
                prompt_data = prompt_manager.get_prompt("SearchAgent", question, search_context)
                if not prompt_data or not isinstance(prompt_data, dict):
                    logger.warning("Invalid prompt data from prompt manager")
                    raise Exception("Invalid prompt data")
                
                if "prompt" not in prompt_data or "system" not in prompt_data:
                    logger.warning("Missing prompt or system key in prompt data")
                    raise Exception("Incomplete prompt data")
                    
                response = ollama_client.generate_response(
                    prompt=prompt_data["prompt"],
                    system_prompt=prompt_data["system"]
                )
            except Exception as prompt_error:
                logger.error(f"Search agent prompt generation error: {prompt_error}")
                # Fallback to direct response with safe system prompt
                try:
                    search_context = f"{context}\n\nSearch Results: {search_results}"
                    response = ollama_client.generate_response(
                        prompt=f"Search Query: {question}\n\nContext: {search_context}\n\nPlease analyze the search results.",
                        system_prompt=self._get_search_system_prompt()
                    )
                except Exception as fallback_error:
                    logger.error(f"Search agent fallback failed: {fallback_error}")
                    response = f"Search analysis is currently unavailable due to technical issues. Query was: {question}"
            
            # Ensure response is valid
            if not response or not isinstance(response, str):
                response = f"Search agent processed query: {question}, but no response was generated."
            
            # Update state
            updated_state = state.copy()
            updated_state["current_agent"] = "SearchAgent"
            updated_state["search_results"] = search_results
            
            # Update agent responses
            agent_responses = state.get("agent_responses", {})
            agent_responses["SearchAgent"] = response
            updated_state["agent_responses"] = agent_responses
            
            # Update execution path
            execution_path = state.get("execution_path", [])
            execution_path.append({
                "agent": "SearchAgent",
                "action": "Performed memory search and analysis",
                "timestamp": datetime.now().isoformat()
            })
            updated_state["execution_path"] = execution_path
            
            # Store in memory
            self._store_agent_interaction(user_id, "SearchAgent", question, response)
            
            logger.info("Search agent completed analysis")
            return updated_state
            
        except Exception as e:
            logger.error(f"Search agent error: {e}")
            updated_state = state.copy()
            updated_state["current_agent"] = "SearchAgent"
            updated_state["agent_responses"] = state.get("agent_responses", {})
            updated_state["agent_responses"]["SearchAgent"] = f"Search analysis currently unavailable: {str(e)}"
            return updated_state
    
    def _response_synthesizer_node(self, state: MultiAgentState) -> MultiAgentState:
        """Synthesize responses from multiple agents into coherent final response"""
        agent_responses = state.get("agent_responses", {})
        question = state.get("question", "")
        
        if not agent_responses:
            updated_state = state.copy()
            updated_state["final_response"] = "No agent responses to synthesize."
            updated_state["response"] = "No agent responses to synthesize."
            return updated_state
        
        # If only one agent responded, return its response directly
        if len(agent_responses) == 1:
            agent_id, response = list(agent_responses.items())[0]
            updated_state = state.copy()
            updated_state["current_agent"] = "ResponseSynthesizer"
            updated_state["final_response"] = response
            updated_state["response"] = response
            updated_state["primary_agent"] = agent_id
            return updated_state
        
        # Multi-agent response synthesis
        response_parts = []
        
        # Add contextual introduction based on query
        query_lower = question.lower()
        if any(word in query_lower for word in ["travel", "trip", "vacation", "visit", "plan"]):
            response_parts.append("🗺️ **Comprehensive Travel Analysis**\n")
            response_parts.append("Here's your complete travel guide combining insights from multiple specialists:\n")
        elif any(word in query_lower for word in ["best", "recommend", "find", "where"]):
            response_parts.append("🎯 **Multi-Expert Recommendations**\n")
            response_parts.append("Our specialists have collaborated to provide you with comprehensive recommendations:\n")
        else:
            response_parts.append("🤖 **Multi-Agent Analysis**\n")
            response_parts.append(f"Multiple experts have analyzed your query: \"{question[:60]}...\" Here are their insights:\n")
        
        # Define agent display info with emojis and friendly names
        agent_info = {
            "WeatherAgent": {"emoji": "🌤️", "name": "Weather Specialist", "expertise": "Climate & Weather Analysis"},
            "DiningAgent": {"emoji": "🍽️", "name": "Dining Expert", "expertise": "Restaurant & Cuisine Recommendations"},
            "ScenicLocationFinderAgent": {"emoji": "🏔️", "name": "Location Scout", "expertise": "Scenic Destinations & Travel"},
            "ForestAnalyzerAgent": {"emoji": "🌲", "name": "Nature Conservationist", "expertise": "Forest Ecosystems & Wildlife"},
            "SearchAgent": {"emoji": "🔍", "name": "Memory Analyst", "expertise": "Historical Search & Patterns"},
            "TravelAgent": {"emoji": "✈️", "name": "Travel Specialist", "expertise": "Travel Planning & Booking"}
        }
        
        # Add each agent's contribution with enhanced formatting
        agent_order = ["TravelAgent", "WeatherAgent", "DiningAgent", "ScenicLocationFinderAgent", "ForestAnalyzerAgent", "SearchAgent"]
        
        for agent_id in agent_order:
            if agent_id in agent_responses:
                response = agent_responses[agent_id].strip()
                if response:
                    info = agent_info.get(agent_id, {"emoji": "🤖", "name": agent_id, "expertise": "Analysis"})
                    
                    response_parts.append(f"## {info['emoji']} {info['name']} - {info['expertise']}")
                    response_parts.append("---")
                    response_parts.append(response)
                    response_parts.append("")  # Add spacing between agents
        
        # Add intelligent summary if multiple agents contributed
        if len(agent_responses) > 1:
            response_parts.append("## 🔗 **Integrated Summary**")
            response_parts.append("---")
            
            # Create contextual summary based on agents involved
            active_agents = list(agent_responses.keys())
            
            if "WeatherAgent" in active_agents and "DiningAgent" in active_agents:
                response_parts.append("🌟 **Perfect Planning Combination**: Weather conditions and dining options have been analyzed together to help you plan the ideal experience.")
            elif "ScenicLocationFinderAgent" in active_agents and "ForestAnalyzerAgent" in active_agents:
                response_parts.append("🌿 **Nature & Conservation Focus**: Scenic locations and ecological insights combined for environmentally conscious exploration.")
            elif "WeatherAgent" in active_agents and "ScenicLocationFinderAgent" in active_agents:
                response_parts.append("🏞️ **Weather-Optimized Travel**: Location recommendations tailored to current and forecast weather conditions.")
            else:
                response_parts.append(f"📋 **Multi-Perspective Analysis**: {len(active_agents)} specialists collaborated to provide comprehensive insights covering all aspects of your query.")
            
            response_parts.append("")
        
        # Add execution metadata
        execution_path = state.get("execution_path", [])
        if execution_path and len(execution_path) > 2:  # Only show if substantial execution
            response_parts.append("## 📊 **Analysis Process**")
            response_parts.append("---")
            agent_steps = [step for step in execution_path if step['agent'] != 'RouterAgent' and step['agent'] != 'ResponseSynthesizer']
            response_parts.append(f"**Execution Path**: {' → '.join([step['agent'] for step in agent_steps])}")
            response_parts.append(f"**Processing Time**: {len(agent_steps)} specialist(s) consulted")
            response_parts.append("")
        
        final_response = "\n".join(response_parts)
        
        # Update state
        updated_state = state.copy()
        updated_state["current_agent"] = "ResponseSynthesizer"
        updated_state["final_response"] = final_response
        updated_state["response"] = final_response
        updated_state["synthesis_type"] = "multi_agent"
        updated_state["agents_involved"] = list(agent_responses.keys())
        
        # Update execution path
        execution_path = state.get("execution_path", [])
        execution_path.append({
            "agent": "ResponseSynthesizer",
            "action": f"Synthesized responses from {len(agent_responses)} agents: {', '.join(agent_responses.keys())}",
            "timestamp": datetime.now().isoformat()
        })
        updated_state["execution_path"] = execution_path
        
        logger.info(f"Response synthesizer created comprehensive multi-agent response from {len(agent_responses)} agents")
        return updated_state
    
    def _analyze_query_for_routing(self, question: str) -> str:
        """Analyze query and determine initial routing decision with prioritized search detection"""
        question_lower = question.lower()
        
        # PRIORITY 1: Search-related queries (specific search terms)
        search_keywords = ["search", "history", "remember", "previous", "similar", "past", "recall", "from my history", "queries", "asked before"]
        if any(keyword in question_lower for keyword in search_keywords):
            return "search"
        
        # PRIORITY 2: Weather-related queries
        weather_keywords = ["weather", "temperature", "rain", "sun", "climate", "forecast", "humidity", "wind", "storm", "snow"]
        if any(keyword in question_lower for keyword in weather_keywords):
            return "weather"
        
        # PRIORITY 3: Dining-related queries  
        dining_keywords = ["restaurant", "food", "cuisine", "dining", "eat", "meal", "chef", "menu", "cooking", "recipe"]
        if any(keyword in question_lower for keyword in dining_keywords):
            return "dining"
        
        # PRIORITY 4: Location-related queries
        location_keywords = ["scenic", "beautiful", "location", "tourist", "destination", "view", "landscape", "mountain"]
        if any(keyword in question_lower for keyword in location_keywords):
            return "location"
        
        # PRIORITY 5: Forest-related queries
        forest_keywords = ["forest", "tree", "wildlife", "ecosystem", "conservation", "nature", "biodiversity"]
        if any(keyword in question_lower for keyword in forest_keywords):
            return "forest"
        
        # PRIORITY 6: Travel agent queries (comprehensive travel planning)
        travel_keywords = ["travel", "trip", "vacation", "holiday", "booking", "flight", "hotel", "itinerary", "tour", "package", "cruise", "resort"]
        if any(keyword in question_lower for keyword in travel_keywords):
            return "travel"  # Route to dedicated travel agent
        
        # Default to location if no specific routing
        return "location"
    
    def _route_from_router(self, state: MultiAgentState) -> str:
        """Route from RouterAgent to appropriate agent"""
        routing_decision = state.get("routing_decision", "location")
        return routing_decision
    
    def _route_to_next_agent(self, state: MultiAgentState) -> str:
        """Determine next agent or end execution - Enhanced for better multi-agent triggers"""
        current_agent = state.get("current_agent", "")
        question = state.get("question", "").lower()
        agent_responses = state.get("agent_responses", {})
        
        # Enhanced keyword detection for multi-agent scenarios
        weather_words = ["weather", "climate", "temperature", "rain", "sun", "forecast", "storm", "season"]
        dining_words = ["restaurant", "food", "dining", "eat", "meal", "cuisine", "chef", "menu", "taste"]
        location_words = ["location", "place", "where", "scenic", "beautiful", "visit", "destination", "travel", "trip"]
        forest_words = ["forest", "tree", "wildlife", "ecosystem", "conservation", "nature", "biodiversity", "jungle"]
        
        # More aggressive multi-agent routing based on current agent
        if current_agent == "WeatherAgent":
            # After weather, check for dining needs
            if any(word in question for word in dining_words):
                if "DiningAgent" not in agent_responses:
                    return "dining"
            # Check for location needs
            if any(word in question for word in location_words):
                if "ScenicLocationFinderAgent" not in agent_responses:
                    return "location"
            # Check for forest/nature needs
            if any(word in question for word in forest_words):
                if "ForestAnalyzerAgent" not in agent_responses:
                    return "forest"
        
        elif current_agent == "DiningAgent":
            # After dining, check for weather needs
            if any(word in question for word in weather_words):
                if "WeatherAgent" not in agent_responses:
                    return "weather"
            # Check for location needs
            if any(word in question for word in location_words):
                if "ScenicLocationFinderAgent" not in agent_responses:
                    return "location"
            # Check for nature/outdoor dining
            if any(word in question for word in forest_words + ["outdoor", "garden", "terrace"]):
                if "ForestAnalyzerAgent" not in agent_responses:
                    return "forest"
        
        elif current_agent == "ScenicLocationFinderAgent":
            # After location, check for weather needs
            if any(word in question for word in weather_words):
                if "WeatherAgent" not in agent_responses:
                    return "weather" 
            # Check for dining needs
            if any(word in question for word in dining_words):
                if "DiningAgent" not in agent_responses:
                    return "dining"
            # Check for forest/nature needs
            if any(word in question for word in forest_words):
                if "ForestAnalyzerAgent" not in agent_responses:
                    return "forest"
        
        elif current_agent == "ForestAnalyzerAgent":
            # After forest analysis, check for location needs
            if any(word in question for word in location_words):
                if "ScenicLocationFinderAgent" not in agent_responses:
                    return "location"
            # Check for weather needs
            if any(word in question for word in weather_words):
                if "WeatherAgent" not in agent_responses:
                    return "weather"
            # Check for dining needs (eco-tourism often includes dining)
            if any(word in question for word in dining_words + ["eco", "sustainable", "local"]):
                if "DiningAgent" not in agent_responses:
                    return "dining"
        
        elif current_agent == "SearchAgent":
            # Search agent typically doesn't trigger other agents
            pass
        
        elif current_agent == "TravelAgent":
            # After travel planning, check for weather needs
            if any(word in question for word in weather_words):
                if "WeatherAgent" not in agent_responses:
                    return "weather"
            # Check for dining needs
            if any(word in question for word in dining_words):
                if "DiningAgent" not in agent_responses:
                    return "dining"
            # Check for location needs
            if any(word in question for word in location_words):
                if "ScenicLocationFinderAgent" not in agent_responses:
                    return "location"
        
        # Enhanced multi-agent detection based on query complexity
        # Look for "best" or "recommend" queries that often need multiple perspectives
        if any(word in question for word in ["best", "recommend", "top", "ideal", "perfect", "plan", "trip", "vacation"]):
            needed_agents = []
            
            if any(word in question for word in weather_words) and "WeatherAgent" not in agent_responses:
                needed_agents.append("weather")
            if any(word in question for word in dining_words) and "DiningAgent" not in agent_responses:
                needed_agents.append("dining")
            if any(word in question for word in location_words) and "ScenicLocationFinderAgent" not in agent_responses:
                needed_agents.append("location")
            if any(word in question for word in forest_words) and "ForestAnalyzerAgent" not in agent_responses:
                needed_agents.append("forest")
            
            # Return the first needed agent
            if needed_agents:
                return needed_agents[0]
        
        # Check for travel/tourism queries that typically need multiple agents
        travel_indicators = ["travel", "trip", "vacation", "holiday", "visit", "explore", "tour"]
        if any(word in question for word in travel_indicators):
            # Ensure we have location agent for travel queries
            if "ScenicLocationFinderAgent" not in agent_responses:
                return "location"
            # Add weather for travel planning
            if "WeatherAgent" not in agent_responses and len(agent_responses) < 2:
                return "weather"
            # Add dining for comprehensive travel advice
            if "DiningAgent" not in agent_responses and len(agent_responses) < 3:
                return "dining"
        
        # If we have multiple agent responses, synthesize them
        if len(agent_responses) > 1:
            return "synthesize"
        
        # If only one agent has responded and no additional routing needed, synthesize
        if len(agent_responses) >= 1:
            return "synthesize"
        
        # Default end
        return "end"
    
    def _build_context_string(self, context: Dict[str, Any]) -> str:
        """Build context string from memory and shared data with null safety"""
        try:
            # Handle None or invalid context
            if context is None or not isinstance(context, dict):
                return "No previous context available."
            
            context_parts = []
            
            # Add STM context with null safety
            stm_data = context.get("stm", {})
            if isinstance(stm_data, dict) and stm_data.get("recent_interactions"):
                recent_interactions = stm_data["recent_interactions"]
                if isinstance(recent_interactions, dict):
                    context_parts.append("Recent interactions:")
                    for agent_id, interaction in recent_interactions.items():
                        if agent_id and interaction:
                            context_parts.append(f"- {agent_id}: {interaction}")
            
            # Add LTM context with null safety
            ltm_data = context.get("ltm", {})
            if isinstance(ltm_data, dict) and ltm_data.get("recent_history"):
                recent_history = ltm_data["recent_history"]
                if isinstance(recent_history, list):
                    context_parts.append("\nRelevant history:")
                    for entry in recent_history[:3]:
                        if isinstance(entry, dict) and "value" in entry and entry["value"]:
                            context_parts.append(f"- {entry['value']}")
            
            return "\n".join(context_parts) if context_parts else "No previous context available."
            
        except Exception as e:
            logger.warning(f"Error building context string: {e}")
            return "No previous context available."
    
    def _perform_memory_search(self, query: str, user_id: int) -> Dict[str, Any]:
        """Perform memory search for SearchAgent"""
        try:
            # Get recent STM and LTM data
            stm_data = self.memory_manager.get_all_stm_for_user(str(user_id))
            ltm_data = self.memory_manager.get_recent_ltm(str(user_id), days=30)
            
            # Simple text matching
            query_lower = query.lower()
            matching_items = []
            
            # Search STM
            for agent_id, content in stm_data.items():
                if query_lower in str(content).lower():
                    matching_items.append({
                        "source": "stm",
                        "agent": agent_id,
                        "content": content,
                        "relevance": str(content).lower().count(query_lower)
                    })
            
            # Search LTM
            for entry in ltm_data:
                if isinstance(entry, dict) and "value" in entry:
                    content = entry["value"]
                    if query_lower in content.lower():
                        matching_items.append({
                            "source": "ltm",
                            "content": content,
                            "relevance": content.lower().count(query_lower),
                            "timestamp": entry.get("timestamp")
                        })
            
            # Sort by relevance
            matching_items.sort(key=lambda x: x.get("relevance", 0), reverse=True)
            
            return {
                "query": query,
                "matches": matching_items[:10],  # Top 10 matches
                "total_found": len(matching_items)
            }
            
        except Exception as e:
            logger.error(f"Memory search error: {e}")
            return {"query": query, "matches": [], "total_found": 0, "error": str(e)}
    
    def _store_agent_interaction(self, user_id: int, agent_id: str, question: str, response: str):
        """Store agent interaction in memory"""
        try:
            # Store in STM (temporary)
            self.memory_manager.set_stm(
                user_id=str(user_id),
                agent_id=agent_id,
                value=f"Q: {question}\nA: {response}",
                expiry=3600  # 1 hour
            )
            
            # Store in LTM (permanent)
            self.memory_manager.set_ltm(
                user_id=str(user_id),
                agent_id=agent_id,
                value=f"Query: {question}\nResponse: {response}"
            )
            
        except Exception as e:
            logger.error(f"Failed to store agent interaction: {e}")
    
    # System prompts for each agent
    def _get_weather_system_prompt(self) -> str:
        return """You are WeatherAgent, a specialized weather analysis assistant. Provide accurate, helpful weather information including:
        - Current conditions and forecasts
        - Climate analysis and seasonal patterns
        - Weather-related planning advice
        - Impact on outdoor activities
        Be practical and actionable in your responses."""
    
    def _get_dining_system_prompt(self) -> str:
        return """You are DiningAgent, a culinary and restaurant specialist. Provide excellent dining recommendations including:
        - Restaurant suggestions and cuisine types
        - Local food culture and specialties
        - Dining experiences and ambiance
        - Food and weather/location considerations
        Be descriptive and helpful for dining decisions."""
    
    def _get_scenic_system_prompt(self) -> str:
        return """You are ScenicLocationFinderAgent, specialized in beautiful destinations. Provide detailed location recommendations including:
        - Scenic spots and viewpoints
        - Photography opportunities
        - Access information and travel tips
        - Integration with weather and dining options
        Be inspiring and practical in your suggestions."""
    
    def _get_forest_system_prompt(self) -> str:
        return """You are ForestAnalyzerAgent, focused on forest ecosystems. Provide comprehensive forest analysis including:
        - Ecosystem characteristics and biodiversity
        - Conservation status and environmental factors
        - Wildlife and flora information
        - Integration with location and weather data
        Be scientific yet accessible in your explanations."""
    
    def _get_search_system_prompt(self) -> str:
        return """You are SearchAgent, specialized in memory and history analysis. Provide insightful search results including:
        - Pattern recognition in user history
        - Relevant past interactions and context
        - Similarity analysis and connections
        - Historical insights for current queries
        Be analytical and helpful in connecting past and present."""
    
    def process_request(self, user: str, user_id: int, question: str) -> Dict[str, Any]:
        """Main processing function for the multiagent system"""
        try:
            # Build graph if not built
            if not self.graph:
                self.graph = self.build_langgraph()
            
            # Get memory context
            stm_context = self._get_stm_context(user_id)
            ltm_context = self._get_ltm_context(user_id)
            
            # Initialize state
            initial_state = MultiAgentState(
                user=user,
                user_id=user_id,
                question=question,
                current_agent="",
                next_agent=None,
                agent_chain=[],
                routing_decision="",
                response="",
                agent_responses={},
                final_response="",
                context={
                    "stm": stm_context,
                    "ltm": ltm_context
                },
                memory={
                    "interactions": [],
                    "agent_data": {}
                },
                shared_data={},
                edges_traversed=[],
                execution_path=[],
                timestamp=datetime.now().isoformat(),
                weather_data=None,
                dining_data=None,
                location_data=None,
                forest_data=None,
                search_results=None
            )
            
            # Execute the graph
            final_state = self.graph.invoke(initial_state)
            
            # Return comprehensive response
            return {
                "user": final_state.get("user"),
                "user_id": final_state.get("user_id"),
                "question": final_state.get("question"),
                "agent": final_state.get("current_agent"),
                "response": final_state.get("final_response", final_state.get("response", "")),
                "agent_responses": final_state.get("agent_responses", {}),
                "execution_path": final_state.get("execution_path", []),
                "edges_traversed": final_state.get("edges_traversed", []),
                "context": final_state.get("context", {}),
                "timestamp": final_state.get("timestamp"),
                "system_version": "2.0.0-multiagent",
                "agents_involved": list(final_state.get("agent_responses", {}).keys())
            }
            
        except Exception as e:
            logger.error(f"Multiagent system execution failed: {e}")
            return {
                "user": user,
                "user_id": user_id,
                "question": question,
                "agent": "ErrorHandler",
                "response": f"Multiagent system error: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_stm_context(self, user_id: int) -> Dict[str, Any]:
        """Get short-term memory context"""
        try:
            stm_data = self.memory_manager.get_all_stm_for_user(str(user_id))
            return {
                "recent_interactions": stm_data,
                "count": len(stm_data)
            }
        except Exception as e:
            logger.warning(f"Could not fetch STM context: {e}")
            return {}
    
    def _get_ltm_context(self, user_id: int) -> Dict[str, Any]:
        """Get long-term memory context"""
        try:
            ltm_data = self.memory_manager.get_recent_ltm(str(user_id), days=7)
            return {
                "recent_history": ltm_data[:10],
                "count": len(ltm_data)
            }
        except Exception as e:
            logger.warning(f"Could not fetch LTM context: {e}")
            return {}

# Global multiagent system instance
langgraph_multiagent_system = LangGraphMultiAgentSystem()
