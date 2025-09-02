"""
Enhanced Mock Ollama Client
Provides intelligent mock responses when Ollama is not available
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EnhancedMockOllamaClient:
    """
    Mock Ollama client that provides intelligent responses based on context
    """
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.default_model = "llama3:8b"
        self.available = True  # Mock is always available
        
        logger.info("🎭 Enhanced Mock Ollama Client initialized")
    
    def is_available(self) -> bool:
        """Mock is always available"""
        return True
    
    def list_models(self) -> List[Dict[str, Any]]:
        """Return mock model list"""
        return [
            {
                "name": "llama3:8b",
                "size": 4661224676,
                "digest": "365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1",
                "details": {
                    "family": "llama",
                    "format": "gguf",
                    "parameter_size": "8B",
                    "quantization_level": "Q4_0"
                }
            }
        ]
    
    def generate_response(
        self, 
        prompt: str, 
        model: Optional[str] = None, 
        system_prompt: Optional[str] = None,
        context: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> str:
        """Generate intelligent mock response based on prompt and system context"""
        
        # Extract agent type from system prompt if available
        agent_type = "AI Assistant"
        if system_prompt:
            system_lower = system_prompt.lower()
            if "weather" in system_lower or "meteorologist" in system_lower:
                agent_type = "Weather Expert"
            elif "dining" in system_lower or "restaurant" in system_lower or "culinary" in system_lower:
                agent_type = "Dining Expert"
            elif "location" in system_lower or "scenic" in system_lower or "travel" in system_lower:
                agent_type = "Location Expert"
            elif "forest" in system_lower or "ecology" in system_lower or "conservation" in system_lower:
                agent_type = "Forest Expert"
            elif "search" in system_lower or "memory" in system_lower:
                agent_type = "Search Expert"
            elif "router" in system_lower or "orchestrat" in system_lower:
                agent_type = "Query Router"
        
        # Analyze prompt for context
        prompt_lower = prompt.lower()
        
        # Weather-related responses
        if any(word in prompt_lower for word in ["weather", "temperature", "rain", "sun", "climate", "forecast", "storm", "snow"]):
            return self._generate_weather_response(prompt, agent_type, context)
        
        # Dining-related responses
        elif any(word in prompt_lower for word in ["restaurant", "dining", "food", "cuisine", "eat", "meal", "lunch", "dinner", "chef", "menu"]):
            return self._generate_dining_response(prompt, agent_type, context)
        
        # Location-related responses
        elif any(word in prompt_lower for word in ["location", "scenic", "place", "visit", "destination", "tourist", "attraction", "view"]):
            return self._generate_location_response(prompt, agent_type, context)
        
        # Forest/nature-related responses
        elif any(word in prompt_lower for word in ["forest", "tree", "wildlife", "nature", "biodiversity", "ecosystem", "conservation"]):
            return self._generate_forest_response(prompt, agent_type, context)
        
        # Search-related responses
        elif any(word in prompt_lower for word in ["search", "history", "previous", "remember", "find", "lookup", "similar"]):
            return self._generate_search_response(prompt, agent_type, context)
        
        # Router/general responses
        else:
            return self._generate_general_response(prompt, agent_type, context)
    
    def _generate_weather_response(self, prompt: str, agent_type: str, context: List[str] = None) -> str:
        """Generate weather-specific mock response"""
        location = self._extract_location(prompt, context)
        location_text = f" for {location}" if location else ""
        
        return f"""🌤️ {agent_type} Analysis:

Current weather conditions{location_text} show typical seasonal patterns with moderate temperatures expected throughout the day.

**Today's Forecast:**
• Temperature: Mild to moderate range (varies by season)
• Conditions: Generally pleasant with possible cloud cover
• Wind: Light to moderate breezes
• Precipitation: Check local conditions for updates

**Weather Planning Advice:**
• Dress in layers for temperature changes
• Consider umbrella if clouds are present
• Outdoor activities are generally favorable
• Monitor local weather services for detailed forecasts

For the most accurate and up-to-date weather information, I recommend checking with local meteorological services. This analysis is based on general seasonal patterns."""
    
    def _generate_dining_response(self, prompt: str, agent_type: str, context: List[str] = None) -> str:
        """Generate dining-specific mock response"""
        location = self._extract_location(prompt, context)
        location_text = f" in {location}" if location else ""
        
        return f"""🍽️ {agent_type} Recommendations:

I can suggest excellent dining options{location_text} based on your preferences and the current context.

**Recommended Dining Categories:**
• **Local Specialties**: Restaurants featuring regional cuisine and traditional dishes
• **Farm-to-Table**: Establishments emphasizing fresh, locally-sourced ingredients
• **Seasonal Menus**: Places that adapt their offerings to seasonal availability
• **Diverse Cuisines**: Options including international and fusion restaurants

**Considerations for Your Selection:**
• Dietary preferences and restrictions
• Atmosphere and ambiance preferences
• Budget considerations
• Distance and accessibility
• Current weather conditions (outdoor seating, etc.)

**Popular Dining Times:**
• Lunch: 11:30 AM - 2:00 PM
• Dinner: 6:00 PM - 9:00 PM
• Reservations recommended for peak times

Would you like more specific recommendations based on particular cuisine types or dining preferences?"""
    
    def _generate_location_response(self, prompt: str, agent_type: str, context: List[str] = None) -> str:
        """Generate location-specific mock response"""
        return f"""📍 {agent_type} Suggestions:

Based on your inquiry, I can recommend several beautiful and interesting locations worth visiting.

