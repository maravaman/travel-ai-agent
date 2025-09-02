"""
Forest ecosystem analysis agent
Constraint: Analyzes forest-related queries with biodiversity and conservation insights
Inherits from BaseAgent for consistent memory management and search functionality
"""
import logging
from typing import Dict, Any, List
from ..base_agent import BaseAgent, GraphState
from ..memory import MemoryManager
from ..location_extractor import location_extractor

logger = logging.getLogger(__name__)

class ForestAnalyzerAgent(BaseAgent):
    """Agent specialized in forest ecosystem analysis, biodiversity, and conservation"""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize ForestAnalyzerAgent with memory management and search capabilities
        
        Args:
            memory_manager: MemoryManager instance for STM and LTM operations
        """
        super().__init__(memory_manager, "ForestAnalyzerAgent")
        
        # Override base capabilities with forest-specific ones
        self._capabilities = [
            "forest_analysis", 
            "biodiversity_assessment", 
            "conservation_insights", 
            "ecosystem_evaluation",
            "location_extraction",
            "environmental_impact"
        ]
        self._description = "Specialized agent for forest ecosystem analysis, biodiversity assessment, and conservation insights"
        
        logger.info("ForestAnalyzerAgent initialized with enhanced memory management and search capabilities")
    
    def process(self, state: GraphState) -> GraphState:
        """
        Process forest-related queries with ecosystem analysis
        
        Args:
            state: Current GraphState containing user query and context
            
        Returns:
            Updated GraphState with forest analysis response
        """
        # Validate incoming state
        if not self.validate_state(state):
            return self.handle_error(state, Exception("Invalid state provided"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        self.log_processing(query, user_id)
        
        try:
            # Extract location from query for context
            detected_location = location_extractor.extract_location(query)
            
            # Search for similar forest-related content in memory
            search_results = self.search_similar_content(query, user_id)
            
            # Get historical forest analysis context
            historical_context = self.get_historical_context(user_id, days=30)
            forest_history = [h for h in historical_context if 'forest' in h.get('input_text', '').lower()]
            
            # Build context for response generation
            context = self._build_forest_context(query, detected_location, search_results, forest_history)
            
            # Generate comprehensive forest analysis response
            if hasattr(self, 'generate_response_with_context'):
                response = self.generate_response_with_context(
                    query=query,
                    context=context,
                    temperature=0.6  # Balanced temperature for informative responses
                )
            else:
                response = self._generate_fallback_response(query, detected_location, context)
            
            # Enhance response with forest-specific analysis
            enhanced_response = self._enhance_forest_response(response, query, detected_location)
            
            # Store this interaction using inherited memory management
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type='forest_analysis',
                metadata={
                    "analysis_type": "forest_ecosystem",
                    "location": detected_location,
                    "similar_queries": len(search_results.get("similar_content", []))
                }
            )
            
            # Store forest-related content as vector embedding
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Forest analysis: {query}",
                metadata={
                    "type": "forest_analysis",
                    "location": detected_location,
                    "analysis_aspects": self._extract_analysis_aspects(query)
                }
            )
            
            return self.format_state_response(
                state,
                enhanced_response,
                {"analysis_type": "forest_ecosystem", "location": detected_location}
            )
            
        except Exception as e:
            logger.error(f"Error in ForestAnalyzerAgent processing: {e}")
            return self.handle_error(state, e)
    
    def get_capabilities(self) -> List[str]:
        """
        Return agent capabilities
        
        Returns:
            List of ForestAnalyzerAgent capabilities
        """
        return self._capabilities
    
    def _build_forest_context(self, query: str, location: str, search_results: Dict, 
                             forest_history: List) -> str:
        """
        Build context for forest analysis
        
        Args:
            query: User's forest-related query
            location: Detected location (if any)
            search_results: Similar content from memory
            forest_history: Previous forest-related interactions
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add location context if available
        if location:
            context_parts.append(f"Location context: {location}")
        
        # Add similar forest content
        if search_results.get("similar_content"):
            context_parts.append("Similar forest-related content:")
            for item in search_results["similar_content"][:3]:
                content = item.get('content', '')[:150]
                context_parts.append(f"- {content}")
        
        # Add historical forest analysis
        if forest_history:
            context_parts.append("Previous forest analyses:")
            for analysis in forest_history[:2]:
                input_text = analysis.get('input_text', '')[:100]
                context_parts.append(f"- Previous query: {input_text}")
        
        # Add forest analysis guidelines
        context_parts.extend([
            "",
            "Forest Analysis Guidelines:",
            "- Assess biodiversity and ecosystem health",
            "- Consider conservation implications",
            "- Evaluate environmental impact factors",
            "- Provide actionable insights when possible"
        ])
        
        return "\n".join(context_parts)
    
    def _generate_fallback_response(self, query: str, location: str, context: str) -> str:
        """
        Generate fallback response when LLM is not available
        
        Args:
            query: User query
            location: Detected location
            context: Analysis context
            
        Returns:
            Fallback forest analysis response
        """
        response_parts = []
        
        if location:
            response_parts.append(f"Forest ecosystem analysis for {location}:")
        else:
            response_parts.append("Forest ecosystem analysis:")
        
        # Analyze query for specific forest aspects
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['biodiversity', 'species', 'wildlife']):
            response_parts.append("🌿 Biodiversity Assessment: Forest ecosystems support diverse species communities. Analysis requires detailed species inventory and habitat evaluation.")
        
        if any(word in query_lower for word in ['conservation', 'protect', 'preserve']):
            response_parts.append("🛡️ Conservation Insights: Forest conservation strategies should focus on habitat preservation, sustainable management, and community engagement.")
        
        if any(word in query_lower for word in ['deforestation', 'logging', 'clear']):
            response_parts.append("⚠️ Environmental Impact: Deforestation has significant impacts on carbon storage, water cycles, and biodiversity. Sustainable alternatives should be considered.")
        
        if any(word in query_lower for word in ['ecosystem', 'health', 'condition']):
            response_parts.append("🌲 Ecosystem Health: Forest health indicators include canopy cover, soil quality, water resources, and species diversity.")
        
        # Add general forest analysis
        if len(response_parts) == 1:  # Only header added
            response_parts.append("Forest ecosystem analysis covers biodiversity, conservation status, environmental impacts, and sustainable management practices.")
        
        response_parts.append("\n💡 For detailed analysis with specific recommendations, ensure Ollama is running for AI-powered insights.")
        
        return "\n\n".join(response_parts)
    
    def _enhance_forest_response(self, response: str, query: str, location: str) -> str:
        """
        Enhance response with forest-specific formatting and insights
        
        Args:
            response: Generated response
            query: Original query
            location: Detected location
            
        Returns:
            Enhanced forest analysis response
        """
        enhanced_parts = [f"🌲 **Forest Analysis Response** 🌲\n"]
        
        if location:
            enhanced_parts.append(f"📍 **Location**: {location}\n")
        
        enhanced_parts.append(f"**Analysis**: {response}\n")
        
        # Add forest analysis summary
        query_lower = query.lower()
        analysis_aspects = []
        
        if 'biodiversity' in query_lower:
            analysis_aspects.append("Biodiversity Assessment")
        if 'conservation' in query_lower:
            analysis_aspects.append("Conservation Analysis")
        if 'ecosystem' in query_lower:
            analysis_aspects.append("Ecosystem Evaluation")
        if 'impact' in query_lower:
            analysis_aspects.append("Environmental Impact")
        
        if analysis_aspects:
            enhanced_parts.append(f"**Analysis Aspects**: {', '.join(analysis_aspects)}\n")
        
        enhanced_parts.append("**Forest Analysis Agent** | Specialized in ecosystem evaluation and conservation insights")
        
        return "\n".join(enhanced_parts)
    
    def _extract_analysis_aspects(self, query: str) -> List[str]:
        """
        Extract forest analysis aspects from query
        
        Args:
            query: User query
            
        Returns:
            List of analysis aspects
        """
        query_lower = query.lower()
        aspects = []
        
        aspect_keywords = {
            "biodiversity": ["biodiversity", "species", "wildlife", "flora", "fauna"],
            "conservation": ["conservation", "protect", "preserve", "save"],
            "deforestation": ["deforestation", "logging", "clear", "cut"],
            "ecosystem": ["ecosystem", "health", "condition", "balance"],
            "climate": ["climate", "carbon", "co2", "greenhouse"],
            "sustainability": ["sustainable", "management", "practice"]
        }
        
        for aspect, keywords in aspect_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                aspects.append(aspect)
        
        return aspects if aspects else ["general_forest_analysis"]
    
    # Forest-specific analysis methods
    def analyze_biodiversity_factors(self, query: str, user_id: int) -> Dict[str, Any]:
        """
        Analyze biodiversity factors in forest query
        
        Args:
            query: Forest-related query
            user_id: User identifier
            
        Returns:
            Biodiversity analysis results
        """
        try:
            # Search for biodiversity-related content
            biodiversity_search = self.search_similar_content(f"biodiversity {query}", user_id)
            
            # Extract biodiversity indicators from query
            indicators = []
            query_lower = query.lower()
            
            if 'species' in query_lower:
                indicators.append("species_diversity")
            if 'habitat' in query_lower:
                indicators.append("habitat_quality")
            if 'endemic' in query_lower:
                indicators.append("endemic_species")
            if 'endangered' in query_lower:
                indicators.append("threatened_species")
            
            return {
                "biodiversity_indicators": indicators,
                "related_content": biodiversity_search.get("similar_content", []),
                "analysis_type": "biodiversity",
                "agent": self.name
            }
            
        except Exception as e:
            logger.warning(f"Biodiversity analysis failed: {e}")
            return {"error": str(e), "analysis_type": "biodiversity"}
    
    def assess_conservation_priority(self, query: str, user_id: int) -> Dict[str, Any]:
        """
        Assess conservation priority based on query
        
        Args:
            query: Conservation-related query
            user_id: User identifier
            
        Returns:
            Conservation priority assessment
        """
        try:
            # Determine conservation priority factors
            priority_factors = []
            query_lower = query.lower()
            
            if any(word in query_lower for word in ['endangered', 'threatened', 'rare']):
                priority_factors.append("species_protection")
            if any(word in query_lower for word in ['habitat', 'corridor', 'fragmentation']):
                priority_factors.append("habitat_connectivity")
            if any(word in query_lower for word in ['old growth', 'primary', 'virgin']):
                priority_factors.append("old_growth_preservation")
            if any(word in query_lower for word in ['water', 'watershed', 'stream']):
                priority_factors.append("watershed_protection")
            
            # Search for related conservation efforts
            conservation_search = self.search_similar_content(f"conservation {query}", user_id)
            
            return {
                "priority_factors": priority_factors,
                "conservation_level": "high" if len(priority_factors) > 2 else "medium" if priority_factors else "standard",
                "related_efforts": conservation_search.get("similar_content", []),
                "analysis_type": "conservation_priority",
                "agent": self.name
            }
            
        except Exception as e:
            logger.warning(f"Conservation priority assessment failed: {e}")
            return {"error": str(e), "analysis_type": "conservation_priority"}
