"""
Text Trip Analyzer Agent
Extracts goals, constraints, destinations from text input
"""

from typing import Dict, Any, List
import logging
import re
from core.base_agent import BaseAgent, GraphState

logger = logging.getLogger(__name__)


class TextTripAnalyzerAgent(BaseAgent):
    """Agent specialized in analyzing trip planning text to extract goals, constraints, and destinations"""
    
    def __init__(self, memory_manager=None, name: str = "TextTripAnalyzer"):
        super().__init__(memory_manager, name)
        self._description = "Analyzes trip planning text to extract goals, constraints, destinations, and preferences"
        self._capabilities = [
            "text_analysis",
            "goal_extraction", 
            "constraint_identification",
            "destination_parsing",
            "preference_detection",
            "budget_analysis"
        ]
    
    @property
    def keywords(self) -> List[str]:
        """Keywords that trigger this agent"""
        return [
            "plan", "trip", "travel", "vacation", "holiday", "destination", "budget",
            "goal", "want", "need", "prefer", "constraint", "limit", "requirement",
            "analyze", "extract", "planning", "itinerary", "schedule"
        ]
    
    @property
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        return """You are TextTripAnalyzer, an expert at analyzing travel planning conversations and extracting key information.
        
        Your role is to carefully analyze text input and extract:
        - Travel goals and objectives
        - Budget constraints and limitations
        - Preferred destinations and locations
        - Travel dates and timing preferences
        - Group size and traveler types
        - Activity preferences and interests
        - Accommodation preferences
        - Transportation preferences
        - Special requirements or constraints
        
        Provide structured, actionable analysis that other travel agents can use."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self._capabilities
    
    def process(self, state: GraphState) -> GraphState:
        """Process trip analysis queries"""
        if not self.validate_state(state):
            return self.handle_error(state, ValueError("Invalid state received"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            self.log_processing(query, user_id)
            
            # Extract trip information from text
            trip_analysis = self._analyze_trip_text(query)
            
            # Search for similar trip planning queries
            search_results = self.search_similar_content(query, user_id, limit=3)
            
            # Get user's travel history for context
            historical_context = self.get_historical_context(user_id, days=30)
            
            # Build context for analysis
            context_parts = []
            if search_results.get("similar_content"):
                context_parts.append("Previous trip planning:")
                for item in search_results["similar_content"][:2]:
                    if isinstance(item, dict) and "content" in item:
                        context_parts.append(f"- {item['content'][:150]}...")
            
            if historical_context:
                context_parts.append("Travel history:")
                for item in historical_context[-3:]:
                    if isinstance(item, dict) and "value" in item:
                        context_parts.append(f"- {item['value'][:100]}...")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            # Generate comprehensive trip analysis
            response = self.generate_response_with_context(
                query=f"Analyze this trip planning text and extract goals, constraints, and destinations: {query}",
                context=context,
                temperature=0.3  # Lower temperature for structured analysis
            )
            
            # Enhance response with extracted data
            enhanced_response = self._format_analysis_response(response, trip_analysis)
            
            # Store interaction with trip analysis metadata
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type="trip_analysis",
                metadata={
                    "analysis_type": "text_trip_analysis",
                    "extracted_data": trip_analysis,
                    "destinations_found": len(trip_analysis.get("destinations", [])),
                    "constraints_found": len(trip_analysis.get("constraints", []))
                }
            )
            
            # Store vector embedding for future trip analysis
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Trip Analysis: {query}\nExtracted: {trip_analysis}",
                metadata={
                    "agent": self.name,
                    "domain": "trip_planning",
                    "analysis_type": "text_extraction"
                }
            )
            
            return self.format_state_response(
                state=state,
                response=enhanced_response,
                additional_data={
                    "trip_analysis": trip_analysis,
                    "orchestration": {
                        "strategy": "text_trip_analysis",
                        "selected_agents": [self.name],
                        "extracted_data": trip_analysis
                    }
                }
            )
            
        except Exception as e:
            return self.handle_error(state, e)
    
    def _analyze_trip_text(self, text: str) -> Dict[str, Any]:
        """Extract structured trip information from text"""
        analysis = {
            "destinations": [],
            "goals": [],
            "constraints": [],
            "preferences": {},
            "budget_info": {},
            "timing": {},
            "group_info": {}
        }
        
        text_lower = text.lower()
        
        # Extract destinations using common patterns
        destination_patterns = [
            r"(?:go to|visit|traveling to|trip to|vacation in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:trip|vacation|travel)",
            r"in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        
        for pattern in destination_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 2 and match not in analysis["destinations"]:
                    analysis["destinations"].append(match)
        
        # Extract budget information
        budget_patterns = [
            r"\$(\d+(?:,\d+)*)",
            r"(\d+)\s*(?:dollars?|USD|euros?|EUR)",
            r"budget.*?(\d+)",
            r"spend.*?(\d+)"
        ]
        
        for pattern in budget_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                analysis["budget_info"]["mentioned_amounts"] = matches
        
        # Extract timing information
        if any(word in text_lower for word in ["week", "weeks"]):
            analysis["timing"]["duration_type"] = "weeks"
        elif any(word in text_lower for word in ["day", "days"]):
            analysis["timing"]["duration_type"] = "days"
        elif any(word in text_lower for word in ["month", "months"]):
            analysis["timing"]["duration_type"] = "months"
        
        # Extract group information
        if any(word in text_lower for word in ["family", "kids", "children"]):
            analysis["group_info"]["type"] = "family"
        elif any(word in text_lower for word in ["couple", "partner", "spouse"]):
            analysis["group_info"]["type"] = "couple"
        elif any(word in text_lower for word in ["solo", "alone", "myself"]):
            analysis["group_info"]["type"] = "solo"
        elif any(word in text_lower for word in ["friends", "group"]):
            analysis["group_info"]["type"] = "friends"
        
        # Extract goals and preferences
        goal_keywords = {
            "relaxation": ["relax", "peaceful", "calm", "rest", "unwind"],
            "adventure": ["adventure", "exciting", "thrill", "active", "hiking"],
            "culture": ["culture", "history", "museum", "art", "heritage"],
            "food": ["food", "cuisine", "restaurant", "dining", "culinary"],
            "nature": ["nature", "outdoor", "wildlife", "park", "scenic"],
            "photography": ["photo", "photography", "instagram", "pictures"]
        }
        
        for goal, keywords in goal_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                analysis["goals"].append(goal)
        
        # Extract constraints
        constraint_keywords = {
            "budget": ["cheap", "budget", "affordable", "expensive", "cost"],
            "time": ["limited time", "short", "quick", "rushed", "tight schedule"],
            "accessibility": ["accessible", "disability", "mobility", "wheelchair"],
            "dietary": ["vegetarian", "vegan", "gluten", "allergy", "dietary"]
        }
        
        for constraint, keywords in constraint_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                analysis["constraints"].append(constraint)
        
        return analysis
    
    def _format_analysis_response(self, response: str, analysis: Dict[str, Any]) -> str:
        """Format the analysis response with extracted data"""
        formatted_parts = [
            "🔍 **Trip Analysis Results**\n",
            f"**AI Analysis:** {response}\n"
        ]
        
        if analysis.get("destinations"):
            formatted_parts.append(f"**📍 Destinations Identified:** {', '.join(analysis['destinations'])}")
        
        if analysis.get("goals"):
            formatted_parts.append(f"**🎯 Travel Goals:** {', '.join(analysis['goals'])}")
        
        if analysis.get("constraints"):
            formatted_parts.append(f"**⚠️ Constraints:** {', '.join(analysis['constraints'])}")
        
        if analysis.get("group_info", {}).get("type"):
            formatted_parts.append(f"**👥 Group Type:** {analysis['group_info']['type']}")
        
        if analysis.get("timing", {}).get("duration_type"):
            formatted_parts.append(f"**⏰ Duration Type:** {analysis['timing']['duration_type']}")
        
        formatted_parts.append("\n**Text Trip Analyzer** | Extracting travel insights from your planning text")
        
        return "\n".join(formatted_parts)