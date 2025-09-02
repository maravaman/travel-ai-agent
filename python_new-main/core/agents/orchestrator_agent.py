"""
Enhanced orchestrator agent for LangGraph
Constraint: Perfect orchestrator that routes queries to BaseAgent-based agents
- Single agent response if query satisfies one agent
- Multi-agent orchestration for complex queries
- Seamless integration with new agent architecture
"""
import json
import re
import logging
from typing import Dict, Any, List, Set
from ..base_agent import BaseAgent, GraphState
from ..memory import MemoryManager
from ..ollama_client import ollama_client, prompt_manager

logger = logging.getLogger(__name__)

class OrchestratorAgent(BaseAgent):
    """
    Enhanced orchestrator agent that routes queries to appropriate BaseAgent-based agents
    
    This orchestrator:
    - Inherits from BaseAgent for consistent interface
    - Auto-discovers available agents via registry
    - Routes queries to appropriate specialized agents
    - Coordinates multi-agent responses
    - Maintains memory of orchestration decisions
    """
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize OrchestratorAgent with memory management and agent discovery
        
        Args:
            memory_manager: MemoryManager instance for STM and LTM operations
        """
        super().__init__(memory_manager, "OrchestratorAgent")
        
        # Override base capabilities with orchestrator-specific ones
        self._capabilities = [
            "query_routing", 
            "multi_agent_coordination", 
            "agent_discovery",
            "response_synthesis",
            "orchestration_memory"
        ]
        self._description = "Intelligent orchestrator that routes queries to appropriate agents and coordinates multi-agent responses"
        
        # Import registry here to avoid circular import
        from ..registry import agent_registry
        
        # Get available agents from registry
        self.available_agents = agent_registry.get_all_agents()
        
        # Build dynamic routing patterns based on available agents
        self.routing_patterns = self._build_routing_patterns()
        
        logger.info(f"OrchestratorAgent initialized with {len(self.available_agents)} available agents")
    
    def process(self, state: GraphState) -> GraphState:
        """
        Orchestrate query routing to appropriate agents
        
        Args:
            state: Current GraphState containing user query and context
            
        Returns:
            Updated GraphState with orchestrated response
        """
        # Validate incoming state
        if not self.validate_state(state):
            return self.handle_error(state, Exception("Invalid state provided"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        self.log_processing(query, user_id)
        
        try:
            # Analyze query to determine routing strategy
            routing_decision = self._analyze_query_routing(query, user_id)
            
            if routing_decision["strategy"] == "single_agent":
                result = self._handle_single_agent(state, routing_decision)
            elif routing_decision["strategy"] == "multi_agent":
                result = self._handle_multi_agent(state, routing_decision)
            else:
                result = self._handle_fallback(state)
            
            # Store orchestration decision in memory
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=f"Orchestration: {routing_decision['strategy']} - {routing_decision.get('reason', '')}",
                interaction_type='orchestration',
                metadata={
                    "strategy": routing_decision["strategy"],
                    "selected_agents": routing_decision.get("agents", []),
                    "confidence": routing_decision.get("confidence", 0)
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in OrchestratorAgent: {e}")
            return self.handle_error(state, e)
    
    def get_capabilities(self) -> List[str]:
        """
        Return orchestrator capabilities
        
        Returns:
            List of OrchestratorAgent capabilities
        """
        return self._capabilities
    
    def _build_routing_patterns(self) -> Dict[str, List[str]]:
        """
        Build routing patterns dynamically based on available agents and their capabilities
        
        Returns:
            Dict mapping agent IDs to their routing patterns
        """
        patterns = {}
        
        # Default patterns for known agent types
        default_patterns = {
            "SearchAgent": [
                r"search.*history", r"find.*similar", r"what.*said.*before",
                r"previous.*conversation", r"recall", r"remember",
                r"search", r"similar", r"history"
            ],
            "ScenicLocationFinderAgent": [
                r"scenic.*location", r"beautiful.*place", r"tourist.*spot",
                r"landscape", r"scenic", r"beautiful", r"tourism", r"visit", r"travel",
                r"destination", r"sightseeing", r"attraction"
            ],
            "ForestAnalyzerAgent": [
                r"forest", r"tree", r"woodland", r"ecosystem.*forest",
                r"deforestation", r"biodiversity.*forest", r"conservation.*forest",
                r"wildlife", r"habitat", r"ecosystem"
            ],
            "WaterBodyAnalyzer": [
                r"water.*body", r"lake", r"river", r"ocean", r"sea", r"pond",
                r"hydrology", r"aquatic", r"marine", r"water.*quality"
            ]
        }
        
        # Build patterns for each available agent
        for agent_id, agent_data in self.available_agents.items():
            if agent_id in default_patterns:
                patterns[agent_id] = default_patterns[agent_id]
            else:
                # Generate patterns from capabilities
                agent_patterns = []
                capabilities = agent_data.get("capabilities", [])
                
                for capability in capabilities:
                    # Convert capability names to regex patterns
                    capability_words = capability.lower().replace("_", " ").split()
                    for word in capability_words:
                        if len(word) > 3:  # Skip short words
                            agent_patterns.append(word)
                
                if agent_patterns:
                    patterns[agent_id] = agent_patterns
                else:
                    # Fallback: use agent name
                    agent_name_words = agent_id.lower().replace("agent", "").split()
                    patterns[agent_id] = [word for word in agent_name_words if len(word) > 3]
        
        return patterns
    
    def _analyze_query_routing(self, query: str, user_id: int) -> Dict[str, Any]:
        """
        Analyze query to determine which agents should handle it
        
        Args:
            query: User query
            user_id: User identifier
            
        Returns:
            Routing decision with strategy and selected agents
        """
        query_lower = query.lower()
        agent_scores = {}
        
        # Score agents based on pattern matching
        for agent_id, patterns in self.routing_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    score += 1
            
            if score > 0:
                agent_scores[agent_id] = score
        
        # Enhance scoring with memory-based context
        memory_context = self._get_memory_routing_context(query, user_id)
        if memory_context:
            for agent_id, context_score in memory_context.items():
                if agent_id in agent_scores:
                    agent_scores[agent_id] += context_score * 0.5  # Weight memory context less than direct patterns
        
        # Use LLM for sophisticated routing if available
        if ollama_client.is_available():
            llm_routing = self._get_llm_routing_decision(query, agent_scores)
            if llm_routing and llm_routing.get("suggested_agents"):
                for agent_id in llm_routing["suggested_agents"]:
                    if agent_id in self.available_agents:
                        agent_scores[agent_id] = agent_scores.get(agent_id, 0) + 2
        
        # Determine routing strategy
        if not agent_scores:
            # No specific matches - use default fallback
            fallback_agents = self._get_fallback_agents()
            return {
                "strategy": "fallback",
                "agents": fallback_agents,
                "reason": "No specific agent pattern matched, using fallback"
            }
        elif len(agent_scores) == 1 or max(agent_scores.values()) >= 3:
            # Single agent if only one matches or one has high confidence
            best_agent = max(agent_scores, key=agent_scores.get)
            return {
                "strategy": "single_agent",
                "agents": [best_agent],
                "confidence": agent_scores[best_agent],
                "reason": f"Single agent {best_agent} best matches query (confidence: {agent_scores[best_agent]})"
            }
        else:
            # Multi-agent for queries that match multiple patterns
            selected_agents = [agent for agent, score in agent_scores.items() if score >= 1]
            return {
                "strategy": "multi_agent",
                "agents": selected_agents,
                "scores": agent_scores,
                "reason": f"Query requires coordination between {len(selected_agents)} agents"
            }
    
    def _get_memory_routing_context(self, query: str, user_id: int) -> Dict[str, int]:
        """
        Get routing context from user's memory and interaction history
        
        Args:
            query: Current query
            user_id: User identifier
            
        Returns:
            Dict mapping agent IDs to context scores
        """
        context_scores = {}
        
        try:
            # Get recent interactions to understand user patterns
            recent_interactions = self.get_recent_interactions(user_id, hours=6)
            
            for interaction in recent_interactions:
                agent_name = interaction.get("agent_id", "")
                if agent_name in self.available_agents:
                    # Give slight preference to recently used agents
                    context_scores[agent_name] = context_scores.get(agent_name, 0) + 1
            
            # Get similar queries from memory
            search_results = self.search_similar_content(query, user_id, limit=3)
            if search_results.get("similar_content"):
                for similar in search_results["similar_content"]:
                    agent_name = similar.get("agent_name", "")
                    if agent_name in self.available_agents:
                        # Weight by similarity score
                        similarity = similar.get("similarity", 0.0)
                        context_scores[agent_name] = context_scores.get(agent_name, 0) + int(similarity * 2)
            
        except Exception as e:
            logger.warning(f"Memory routing context failed: {e}")
        
        return context_scores
    
    def _get_llm_routing_decision(self, query: str, current_scores: Dict[str, int]) -> Dict:
        """
        Use LLM to make sophisticated routing decision
        
        Args:
            query: User query
            current_scores: Current agent scores from pattern matching
            
        Returns:
            LLM routing decision
        """
        try:
            # Build context with available agents and their capabilities
            agents_context = []
            for agent_id, agent_data in self.available_agents.items():
                agents_context.append(f"- {agent_id}: {', '.join(agent_data.get('capabilities', []))}")
            
            context = f"""
