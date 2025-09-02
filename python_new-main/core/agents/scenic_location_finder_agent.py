"""
Scenic location finder and recommendation agent
Constraint: Provides personalized travel suggestions and scenic location recommendations
Inherits from BaseAgent for consistent memory management and search functionality
"""
import logging
from typing import Dict, Any, List
from ..base_agent import BaseAgent, GraphState
from ..memory import MemoryManager
from ..location_extractor import location_extractor

logger = logging.getLogger(__name__)

class ScenicLocationFinderAgent(BaseAgent):
    """Agent specialized in finding scenic locations and providing travel recommendations"""
    
    def __init__(self, memory_manager: MemoryManager):
        """
        Initialize ScenicLocationFinderAgent with memory management and search capabilities
        
        Args:
            memory_manager: MemoryManager instance for STM and LTM operations
        """
        super().__init__(memory_manager, "ScenicLocationFinderAgent")
        
        # Override base capabilities with scenic location-specific ones
        self._capabilities = [
            "scenic_location_search", 
            "travel_recommendations", 
            "location_analysis", 
            "tourism_insights",
            "geographical_context",
            "personalized_suggestions"
        ]
        self._description = "Specialized agent for finding scenic locations and providing personalized travel recommendations"
        
        logger.info("ScenicLocationFinderAgent initialized with enhanced memory management and search capabilities")
    
    def process(self, state: GraphState) -> GraphState:
        """
        Process scenic location queries and provide travel recommendations
        
        Args:
            state: Current GraphState containing user query and context
            
        Returns:
            Updated GraphState with scenic location recommendations
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
            
            # Search for similar scenic location queries in memory
            search_results = self.search_similar_content(query, user_id)
            
            # Get user's travel history and preferences
            travel_history = self.get_historical_context(user_id, days=90)
            scenic_history = [h for h in travel_history if any(word in h.get('input_text', '').lower() 
                                                             for word in ['scenic', 'travel', 'visit', 'beautiful', 'tourist'])]
            
            # Build context for personalized recommendations
            context = self._build_scenic_context(query, detected_location, search_results, scenic_history)
            
            # Generate personalized scenic location recommendations
            if hasattr(self, 'generate_response_with_context'):
                response = self.generate_response_with_context(
                    query=query,
                    context=context,
                    temperature=0.7  # Higher temperature for creative recommendations
                )
            else:
                response = self._generate_fallback_response(query, detected_location, context)
            
            # Enhance response with scenic location formatting
            enhanced_response = self._enhance_scenic_response(response, query, detected_location)
            
            # Store this interaction using inherited memory management
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type='scenic_recommendation',
                metadata={
                    "recommendation_type": "scenic_location",
                    "location": detected_location,
                    "user_preferences": self._extract_travel_preferences(query),
                    "similar_queries": len(search_results.get("similar_content", []))
                }
            )
            
            # Store travel preferences as vector embedding
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Scenic location query: {query}",
                metadata={
                    "type": "travel_preference",
                    "location": detected_location,
                    "preferences": self._extract_travel_preferences(query)
                }
            )
            
            return self.format_state_response(
                state,
                enhanced_response,
                {"recommendation_type": "scenic_location", "location": detected_location}
            )
            
        except Exception as e:
            logger.error(f"Error in ScenicLocationFinderAgent processing: {e}")
            return self.handle_error(state, e)
    
    def get_capabilities(self) -> List[str]:
        """
        Return agent capabilities
        
        Returns:
            List of ScenicLocationFinderAgent capabilities
        """
        return self._capabilities
    
    def _build_scenic_context(self, query: str, location: str, search_results: Dict, 
                             scenic_history: List) -> str:
        """
        Build context for scenic location recommendations
        
        Args:
            query: User's scenic location query
            location: Detected location (if any)
            search_results: Similar content from memory
            scenic_history: Previous travel-related interactions
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add location context if available
        if location:
            context_parts.append(f"Target location/region: {location}")
        
        # Add similar scenic queries
        if search_results.get("similar_content"):
            context_parts.append("Similar scenic location queries:")
            for item in search_results["similar_content"][:3]:
                content = item.get('content', '')[:150]
                context_parts.append(f"- {content}")
        
        # Add user's travel history and preferences
        if scenic_history:
            context_parts.append("User's travel history:")
            for travel in scenic_history[:3]:
                input_text = travel.get('input_text', '')[:100]
                context_parts.append(f"- Previous interest: {input_text}")
        
        # Add travel recommendation guidelines
        context_parts.extend([
            "",
            "Scenic Location Guidelines:",
            "- Provide specific location names when possible",
            "- Include accessibility and best visiting times",
            "- Consider different activity preferences (hiking, photography, relaxation)",
            "- Mention unique features and attractions",
            "- Suggest nearby complementary locations"
        ])
        
        return "\n".join(context_parts)
    
    def _generate_fallback_response(self, query: str, location: str, context: str) -> str:
        """
        Generate fallback response when LLM is not available
        
        Args:
            query: User query
            location: Detected location
            context: Recommendation context
            
        Returns:
            Fallback scenic location response
        """
        response_parts = []
        
        if location:
            response_parts.append(f"🌟 Scenic Location Recommendations for {location}:")
        else:
            response_parts.append("🌟 Scenic Location Recommendations:")
        
        # Analyze query for specific scenic preferences
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['mountain', 'peak', 'summit', 'hill']):
            response_parts.append("🏔️ Mountain Scenery: Consider mountain viewpoints, scenic overlooks, and hiking trails with panoramic vistas.")
        
        if any(word in query_lower for word in ['beach', 'coast', 'ocean', 'sea', 'shore']):
            response_parts.append("🏖️ Coastal Beauty: Explore pristine beaches, dramatic coastlines, and scenic coastal drives.")
        
        if any(word in query_lower for word in ['lake', 'river', 'waterfall', 'water']):
            response_parts.append("💧 Water Features: Discover serene lakes, flowing rivers, and spectacular waterfalls.")
        
        if any(word in query_lower for word in ['forest', 'woods', 'nature', 'wildlife']):
            response_parts.append("🌲 Natural Areas: Visit old-growth forests, nature preserves, and wildlife viewing areas.")
        
        if any(word in query_lower for word in ['sunset', 'sunrise', 'photography', 'photo']):
            response_parts.append("📸 Photography Spots: Seek locations known for stunning sunrises, sunsets, and photogenic landscapes.")
        
        if any(word in query_lower for word in ['historic', 'cultural', 'heritage', 'architecture']):
            response_parts.append("🏛️ Cultural Sites: Explore historic landmarks, architectural marvels, and culturally significant locations.")
        
        # Add general recommendations if no specific preferences detected
        if len(response_parts) == 1:  # Only header added
            response_parts.extend([
                "🌄 Natural Landscapes: National parks, scenic overlooks, and nature trails",
                "🏛️ Cultural Attractions: Historic sites, museums, and architectural landmarks",
                "🌊 Water Features: Lakes, rivers, waterfalls, and coastal areas",
                "🌸 Seasonal Highlights: Consider seasonal attractions like spring blooms or fall foliage"
            ])
        
        response_parts.append("\n💡 For personalized recommendations with specific locations and details, ensure Ollama is running for AI-powered travel insights.")
        
        return "\n\n".join(response_parts)
    
    def _enhance_scenic_response(self, response: str, query: str, location: str) -> str:
        """
        Enhance response with scenic location formatting and travel tips
        
        Args:
            response: Generated response
            query: Original query
            location: Detected location
            
        Returns:
            Enhanced scenic location response
        """
        enhanced_parts = [f"🌟 **Scenic Location Finder** 🌟\n"]
        
        if location:
            enhanced_parts.append(f"📍 **Target Region**: {location}\n")
        
        enhanced_parts.append(f"**Recommendations**: {response}\n")
        
        # Add travel preferences summary
        preferences = self._extract_travel_preferences(query)
        if preferences:
            enhanced_parts.append(f"**Detected Preferences**: {', '.join(preferences)}\n")
        
        # Add travel tips
        enhanced_parts.append("**Travel Tips**:")
        enhanced_parts.append("- Check weather conditions and seasonal accessibility")
        enhanced_parts.append("- Consider local regulations and park fees")
        enhanced_parts.append("- Plan for parking and transportation")
        enhanced_parts.append("- Bring appropriate gear for the activities\n")
        
        enhanced_parts.append("**Scenic Location Finder Agent** | Personalized travel recommendations")
        
        return "\n".join(enhanced_parts)
    
    def _extract_travel_preferences(self, query: str) -> List[str]:
        """
        Extract travel preferences from query
        
        Args:
            query: User query
            
        Returns:
            List of detected travel preferences
        """
        query_lower = query.lower()
        preferences = []
        
        preference_keywords = {
            "mountains": ["mountain", "peak", "summit", "alpine", "hill"],
            "water": ["beach", "lake", "river", "waterfall", "coast", "ocean"],
            "nature": ["forest", "nature", "wildlife", "park", "trail"],
            "photography": ["photo", "photography", "sunrise", "sunset", "scenic"],
            "culture": ["historic", "cultural", "heritage", "museum", "architecture"],
            "adventure": ["hiking", "climbing", "adventure", "outdoor", "active"],
            "relaxation": ["peaceful", "quiet", "relaxing", "serene", "calm"]
        }
        
        for preference, keywords in preference_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                preferences.append(preference)
        
        return preferences if preferences else ["general_sightseeing"]
    
    # Scenic location-specific methods
    def find_locations_by_type(self, location_type: str, region: str, user_id: int) -> Dict[str, Any]:
        """
        Find scenic locations by type and region
        
        Args:
            location_type: Type of location (e.g., "mountain", "beach", "forest")
            region: Geographic region
            user_id: User identifier
            
        Returns:
            Location search results
        """
        try:
            # Search for locations of specific type
            search_query = f"{location_type} {region} scenic"
            location_search = self.search_similar_content(search_query, user_id)
            
            # Get user's preferences for this location type
            user_history = self.get_historical_context(user_id, days=180)
            type_history = [h for h in user_history if location_type in h.get('input_text', '').lower()]
            
            return {
                "location_type": location_type,
                "region": region,
                "search_results": location_search.get("similar_content", []),
                "user_history": type_history[:5],
                "agent": self.name
            }
            
        except Exception as e:
            logger.warning(f"Location type search failed: {e}")
            return {"error": str(e), "location_type": location_type, "region": region}
    
    def get_travel_recommendations(self, user_id: int, preferences: List[str] = None) -> Dict[str, Any]:
        """
        Get personalized travel recommendations based on user history
        
        Args:
            user_id: User identifier
            preferences: Specific preferences to consider
            
        Returns:
            Personalized travel recommendations
        """
        try:
            # Get user's travel history
            travel_history = self.get_historical_context(user_id, days=365)
            
            # Extract patterns from user's queries
            location_mentions = []
            activity_patterns = []
            
            for interaction in travel_history:
                query = interaction.get('input_text', '').lower()
                if any(word in query for word in ['visit', 'travel', 'scenic', 'beautiful']):
                    # Extract mentioned locations and activities
                    if 'mountain' in query:
                        activity_patterns.append('mountain')
                    if 'beach' in query:
                        activity_patterns.append('beach')
                    if 'photo' in query or 'photography' in query:
                        activity_patterns.append('photography')
            
            # Generate recommendations based on patterns
            recommendations = {
                "user_patterns": list(set(activity_patterns)),
                "recommendation_count": len(travel_history),
                "preferences": preferences or [],
                "agent": self.name,
                "user_id": user_id
            }
            
            return recommendations
            
        except Exception as e:
            logger.warning(f"Travel recommendations failed: {e}")
            return {"error": str(e), "agent": self.name, "user_id": user_id}
    
    def analyze_seasonal_attractions(self, query: str, user_id: int) -> Dict[str, Any]:
        """
        Analyze seasonal attractions mentioned in query
        
        Args:
            query: User query
            user_id: User identifier
            
        Returns:
            Seasonal attraction analysis
        """
        try:
            query_lower = query.lower()
            seasonal_indicators = []
            
            # Detect seasonal preferences
            if any(word in query_lower for word in ['spring', 'bloom', 'flower']):
                seasonal_indicators.append("spring_blooms")
            if any(word in query_lower for word in ['summer', 'warm', 'sun']):
                seasonal_indicators.append("summer_activities")
            if any(word in query_lower for word in ['fall', 'autumn', 'foliage']):
                seasonal_indicators.append("fall_colors")
            if any(word in query_lower for word in ['winter', 'snow', 'cold']):
                seasonal_indicators.append("winter_scenery")
            
            # Search for seasonal content
            seasonal_search = self.search_similar_content(f"seasonal {query}", user_id)
            
            return {
                "seasonal_indicators": seasonal_indicators,
                "seasonal_content": seasonal_search.get("similar_content", []),
                "analysis_type": "seasonal_attractions",
                "agent": self.name
            }
            
        except Exception as e:
            logger.warning(f"Seasonal analysis failed: {e}")
            return {"error": str(e), "analysis_type": "seasonal_attractions"}