**Scenic Categories:**
• **Natural Viewpoints**: Elevated locations offering panoramic views
• **Waterfront Areas**: Lakes, rivers, or coastal locations with scenic beauty
• **Historic Districts**: Areas with cultural significance and architectural interest
• **Parks & Recreation**: Public spaces ideal for outdoor activities
• **Photography Spots**: Locations known for excellent photo opportunities

**Best Visiting Practices:**
• **Timing**: Early morning or late afternoon often provide the best lighting
• **Seasonality**: Different locations shine in different seasons
• **Accessibility**: Consider transportation and walking requirements
• **Weather**: Current conditions affect visibility and accessibility

**Planning Tips:**
• Check operating hours for managed locations
• Consider parking availability
• Bring appropriate gear (camera, walking shoes, etc.)
• Respect environmental guidelines and local regulations

The best locations often combine natural beauty with cultural significance. Would you like more specific recommendations based on your interests or proximity preferences?"""
    
    def _generate_forest_response(self, prompt: str, agent_type: str, context: List[str] = None) -> str:
        """Generate forest/ecology-specific mock response"""
        return f"""🌲 {agent_type} Analysis:

Forest ecosystems in this region support diverse wildlife communities and represent important conservation areas.

**Ecological Characteristics:**
• **Biodiversity**: Multiple species of flora and fauna coexist
• **Canopy Structure**: Various layers supporting different ecological niches  
• **Wildlife Corridors**: Connected habitats enabling species migration
• **Soil Systems**: Complex underground networks supporting plant communities

**Conservation Considerations:**
• **Habitat Protection**: Maintaining undisturbed areas for wildlife
• **Sustainable Access**: Balancing public enjoyment with ecosystem preservation
• **Species Monitoring**: Tracking populations of key indicator species
• **Climate Adaptation**: Supporting ecosystem resilience to environmental changes

**Visitor Guidelines:**
• Stay on designated trails to minimize impact
• Observe wildlife from appropriate distances
• Pack out all waste materials
• Follow seasonal restrictions and closures
• Support local conservation efforts

**Best Observation Times:**
• Early morning: Active wildlife, good lighting
• Late afternoon: Animal movement, optimal photography
• Seasonal variations affect animal behavior and plant phenology

Forest health depends on maintaining the delicate balance of ecological relationships while allowing appropriate human interaction with these natural systems."""
    
    def _generate_search_response(self, prompt: str, agent_type: str, context: List[str] = None) -> str:
        """Generate search-specific mock response"""
        return f"""🔍 {agent_type} Results:

Based on analysis of historical interactions and memory patterns, I can provide insights about previous queries and related information.

**Search Analysis:**
• **Pattern Recognition**: Identifying recurring themes in past interactions
• **Contextual Connections**: Finding relationships between different queries
• **User Preferences**: Tracking interests and preferred information types
• **Temporal Patterns**: Understanding how interests evolve over time

**Available Search Types:**
• **Similarity Search**: Finding content related to current query
• **Historical Lookup**: Retrieving previous interactions and responses
• **Topic Clustering**: Grouping related queries and responses
• **Trend Analysis**: Identifying patterns in user interests

**Search Results Context:**
{self._format_context(context) if context else "No previous context available"}

**Memory Integration:**
• Short-term memory: Recent conversation context
• Long-term memory: Historical interaction patterns
• Cross-agent data: Information shared between different AI agents
• User preferences: Learned patterns from past interactions

For more specific search results, please provide additional context about what type of information you're looking for or which time period you're interested in exploring."""
    
    def _generate_general_response(self, prompt: str, agent_type: str, context: List[str] = None) -> str:
        """Generate general mock response"""
        return f"""💡 {agent_type} Response:

I understand your inquiry: "{prompt[:100]}{'...' if len(prompt) > 100 else ''}"

**Analysis:**
I'm currently operating in demonstration mode to provide helpful guidance while the full AI system is configured. Based on your query, I can offer general information and recommendations.

**Context Consideration:**
{self._format_context(context) if context else "Processing your query with available information"}

**Available Assistance:**
• General information and guidance
• Recommendations based on common patterns
• Contextual analysis of your request
• Suggestions for more detailed information sources

**System Status:**
Currently running in mock mode - responses are designed to be helpful and contextually appropriate while maintaining system functionality during configuration or maintenance periods.

For more detailed and specific responses, please ensure the full AI system components are properly configured. I'm designed to provide helpful, accurate, and contextually relevant information based on your specific needs.

Would you like me to focus on any particular aspect of your query or provide additional guidance in a specific area?"""
    
    def _extract_location(self, prompt: str, context: List[str] = None) -> str:
        """Extract location information from prompt or context"""
        # Simple location extraction - could be enhanced with NLP
        location_keywords = ["in", "at", "near", "around", "for"]
        words = prompt.split()
        
        for i, word in enumerate(words):
            if word.lower() in location_keywords and i + 1 < len(words):
                return words[i + 1].strip(".,!?")
        
        # Check context for location info
        if context:
            for ctx in context:
                if "location:" in ctx.lower():
                    return ctx.split(":")[-1].strip()
        
        return None
    
    def _format_context(self, context: List[str]) -> str:
        """Format context information for display"""
        if not context:
            return "No previous context available"
        
        formatted = []
        for i, ctx in enumerate(context[:3]):  # Limit to first 3 context items
            formatted.append(f"• {ctx[:100]}{'...' if len(ctx) > 100 else ''}")
        
        if len(context) > 3:
            formatted.append(f"• ... and {len(context) - 3} more context items")
        
        return "\n".join(formatted)
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Mock chat completion"""
        if messages:
            last_message = messages[-1].get("content", "")
            return self.generate_response(last_message)
        return "No messages provided for chat completion."

# Create singleton instance
enhanced_mock_client = EnhancedMockOllamaClient()
