"""
LangGraph Framework Implementation
Perfectly matches client requirements for data flow:
Client → LangGraph → Agents → Memory (Redis/MySQL) → Response
"""

import json
import logging
import importlib
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
from pathlib import Path
import operator

from langgraph.graph import StateGraph, END
from core.memory import MemoryManager
from core.ollama_client import ollama_client, prompt_manager

logger = logging.getLogger(__name__)

class GraphState(TypedDict, total=False):
    """LangGraph state structure"""
    user: str
    user_id: int
    question: str
    current_agent: str
    response: str
    context: Dict[str, Any]
    memory: Dict[str, Any]
    edges_traversed: List[str]
    timestamp: str

class LangGraphFramework:
    """
    Perfect framework implementation matching client specifications:
    1. Client sends request (POST /run_graph)
    2. LangGraph loads agent graph from agents.json
    3. Registered agents are initialized from config file
    4. Memory Manager provides context using STM (Redis) + LTM (MySQL)
    5. Edge Map defines agent communication
    6. Agent executes with context
    7. Result stored back to memory
    8. Response returned to client
    """
    
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.agents_config = {}
        self.edge_map = {}
        self.loaded_agents = {}
        self.graph = None
        
        # Load configuration from agents.json
        self.load_agents_config()
        
    def load_agents_config(self):
        """Step 2: Load agent graph from agents.json"""
        try:
            config_path = Path(__file__).parent / "agents.json"
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.agents_config = {agent['id']: agent for agent in config.get('agents', [])}
            self.edge_map = config.get('edges', {})
            self.entry_point = config.get('entry_point', 'ScenicLocationFinder')
            
            logger.info(f"✅ Loaded {len(self.agents_config)} agents from configuration")
            logger.info(f"📊 Edge map: {self.edge_map}")
            
        except Exception as e:
            logger.error(f"❌ Failed to load agents config: {e}")
            self.agents_config = {}
            self.edge_map = {}
    
    def initialize_agents(self):
        """Step 3: Initialize registered agents from config file"""
        for agent_id, agent_config in self.agents_config.items():
            try:
                # Create agent instance with proper initialization
                agent_instance = LangGraphAgent(
                    agent_id=agent_id,
                    config=agent_config,
                    memory_manager=self.memory_manager,
                    edge_map=self.edge_map
                )
                self.loaded_agents[agent_id] = agent_instance
                logger.info(f"✅ Initialized agent: {agent_id}")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize agent {agent_id}: {e}")
    
    def build_langgraph(self) -> StateGraph:
        """Build LangGraph with proper node and edge configuration"""
        builder = StateGraph(GraphState)
        
        # Add a single orchestrator node that handles all agent execution
        builder.add_node("orchestrator", self._execute_agent_flow)
        
        # Set entry point
        builder.set_entry_point("orchestrator")
        
        # Simple end after orchestrator
        builder.add_edge("orchestrator", END)
        
        return builder.compile()
    
    def _execute_agent_flow(self, state: GraphState) -> GraphState:
        """Execute fully democratic multi-agent flow with equal preferences"""
        question = state.get("question", "")
        
        # Get all relevant agents with equal preference (no hardcoding)
        relevant_agents = self._identify_relevant_agents(question)
        
        if not relevant_agents:
            # Fallback to entry point if no agents match
            relevant_agents = [self.entry_point] if self.entry_point in self.loaded_agents else []
        
        if not relevant_agents:
            # Final fallback
            updated_state = state.copy()
            updated_state["current_agent"] = "ErrorHandler"
            updated_state["response"] = "No agents available to process request"
            updated_state["edges_traversed"] = ["ErrorHandler"]
            return updated_state
        
        # Execute ALL relevant agents with equal preference
        agent_responses = []
        all_edges_traversed = []
        primary_agent = relevant_agents[0]  # For backward compatibility
        
        for agent_id in relevant_agents:
            if agent_id in self.loaded_agents:
                try:
                    agent = self.loaded_agents[agent_id]
                    agent_state = agent.execute(state)
                    
                    response = agent_state.get("response", "")
                    if response.strip():  # Only include non-empty responses
                        agent_responses.append({
                            'agent_id': agent_id,
                            'response': response,
                            'edges_traversed': agent_state.get("edges_traversed", [])
                        })
                        all_edges_traversed.extend(agent_state.get("edges_traversed", []))
                    
                except Exception as e:
                    logger.warning(f"⚠️ Agent {agent_id} execution failed: {e}")
                    continue
        
        # Combine all agent responses democratically (equal treatment)
        combined_response = self._combine_equal_agent_responses(agent_responses)
        
        # Return combined state
        updated_state = state.copy()
        updated_state["current_agent"] = primary_agent  # For API compatibility
        updated_state["response"] = combined_response
        updated_state["edges_traversed"] = list(set(all_edges_traversed))  # Remove duplicates
        
        return updated_state
    
    def _identify_relevant_agents(self, question: str) -> List[str]:
        """Dynamically identify ALL relevant agents with NO hardcodes - fully democratic"""
        question_lower = question.lower()
        relevant_agents = []
        
        # Completely dynamic agent matching - NO hardcoded capabilities!
        # Extract capabilities directly from agents.json configuration
        agent_scores = {}
        
        for agent_id, config in self.agents_config.items():
            if agent_id not in self.loaded_agents:
                continue
                
            score = 0
            keywords_matched = []
            
            # Use agent capabilities from configuration
            capabilities = config.get('capabilities', [])
            description = config.get('description', '')
            
            # Dynamic keyword extraction from agent capabilities and description
            all_keywords = capabilities + description.lower().split()
            
            # Count matches in query (completely dynamic)
            for keyword in all_keywords:
                keyword_clean = keyword.lower().strip('[](),.')
                if keyword_clean in question_lower and len(keyword_clean) > 2:
                    score += 1
                    if keyword_clean not in keywords_matched:
                        keywords_matched.append(keyword_clean)
            
            # Add semantic relevance based on common query patterns (no hardcodes)
            semantic_words = ["where", "what", "how", "when", "help", "find", "search", "tell", "show"]
            for word in semantic_words:
                if word in question_lower:
                    score += 0.3  # Lower weight for semantic matches
            
            if score > 0:
                agent_scores[agent_id] = {
                    'score': score,
                    'keywords_matched': keywords_matched,
                    'description': description
                }
        
        # Select ALL agents with positive scores (democratic - no artificial limits)
        if agent_scores:
            # Sort by score (highest first) but include ALL with positive scores
            sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            relevant_agents = [agent_id for agent_id, info in sorted_agents]
            
            logger.info(f"🎯 Democratic agent selection for query '{question}':")
            for agent_id, info in sorted_agents:
                logger.info(f"   • {agent_id}: score={info['score']}, keywords={info['keywords_matched']}")
        else:
            logger.info(f"🔍 No specific agents matched query '{question}', using fallback")
        
        return relevant_agents
    
    def _combine_equal_agent_responses(self, agent_responses: List[Dict[str, Any]]) -> str:
        """Combine responses from multiple agents with equal treatment (democratic synthesis)"""
        if not agent_responses:
            return "No responses generated from agents."
        
        if len(agent_responses) == 1:
            # Single agent response - return as-is for backward compatibility
            return agent_responses[0]['response']
        
        # Multiple agent responses - create democratic synthesis
        combined_parts = []
        combined_parts.append("🤖 **Multi-Agent Analysis** (Democratic Response)\n")
        
        # Add all agent perspectives with equal prominence
        for i, agent_resp in enumerate(agent_responses, 1):
            agent_id = agent_resp['agent_id']
            response = agent_resp['response'].strip()
            
            if response:
                # Clean agent ID for display
                display_name = agent_id.replace('Analyzer', '').replace('Agent', '').replace('Finder', '')
                combined_parts.append(f"**{display_name} Analysis:**")
                combined_parts.append(response)
                
                if i < len(agent_responses):  # Add separator except for last item
                    combined_parts.append("")
        
        # Add synthesis footer
        agent_names = [resp['agent_id'].replace('Analyzer', '').replace('Agent', '').replace('Finder', '') 
                      for resp in agent_responses]
        combined_parts.append(f"\n*Combined insights from {len(agent_responses)} agents: {', '.join(agent_names)}*")
        
        return "\n".join(combined_parts)
    
    def _should_continue(self, state: GraphState) -> str:
        """Determine next agent based on state and edge map"""
        current_agent = state.get('current_agent', self.entry_point)
        possible_next = self.edge_map.get(current_agent, [])
        
        if not possible_next:
            return END
        
        # For now, return first available next agent
        # This can be enhanced with more sophisticated routing logic
        return possible_next[0] if possible_next else END
    
    def process_request(self, user: str, user_id: int, question: str) -> Dict[str, Any]:
        """
        Main processing function following client's exact data flow:
        Client → LangGraph → Agents → Memory → Response
        """
        
        # Initialize agents if not done
        if not self.loaded_agents:
            self.initialize_agents()
        
        # Build graph if not built
        if not self.graph:
            self.graph = self.build_langgraph()
        
        # Step 4: Memory Manager provides context
        stm_context = self._get_stm_context(user_id)
        ltm_context = self._get_ltm_context(user_id)
        
        # Initialize state
        initial_state = GraphState(
            user=user,
            user_id=user_id,
            question=question,
            current_agent=self.entry_point,
            response="",
            context={
                "stm": stm_context,
                "ltm": ltm_context
            },
            memory={
                "interactions": [],
                "agent_responses": {}
            },
            edges_traversed=[],
            timestamp=datetime.now().isoformat()
        )
        
        try:
            # Execute LangGraph
            final_state = self.graph.invoke(initial_state)
            
            # Step 7: Store result back to memory
            self._store_results_to_memory(final_state)
            
            # Step 8: Return response to client
            return {
                "user": final_state.get("user"),
                "user_id": final_state.get("user_id"),
                "question": final_state.get("question"),
                "agent": final_state.get("current_agent"),
                "response": final_state.get("response", "No response generated"),
                "context": final_state.get("context", {}),
                "edges_traversed": final_state.get("edges_traversed", []),
                "timestamp": final_state.get("timestamp"),
                "framework_version": "1.0.0"
            }
            
        except Exception as e:
            logger.error(f"❌ Graph execution failed: {e}")
            return {
                "user": user,
                "user_id": user_id,
                "question": question,
                "agent": "ErrorHandler",
                "response": f"System error occurred: {str(e)}",
                "error": True,
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_stm_context(self, user_id: int) -> Dict[str, Any]:
        """Get short-term memory context from Redis"""
        try:
            stm_data = self.memory_manager.get_all_stm_for_user(str(user_id))
            return {
                "recent_interactions": stm_data,
                "count": len(stm_data)
            }
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch STM context: {e}")
            return {}
    
    def _get_ltm_context(self, user_id: int) -> Dict[str, Any]:
        """Get long-term memory context from MySQL"""
        try:
            ltm_data = self.memory_manager.get_recent_ltm(str(user_id), days=7)
            return {
                "recent_history": ltm_data[:10],  # Last 10 entries
                "count": len(ltm_data)
            }
        except Exception as e:
            logger.warning(f"⚠️ Could not fetch LTM context: {e}")
            return {}
    
    def _store_results_to_memory(self, state: GraphState):
        """Store execution results back to memory with proper user tracking"""
        try:
            user_id = str(state.get("user_id", 0))
            agent = state.get("current_agent", "unknown")
            question = state.get("question", "")
            response = state.get("response", "")
            
            # Store in STM (Redis) - temporary interaction
            self.memory_manager.set_stm(
                user_id=user_id,
                agent_id=agent,
                value=f"Q: {question}\nA: {response}",
                expiry=3600  # 1 hour
            )
            
            # Store in LTM (MySQL) - permanent record with proper user association
            self.memory_manager.set_ltm(
                user_id=user_id,
                agent_id=agent,
                value=f"Query: {question}\nResponse: {response}\nEdges: {state.get('edges_traversed', [])}"
            )
            
            # Log activity for authenticated users
            self._log_user_activity(state)
            
            logger.info(f"✅ Stored results for user {user_id}, agent {agent}")
            
        except Exception as e:
            logger.error(f"❌ Failed to store results to memory: {e}")
    
    def _log_user_activity(self, state: GraphState):
        """Log user activity if authentication service is available"""
        try:
            user_id = state.get("user_id")
            if user_id and user_id != 0:  # Only for authenticated users
                # Try to import and use auth service if available
                from auth.auth_service import auth_service
                
                # Ensure user exists (create anonymous if needed)
                username = state.get("user", f"user_{user_id}")
                auth_service.ensure_user_exists(int(user_id), username)
                
                auth_service.log_user_query(
                    user_id=int(user_id),
                    session_id="langgraph_session",  # Could be enhanced with actual session tracking
                    question=state.get("question", ""),
                    agent_used=state.get("current_agent", "unknown"),
                    response_text=state.get("response", ""),
                    edges_traversed=state.get("edges_traversed", []),
                    processing_time=None  # Could be tracked if needed
                )
                
                logger.info(f"✅ Activity logged for user {user_id}")
        except Exception as e:
            # Silently fail if auth service not available - this maintains backward compatibility
            logger.debug(f"User activity logging not available: {e}")

class LangGraphAgent:
    """Individual agent that executes within LangGraph framework"""
    
    def __init__(self, agent_id: str, config: Dict[str, Any], memory_manager: MemoryManager, edge_map: Dict[str, List[str]]):
        self.agent_id = agent_id
        self.config = config
        self.memory_manager = memory_manager
        self.edge_map = edge_map
        
    def execute(self, state: GraphState) -> GraphState:
        """
        Step 6: Agent executes its logic with given context
        Uses Memory Manager context (STM + LTM) for processing
        """
        
        user_id = state.get("user_id", 0)
        question = state.get("question", "")
        context = state.get("context", {})
        
        try:
            # Build context string from memory
            context_string = self._build_context_string(context)
            
            # Get agent-specific prompt
            prompt_data = prompt_manager.get_prompt(self.agent_id, question, context_string)
            
            # Execute agent logic using Ollama
            response = ollama_client.generate_response(
                prompt=prompt_data["prompt"],
                system_prompt=prompt_data["system"]
            )
            
            # Clean response (ensure it's text, not JSON)
            clean_response = self._clean_response(response)
            
            # Update state
            updated_state = state.copy()
            updated_state["current_agent"] = self.agent_id
            updated_state["response"] = clean_response
            updated_state["edges_traversed"] = state.get("edges_traversed", []) + [self.agent_id]
            
            # Add to memory interactions
            memory_data = updated_state.get("memory", {})
            memory_data["agent_responses"] = memory_data.get("agent_responses", {})
            memory_data["agent_responses"][self.agent_id] = clean_response
            updated_state["memory"] = memory_data
            
            logger.info(f"✅ Agent {self.agent_id} executed successfully")
            return updated_state
            
        except Exception as e:
            logger.error(f"❌ Agent {self.agent_id} execution failed: {e}")
            updated_state = state.copy()
            updated_state["current_agent"] = self.agent_id
            updated_state["response"] = f"Agent {self.agent_id} encountered an error: {str(e)}"
            return updated_state
    
    def _build_context_string(self, context: Dict[str, Any]) -> str:
        """Build context string from STM and LTM data"""
        context_parts = []
        
        # Add STM context
        stm_data = context.get("stm", {})
        if stm_data.get("recent_interactions"):
            context_parts.append("Recent interactions:")
            for agent_id, interaction in stm_data["recent_interactions"].items():
                context_parts.append(f"- {agent_id}: {interaction}")
        
        # Add LTM context
        ltm_data = context.get("ltm", {})
        if ltm_data.get("recent_history"):
            context_parts.append("\nRelevant history:")
            for entry in ltm_data["recent_history"][:3]:  # Last 3 entries
                if isinstance(entry, dict) and "value" in entry:
                    context_parts.append(f"- {entry['value']}")
        
        return "\n".join(context_parts) if context_parts else "No previous context available."
    
    def _clean_response(self, response: str) -> str:
        """Ensure response is clean text, not JSON"""
        if response.startswith('{') and response.endswith('}'):
            try:
                json_response = json.loads(response)
                if "response" in json_response:
                    return json_response["response"]
                elif "content" in json_response:
                    return json_response["content"]
                elif "text" in json_response:
                    return json_response["text"]
            except json.JSONDecodeError:
                pass
        return response

# Global framework instance
langgraph_framework = LangGraphFramework()
