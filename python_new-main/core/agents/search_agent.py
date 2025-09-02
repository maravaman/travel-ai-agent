"""
Vector-based similarity search agent
Constraint: Works with vector embeddings to match history and return JSON responses
Inherits from BaseAgent for consistent memory management and search functionality
"""
import json
import logging
from typing import Dict, Any, List
from ..base_agent import BaseAgent, GraphState
from ..memory import MemoryManager
from ..ollama_client import ollama_client, prompt_manager

logger = logging.getLogger(__name__)

class SearchAgent(BaseAgent):
    """Agent specialized in similarity search of user history using vector embeddings"""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize SearchAgent with memory management and search capabilities
        
        Args:
            memory_manager: MemoryManager instance for STM and LTM operations
        """
        super().__init__(memory_manager, "SearchAgent")
        
        # Override base capabilities with search-specific ones
        self._capabilities = ["similarity_search", "vector_embedding", "json_response", "cross_agent_search"]
        self._description = "Vector-based similarity search agent that finds similar content from user history and returns JSON responses"
        
        logger.info("SearchAgent initialized with enhanced memory management and search capabilities")
    
    def process(self, state: GraphState) -> GraphState:
        """
        Process search query using vector similarity search
        Returns results in JSON format as per constraint requirement
        
        Args:
            state: Current GraphState containing user query and context
            
        Returns:
            Updated GraphState with search results in JSON format
        """
        # Validate incoming state
        if not self.validate_state(state):
            return self.handle_error(state, Exception("Invalid state provided"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        self.log_processing(query, user_id)
        
        try:
            # Get similarity search results as JSON using base class memory management
            search_results = self.search_similar_content(query, user_id)
            
            # Enhanced search - also get cross-agent history
            cross_agent_results = self.search_cross_agent_history(query, user_id)
            
            # Get formatted prompt for the search agent
            context = self._format_context(search_results, cross_agent_results)
            
            # Generate response using LLM with context
            if ollama_client.is_available():
                response = self.generate_response_with_context(
                    query=query,
                    context=context,
                    temperature=0.3  # Lower temperature for focused search results
                )
                
                # Try to extract JSON from response, fallback to structured format
                try:
                    # Check if response contains valid JSON
                    if '{' in response and '}' in response:
                        json_start = response.find('{')
                        json_end = response.rfind('}') + 1
                        json_str = response[json_start:json_end]
                        parsed_json = json.loads(json_str)
                        final_response = json.dumps(parsed_json, indent=2)
                    else:
                        # Create structured JSON response
                        final_response = json.dumps({
                            "search_results": search_results,
                            "cross_agent_results": cross_agent_results,
                            "analysis": response,
                            "agent": self.name,
                            "query": query
                        }, indent=2)
                except json.JSONDecodeError:
                    # Fallback to structured response
                    final_response = json.dumps({
                        "search_results": search_results,
                        "cross_agent_results": cross_agent_results,
                        "analysis": response,
                        "agent": self.name,
                        "query": query,
                        "note": "LLM response was not valid JSON, wrapped in structured format"
                    }, indent=2)
            else:
                # Fallback when Ollama is not available
                final_response = json.dumps({
                    "search_results": search_results,
                    "cross_agent_results": cross_agent_results,
                    "message": "Vector similarity search completed. Ollama not available for analysis.",
                    "agent": self.name,
                    "query": query
                }, indent=2)
            
            # Store this search interaction using inherited memory management
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=final_response,
                interaction_type='search',
                metadata={"search_type": "similarity", "results_count": len(search_results.get("similar_content", []))}
            )
            
            # Store search query as vector embedding for future searches
            self.store_vector_embedding(
                user_id=user_id,
                content=query,
                metadata={"type": "search_query", "timestamp": search_results.get("timestamp", "")}
            )
            
            return self.format_state_response(
                state,
                final_response,
                {"response_type": "json"}
            )
            
        except Exception as e:
            logger.error(f"Error in SearchAgent processing: {e}")
            return self.handle_error(state, e)
    
    def get_capabilities(self) -> List[str]:
        """
        Return agent capabilities
        
        Returns:
            List of SearchAgent capabilities
        """
        return self._capabilities
    
    def _format_context(self, search_results: Dict, cross_agent_results: Dict) -> str:
        """
        Format search results as context for the LLM
        
        Args:
            search_results: Results from similarity search
            cross_agent_results: Results from cross-agent search
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Format similarity search results
        if search_results.get("similar_content"):
            context_parts.append("Similar content found:")
            for i, item in enumerate(search_results["similar_content"][:5], 1):
                similarity = item.get('similarity', 0.0)
                agent_name = item.get('agent_name', 'Unknown')
                content = item.get('content', '')[:100]
                context_parts.append(f"{i}. [{agent_name}] {content} (similarity: {similarity:.2f})")
        
        # Format recent interactions
        if search_results.get("recent_interactions"):
            context_parts.append("\nRecent interactions:")
            for i, interaction in enumerate(search_results["recent_interactions"][:3], 1):
                agent_name = interaction.get('agent_name', 'Unknown')
                query = interaction.get('query', '')[:50]
                context_parts.append(f"{i}. [{agent_name}] Q: {query}...")
        
        # Add cross-agent search context
        if cross_agent_results.get("search_results"):
            context_parts.append("\nCross-agent search results available in JSON format")
        
        return "\n".join(context_parts) if context_parts else "No relevant context found"
    
    # Additional search-specific methods
    def search_by_agent(self, query: str, user_id: int, target_agent: str) -> Dict[str, Any]:
        """
        Search for content from a specific agent
        
        Args:
            query: Search query
            user_id: User identifier
            target_agent: Specific agent to search
            
        Returns:
            Search results from specific agent
        """
        try:
            if hasattr(self.memory, 'get_search_history_json'):
                return self.memory.get_search_history_json(
                    query=query,
                    user_id=user_id,
                    agent_name=target_agent
                )
            else:
                # Fallback to historical context
                historical = self.get_historical_context(user_id)
                filtered = [h for h in historical if h.get('agent_id') == target_agent]
                return {
                    "similar_content": filtered[:5],
                    "query": query,
                    "target_agent": target_agent
                }
        except Exception as e:
            logger.warning(f"Agent-specific search failed: {e}")
            return {"similar_content": [], "query": query, "target_agent": target_agent, "error": str(e)}
    
    def get_search_analytics(self, user_id: int) -> Dict[str, Any]:
        """
        Get search analytics for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Search analytics data
        """
        try:
            recent_interactions = self.get_recent_interactions(user_id, hours=24)
            historical_context = self.get_historical_context(user_id, days=30)
            
            return {
                "recent_searches": len([i for i in recent_interactions if "search" in i.get("value", "").lower()]),
                "total_interactions": len(historical_context),
                "agent": self.name,
                "user_id": user_id
            }
        except Exception as e:
            logger.warning(f"Search analytics failed: {e}")
            return {"error": str(e), "agent": self.name, "user_id": user_id}