Available agents and capabilities:
{chr(10).join(agents_context)}

Current pattern matching scores: {current_scores}

Please analyze the query and suggest the most appropriate agent(s).
Return response as JSON with 'suggested_agents' list and 'reasoning'.
"""
            
            response = self.generate_response_with_context(
                query=f"Route this query to appropriate agents: {query}",
                context=context,
                temperature=0.1  # Low temperature for consistent routing
            )
            
            # Try to extract JSON from response
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
                
        except Exception as e:
            logger.warning(f"LLM routing decision failed: {e}")
        
        return {}
    
    def _get_fallback_agents(self) -> List[str]:
        """
        Get fallback agents when no specific routing is determined
        
        Returns:
            List of fallback agent IDs
        """
        # Prefer agents with general capabilities
        fallback_priority = [
            "ScenicLocationFinderAgent",  # General recommendations
            "SearchAgent",                # Can search for relevant info
            "TemplateAgent"               # Template for basic responses
        ]
        
        available_fallbacks = []
        for agent_id in fallback_priority:
            if agent_id in self.available_agents:
                available_fallbacks.append(agent_id)
        
        # If no preferred fallbacks, use first available agent
        if not available_fallbacks and self.available_agents:
            available_fallbacks = [list(self.available_agents.keys())[0]]
        
        return available_fallbacks[:1]  # Return only one fallback agent
    
    def _handle_single_agent(self, state: GraphState, routing_decision: Dict) -> GraphState:
        """
        Handle single agent routing
        
        Args:
            state: Current state
            routing_decision: Routing decision
            
        Returns:
            Updated state with single agent response
        """
        agent_id = routing_decision["agents"][0]
        user_id = state.get("user_id", 0)
        query = state.get("question", "")
        
        logger.info(f"Routing to single agent: {agent_id}")
        
        try:
            # Import registry to get instance
            from ..registry import agent_registry
            
            # Create agent instance using new registry
            agent_instance = agent_registry.create_agent_instance(agent_id, self.memory)
            if not agent_instance:
                return self._handle_fallback(state)
            
            # Process with the selected agent
            result = agent_instance.process(state)
            
            # Add orchestration metadata
            orchestration_info = {
                "strategy": "single_agent",
                "selected_agent": agent_id,
                "reason": routing_decision["reason"],
                "confidence": routing_decision.get("confidence", 1)
            }
            
            result["orchestration"] = orchestration_info
            return result
            
        except Exception as e:
            logger.error(f"Error in single agent routing: {e}")
            return self._handle_fallback(state)
    
    def _handle_multi_agent(self, state: GraphState, routing_decision: Dict) -> GraphState:
        """
        Handle multi-agent orchestration
        
        Args:
            state: Current state
            routing_decision: Routing decision
            
        Returns:
            Updated state with multi-agent response
        """
        agent_ids = routing_decision["agents"]
        user_id = state.get("user_id", 0)
        query = state.get("question", "")
        
        logger.info(f"Multi-agent orchestration with: {agent_ids}")
        
        try:
            agent_responses = []
            
            # Process query with each selected agent
            for agent_id in agent_ids:
                try:
                    # Import registry for each agent instance
                    from ..registry import agent_registry
                    agent_instance = agent_registry.create_agent_instance(agent_id, self.memory)
                    if agent_instance:
                        result = agent_instance.process(state)
                        agent_responses.append({
                            "agent": agent_id,
                            "response": result.get("response", ""),
                            "success": not result.get("error", False),
                            "capabilities": agent_instance.get_capabilities()
                        })
                except Exception as e:
                    logger.error(f"Error processing with agent {agent_id}: {e}")
                    agent_responses.append({
                        "agent": agent_id,
                        "response": f"Agent error: {str(e)}",
                        "success": False
                    })
            
            # Synthesize responses
            combined_response = self._synthesize_multi_agent_responses(query, agent_responses)
            
            return self.format_state_response(
                state,
                combined_response,
                {
                    "orchestration": {
                        "strategy": "multi_agent",
                        "agents": agent_ids,
                        "individual_responses": agent_responses,
                        "reason": routing_decision["reason"]
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Error in multi-agent orchestration: {e}")
            return self._handle_fallback(state)
    
    def _synthesize_multi_agent_responses(self, query: str, agent_responses: List[Dict]) -> str:
        """
        Synthesize multiple agent responses into coherent answer
        
        Args:
            query: Original query
            agent_responses: List of agent responses
            
        Returns:
            Synthesized response
        """
        if not agent_responses:
            return "No agent responses available"
        
        # Filter successful responses
        successful_responses = [r for r in agent_responses if r["success"]]
        if not successful_responses:
            return "All agents encountered errors during processing"
        
        # If only one successful response, return it
        if len(successful_responses) == 1:
            return successful_responses[0]["response"]
        
        # Use LLM to synthesize multiple responses if available
        if ollama_client.is_available() and len(successful_responses) > 1:
            try:
                synthesis_context = self._format_responses_for_synthesis(successful_responses)
                
                synthesized = self.generate_response_with_context(
                    query=f"Synthesize these agent responses for the query: {query}",
                    context=synthesis_context,
                    temperature=0.5
                )
                
                # Format final response
                final_response = f"🤖 **Multi-Agent Orchestrated Response**\n\n{synthesized}\n\n"
                final_response += "**Agent Contributions:**\n"
                for resp in successful_responses:
                    capabilities = ', '.join(resp.get('capabilities', []))
                    final_response += f"- **{resp['agent']}** ({capabilities}): {resp['response'][:150]}...\n"
                
                return final_response
                
            except Exception as e:
                logger.error(f"Error synthesizing responses: {e}")
        
        # Fallback: concatenate responses
        combined = "🤖 **Multi-Agent Response:**\n\n"
        for i, response in enumerate(successful_responses, 1):
            combined += f"**{response['agent']} ({i}/{len(successful_responses)}):**\n"
            combined += f"{response['response']}\n\n"
        
        return combined
    
    def _format_responses_for_synthesis(self, responses: List[Dict]) -> str:
        """
        Format agent responses for LLM synthesis
        
        Args:
            responses: List of agent responses
            
        Returns:
            Formatted context string
        """
        formatted = []
        for i, response in enumerate(responses, 1):
            agent_name = response["agent"]
            capabilities = ', '.join(response.get('capabilities', []))
            content = response["response"]
            formatted.append(f"{i}. **{agent_name}** ({capabilities}): {content}")
        
        return "\n\n".join(formatted)
    
    def _handle_fallback(self, state: GraphState) -> GraphState:
        """
        Handle fallback when no specific routing is determined
        
        Args:
            state: Current state
            
        Returns:
            Updated state with fallback response
        """
        fallback_agents = self._get_fallback_agents()
        
        if not fallback_agents:
            return self.format_state_response(
                state,
                "No available agents for processing this query",
                {"error": True, "orchestration": {"strategy": "no_agents"}}
            )
        
        fallback_agent_id = fallback_agents[0]
        logger.info(f"Using fallback agent: {fallback_agent_id}")
        
        try:
            from ..registry import agent_registry
            agent_instance = agent_registry.create_agent_instance(fallback_agent_id, self.memory)
            if agent_instance:
                result = agent_instance.process(state)
                result["orchestration"] = {
                    "strategy": "fallback",
                    "selected_agent": fallback_agent_id,
                    "reason": "Default fallback when no specific routing determined"
                }
                return result
                
        except Exception as e:
            logger.error(f"Fallback agent failed: {e}")
        
        return self.format_state_response(
            state,
            "All agent routing options failed. Please try rephrasing your query.",
            {"error": True, "orchestration": {"strategy": "complete_failure"}}
        )
    
    # Orchestrator-specific methods
    def get_agent_usage_analytics(self, user_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics on agent usage patterns for a user
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Agent usage analytics
        """
        try:
            historical_context = self.get_historical_context(user_id, days)
            
            agent_usage = {}
            orchestration_strategies = {}
            
            for interaction in historical_context:
                # Count agent usage
                if 'orchestration' in interaction.get('output_text', ''):
                    # Try to extract orchestration info
                    output = interaction.get('output_text', '')
                    if 'single_agent' in output:
                        orchestration_strategies['single_agent'] = orchestration_strategies.get('single_agent', 0) + 1
                    elif 'multi_agent' in output:
                        orchestration_strategies['multi_agent'] = orchestration_strategies.get('multi_agent', 0) + 1
                    elif 'fallback' in output:
                        orchestration_strategies['fallback'] = orchestration_strategies.get('fallback', 0) + 1
            
            return {
                "user_id": user_id,
                "analysis_period_days": days,
                "total_orchestrations": len(historical_context),
                "orchestration_strategies": orchestration_strategies,
                "available_agents": list(self.available_agents.keys()),
                "agent": self.name
            }
            
        except Exception as e:
            logger.warning(f"Agent usage analytics failed: {e}")
            return {"error": str(e), "agent": self.name}
    
    def refresh_available_agents(self) -> None:
        """
        Refresh the list of available agents from registry
        """
        try:
            from ..registry import agent_registry
            agent_registry.refresh()
            self.available_agents = agent_registry.get_all_agents()
            self.routing_patterns = self._build_routing_patterns()
            logger.info(f"Refreshed available agents: {len(self.available_agents)} agents")
        except Exception as e:
            logger.error(f"Failed to refresh available agents: {e}")
