"""
Abstract base agent class for LangGraph multi-agent system
Constraint: All agents inherit from this base class for consistent memory management and search functionality
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypedDict
import logging
from .memory import MemoryManager
from .ollama_client import ollama_client, prompt_manager

logger = logging.getLogger(__name__)

# Define GraphState for type hinting
class GraphState(TypedDict, total=False):
    user: str
    user_id: int
    question: str
    agent: str
    response: str
    orchestration: dict

class BaseAgent(ABC):
    """
    Abstract base class that all agents must inherit from.
    Provides standardized memory management, search capabilities, and interface methods.
    """
    
    def __init__(self, memory_manager: MemoryManager, name: str = None):
        """
        Initialize base agent with memory management and search capabilities
        
        Args:
            memory_manager: MemoryManager instance for STM and LTM operations
            name: Agent name (auto-derived from class name if not provided)
        """
        self.memory = memory_manager
        self.name = name or self.__class__.__name__.replace("Agent", "")
        
        # Store reference to search agent (initialized lazily to avoid circular imports)
        self._search_agent = None
        
        # Agent capabilities - should be overridden by subclasses
        self._capabilities = ["base_functionality"]
        
        # Agent description - should be overridden by subclasses
        self._description = "Base agent with memory management and search capabilities"
        
        logger.info(f"Initialized {self.__class__.__name__} with memory management and search")
    
    @abstractmethod
    def process(self, state: GraphState) -> GraphState:
        """
        Main processing method that each agent must implement.
        
        Args:
            state: Current GraphState containing user query and context
            
        Returns:
            Updated GraphState with agent response
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """
        Return list of agent capabilities.
        Must be implemented by each agent.
        
        Returns:
            List of capability strings
        """
        pass
    
    def can_handle(self, query: str) -> float:
        """
        Determine if this agent can handle a specific query
        
        Args:
            query: The input query
            
        Returns:
            Float between 0 and 1 indicating confidence level
        """
        if not hasattr(self, 'keywords'):
            return 0.0
            
        query_lower = query.lower()
        keywords = getattr(self, 'keywords', [])
        
        if not keywords:
            return 0.0
            
        keyword_matches = sum(1 for keyword in keywords if keyword.lower() in query_lower)
        confidence = min(keyword_matches / len(keywords), 1.0) if keywords else 0.0
        
        return confidence
    
    def get_description(self) -> str:
        """
        Return agent description.
        Can be overridden by subclasses.
        
        Returns:
            Agent description string
        """
        return self._description
    
    def get_name(self) -> str:
        """
        Return agent name.
        
        Returns:
            Agent name string
        """
        return self.name
    
    # ----------------------
    # MEMORY MANAGEMENT METHODS
    # ----------------------
    
    def store_interaction(self, user_id: int, query: str, response: str, 
                         interaction_type: str = 'single', metadata: Dict = None):
        """
        Store interaction in agent's memory (both STM and LTM)
        
        Args:
            user_id: User identifier
            query: User's query/input
            response: Agent's response
            interaction_type: Type of interaction ('single', 'orchestrated', etc.)
            metadata: Additional metadata to store
        """
        try:
            # Store in short-term memory (Redis)
            self.memory.set_stm(user_id, self.name, query)
            
            # Store in long-term memory (MySQL)
            self.memory.store_ltm(user_id, self.name, query, response)
            
            # Store interaction with metadata if memory supports it
            if hasattr(self.memory, 'store_interaction'):
                self.memory.store_interaction(
                    user_id=user_id,
                    agent_name=self.name,
                    query=query,
                    response=response,
                    interaction_type=interaction_type,
                    metadata=metadata
                )
            
            logger.debug(f"{self.name} stored interaction for user {user_id}")
            
        except Exception as e:
            logger.warning(f"Failed to store interaction for {self.name}: {e}")
    
    def get_recent_interactions(self, user_id: int, hours: int = 2) -> List[Dict]:
        """
        Get recent interactions from memory
        
        Args:
            user_id: User identifier
            hours: Number of hours to look back
            
        Returns:
            List of recent interactions
        """
        try:
            return self.memory.get_recent_stm(user_id, self.name, hours)
        except Exception as e:
            logger.warning(f"Failed to get recent interactions for {self.name}: {e}")
            return []
    
    def get_historical_context(self, user_id: int, days: int = 7) -> List[Dict]:
        """
        Get historical context from long-term memory
        
        Args:
            user_id: User identifier
            days: Number of days to look back
            
        Returns:
            List of historical interactions
        """
        try:
            return self.memory.get_ltm_by_agent(user_id, self.name)
        except Exception as e:
            logger.warning(f"Failed to get historical context for {self.name}: {e}")
            return []
    
    def store_vector_embedding(self, user_id: int, content: str, metadata: Dict = None):
        """
        Store content as vector embedding for similarity search
        
        Args:
            user_id: User identifier
            content: Content to store as embedding
            metadata: Additional metadata
        """
        try:
            if hasattr(self.memory, 'store_vector_embedding'):
                self.memory.store_vector_embedding(
                    user_id=user_id,
                    agent_name=self.name,
                    content=content,
                    metadata=metadata or {}
                )
                logger.debug(f"{self.name} stored vector embedding for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to store vector embedding for {self.name}: {e}")
    
    # ----------------------
    # SEARCH CAPABILITIES
    # ----------------------
    
    def search_similar_content(self, query: str, user_id: int, limit: int = 5) -> Dict[str, Any]:
        """
        Search for similar content in memory using vector similarity
        
        Args:
            query: Search query
            user_id: User identifier
            limit: Maximum number of results
            
        Returns:
            Dictionary containing search results
        """
        try:
            if hasattr(self.memory, 'get_search_history_json'):
                return self.memory.get_search_history_json(
                    query=query,
                    user_id=user_id,
                    agent_name=self.name
                )
            else:
                # Fallback to basic search
                recent = self.get_recent_interactions(user_id)
                return {
                    "similar_content": recent[:limit],
                    "query": query,
                    "agent": self.name,
                    "timestamp": str(logger.info)
                }
        except Exception as e:
            logger.warning(f"Search failed for {self.name}: {e}")
            return {"similar_content": [], "query": query, "error": str(e)}
    
    def search_cross_agent_history(self, query: str, user_id: int) -> Dict[str, Any]:
        """
        Search across all agents' history for the user
        
        Args:
            query: Search query
            user_id: User identifier
            
        Returns:
            Dictionary containing cross-agent search results
        """
        try:
            # Create a temporary state for search
            search_state = {
                "question": query,
                "user_id": user_id,
                "user": str(user_id)
            }
            
            # Use internal search agent
            result = self._search_agent.process(search_state)
            return {
                "search_results": result.get("response", "{}"),
                "query": query,
                "search_type": "cross_agent"
            }
        except Exception as e:
            logger.warning(f"Cross-agent search failed for {self.name}: {e}")
            return {"search_results": "{}", "query": query, "error": str(e)}
    
    # ----------------------
    # LLM INTEGRATION METHODS
    # ----------------------
    
    def generate_response_with_context(self, query: str, context: str, 
                                     temperature: float = 0.7) -> str:
        """
        Generate response using LLM with context
        
        Args:
            query: User query
            context: Context information
            temperature: LLM temperature setting
            
        Returns:
            Generated response
        """
        try:
            if ollama_client.is_available():
                prompt_data = prompt_manager.get_prompt(
                    agent_name=self.name,
                    query=query,
                    context=context
                )
                
                response = ollama_client.generate_response(
                    prompt=prompt_data["prompt"],
                    system_prompt=prompt_data["system"],
                    temperature=temperature
                )
                
                return response
            else:
                return f"{self.name} response: {query} (Context: {context[:100]}...)"
                
        except Exception as e:
            logger.error(f"LLM response generation failed for {self.name}: {e}")
            return f"Error generating response: {str(e)}"
    
    # ----------------------
    # UTILITY METHODS
    # ----------------------
    
    def format_state_response(self, state: GraphState, response: str, 
                            additional_data: Dict = None) -> GraphState:
        """
        Format and return updated state with agent response
        
        Args:
            state: Current state
            response: Agent response
            additional_data: Additional data to include in state
            
        Returns:
            Updated GraphState
        """
        updated_state = state.copy()
        updated_state["agent"] = self.name
        updated_state["response"] = response
        
        if additional_data:
            updated_state.update(additional_data)
        
        return updated_state
    
    def log_processing(self, query: str, user_id: int = None):
        """
        Log agent processing activity
        
        Args:
            query: Query being processed
            user_id: User identifier
        """
        logger.info(f"{self.name} processing query: {query[:100]}..." + 
                   (f" for user {user_id}" if user_id else ""))
    
    def validate_state(self, state: GraphState) -> bool:
        """
        Validate incoming state has required fields
        
        Args:
            state: State to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["question"]
        for field in required_fields:
            if field not in state:
                logger.warning(f"{self.name} received invalid state: missing {field}")
                return False
        return True
    
    def handle_error(self, state: GraphState, error: Exception) -> GraphState:
        """
        Handle errors gracefully and return error state
        
        Args:
            state: Current state
            error: Exception that occurred
            
        Returns:
            Error state
        """
        error_msg = f"{self.name} error: {str(error)}"
        logger.error(error_msg)
        
        return self.format_state_response(
            state,
            error_msg,
            {"error": True}
        )
