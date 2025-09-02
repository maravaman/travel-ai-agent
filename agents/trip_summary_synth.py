"""
Trip Summary Synthesizer Agent
Combines all agent outputs and updates User Travel Profile (UTP)
"""

from typing import Dict, Any, List
import logging
import json
from datetime import datetime
from core.base_agent import BaseAgent, GraphState

logger = logging.getLogger(__name__)


class TripSummarySynthAgent(BaseAgent):
    """Agent specialized in synthesizing multi-agent outputs and updating User Travel Profile"""
    
    def __init__(self, memory_manager=None, name: str = "TripSummarySynth"):
        super().__init__(memory_manager, name)
        self._description = "Synthesizes multi-agent travel outputs and maintains User Travel Profile"
        self._capabilities = [
            "response_synthesis",
            "profile_updating",
            "preference_learning",
            "pattern_recognition",
            "summary_generation",
            "utp_management"
        ]
    
    @property
    def keywords(self) -> List[str]:
        """Keywords that trigger this agent"""
        return [
            "summary", "synthesize", "combine", "overall", "conclusion",
            "profile", "preferences", "update", "learn", "pattern",
            "final", "complete", "comprehensive", "integrate"
        ]
    
    @property
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        return """You are TripSummarySynth, an expert at synthesizing travel information and maintaining user profiles.
        
        Your role is to:
        - Combine outputs from multiple travel agents into coherent summaries
        - Extract and update user travel preferences and patterns
        - Create comprehensive travel recommendations
        - Maintain and update User Travel Profiles (UTP)
        - Identify learning opportunities from travel planning sessions
        - Generate actionable next steps and checklists
        
        Always provide structured, actionable summaries that help users move forward with their travel plans."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self._capabilities
    
    def process(self, state: GraphState) -> GraphState:
        """Process synthesis and profile update queries"""
        if not self.validate_state(state):
            return self.handle_error(state, ValueError("Invalid state received"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            self.log_processing(query, user_id)
            
            # Get current User Travel Profile
            current_utp = self._get_user_travel_profile(user_id)
            
            # Analyze the query for synthesis needs
            synthesis_context = self._analyze_synthesis_needs(query, state)
            
            # Search for related travel planning sessions
            search_results = self.search_similar_content(query, user_id, limit=5)
            
            # Get recent travel planning history
            historical_context = self.get_historical_context(user_id, days=7)
            
            # Build comprehensive context
            context_parts = []
            context_parts.append(f"Current User Travel Profile: {json.dumps(current_utp, indent=2)}")
            
            if search_results.get("similar_content"):
                context_parts.append("Related travel planning:")
                for item in search_results["similar_content"][:3]:
                    if isinstance(item, dict) and "content" in item:
                        context_parts.append(f"- {item['content'][:150]}...")
            
            if historical_context:
                context_parts.append("Recent planning sessions:")
                for item in historical_context[-3:]:
                    if isinstance(item, dict) and "value" in item:
                        context_parts.append(f"- {item['value'][:100]}...")
            
            context = "\n".join(context_parts)
            
            # Generate comprehensive synthesis
            response = self.generate_response_with_context(
                query=f"Synthesize travel planning information and provide comprehensive summary: {query}",
                context=context,
                temperature=0.4  # Lower temperature for structured synthesis
            )
            
            # Update User Travel Profile based on new information
            updated_utp = self._update_user_travel_profile(current_utp, query, synthesis_context)
            
            # Format final synthesis response
            enhanced_response = self._format_synthesis_response(response, synthesis_context, updated_utp)
            
            # Store the updated UTP
            self._store_user_travel_profile(user_id, updated_utp)
            
            # Store interaction with synthesis metadata
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type="trip_synthesis",
                metadata={
                    "analysis_type": "travel_synthesis",
                    "synthesis_context": synthesis_context,
                    "utp_updated": True,
                    "profile_changes": self._get_profile_changes(current_utp, updated_utp)
                }
            )
            
            # Store vector embedding for synthesis pattern learning
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Trip Synthesis: {query}\nProfile Updates: {updated_utp}",
                metadata={
                    "agent": self.name,
                    "domain": "travel_synthesis",
                    "session_type": synthesis_context.get("session_type", "chat")
                }
            )
            
            return self.format_state_response(
                state=state,
                response=enhanced_response,
                additional_data={
                    "synthesis_context": synthesis_context,
                    "updated_utp": updated_utp,
                    "orchestration": {
                        "strategy": "trip_synthesis",
                        "selected_agents": [self.name],
                        "utp_updated": True,
                        "synthesis_complete": True
                    }
                }
            )
            
        except Exception as e:
            return self.handle_error(state, e)
    
    def _get_user_travel_profile(self, user_id: int) -> Dict[str, Any]:
        """Get current User Travel Profile from memory"""
        try:
            # Try to get from STM cache first
            cached_utp = self.memory.get_stm(str(user_id), "user_travel_profile")
            if cached_utp:
                return json.loads(cached_utp)
            
            # Get from LTM if not cached
            ltm_data = self.memory.get_ltm_by_agent(str(user_id), "TripSummarySynth")
            for entry in ltm_data:
                if "user_travel_profile" in entry.get("value", ""):
                    try:
                        profile_data = json.loads(entry["value"].split("Profile: ")[1])
                        return profile_data
                    except (json.JSONDecodeError, IndexError):
                        continue
            
            # Return default profile if none found
            return self._get_default_travel_profile()
            
        except Exception as e:
            logger.warning(f"Error getting UTP: {e}")
            return self._get_default_travel_profile()
    
    def _get_default_travel_profile(self) -> Dict[str, Any]:
        """Get default User Travel Profile structure"""
        return {
            "destinations_of_interest": [],
            "cuisine_preferences": [],
            "climate_tolerance": {
                "preferred_temperature": "moderate",
                "weather_preferences": []
            },
            "travel_pace": "balanced",
            "behavioral_notes": {
                "decision_style": "analytical",
                "planning_patterns": [],
                "stress_triggers": [],
                "preferred_support": []
            },
            "budget_patterns": {
                "typical_range": "medium",
                "spending_priorities": []
            },
            "group_preferences": {
                "typical_group_size": "small",
                "travel_companions": []
            },
            "activity_preferences": [],
            "accommodation_preferences": [],
            "last_updated": datetime.now().isoformat(),
            "profile_version": "1.0"
        }
    
    def _update_user_travel_profile(self, current_utp: Dict[str, Any], query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update User Travel Profile based on new information"""
        updated_utp = current_utp.copy()
        query_lower = query.lower()
        
        # Update destinations of interest
        if context.get("destinations"):
            for dest in context["destinations"]:
                if dest not in updated_utp["destinations_of_interest"]:
                    updated_utp["destinations_of_interest"].append(dest)
        
        # Update cuisine preferences
        cuisine_keywords = {
            "italian": ["italian", "pasta", "pizza"],
            "asian": ["asian", "chinese", "japanese", "thai"],
            "mediterranean": ["mediterranean", "greek"],
            "local": ["local", "authentic", "traditional"]
        }
        
        for cuisine, keywords in cuisine_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if cuisine not in updated_utp["cuisine_preferences"]:
                    updated_utp["cuisine_preferences"].append(cuisine)
        
        # Update travel pace
        if any(word in query_lower for word in ["relaxed", "slow", "leisurely"]):
            updated_utp["travel_pace"] = "relaxed"
        elif any(word in query_lower for word in ["packed", "busy", "lots", "many"]):
            updated_utp["travel_pace"] = "packed"
        
        # Update activity preferences
        activity_keywords = {
            "outdoor": ["hiking", "nature", "outdoor", "adventure"],
            "cultural": ["museum", "history", "culture", "art"],
            "food": ["food", "dining", "restaurant", "culinary"],
            "photography": ["photo", "photography", "scenic", "views"],
            "relaxation": ["spa", "beach", "relax", "peaceful"]
        }
        
        for activity, keywords in activity_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if activity not in updated_utp["activity_preferences"]:
                    updated_utp["activity_preferences"].append(activity)
        
        # Update behavioral notes
        if any(word in query_lower for word in ["stressed", "overwhelmed", "anxious"]):
            if "stress_during_planning" not in updated_utp["behavioral_notes"]["stress_triggers"]:
                updated_utp["behavioral_notes"]["stress_triggers"].append("complex_decisions")
        
        if any(word in query_lower for word in ["research", "compare", "analyze"]):
            updated_utp["behavioral_notes"]["decision_style"] = "analytical"
        elif any(word in query_lower for word in ["quick", "fast", "decide"]):
            updated_utp["behavioral_notes"]["decision_style"] = "intuitive"
        
        # Update timestamp
        updated_utp["last_updated"] = datetime.now().isoformat()
        
        return updated_utp
    
    def _store_user_travel_profile(self, user_id: int, utp: Dict[str, Any]):
        """Store updated User Travel Profile in both STM and LTM"""
        try:
            utp_json = json.dumps(utp)
            
            # Cache in STM (Redis) for quick access
            self.memory.set_stm(str(user_id), "user_travel_profile", utp_json, expiry=7*24*3600)  # 7 days
            
            # Store in LTM (MySQL) for persistence
            self.memory.set_ltm(str(user_id), "TripSummarySynth", f"Profile: {utp_json}")
            
            logger.info(f"Updated UTP for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error storing UTP: {e}")
    
    def _analyze_synthesis_needs(self, query: str, state: GraphState) -> Dict[str, Any]:
        """Analyze what kind of synthesis is needed"""
        context = {
            "session_type": "chat",
            "synthesis_scope": "single_query",
            "destinations": [],
            "agent_outputs": {},
            "key_decisions": [],
            "next_steps": []
        }
        
        # Check if this is a batch/recording mode
        if len(query) > 1000 or "transcript" in query.lower():
            context["session_type"] = "recording"
            context["synthesis_scope"] = "full_session"
        
        # Extract any agent outputs from state
        if hasattr(state, 'agent_responses'):
            context["agent_outputs"] = state.agent_responses
        
        return context
    
    def _format_synthesis_response(self, response: str, context: Dict[str, Any], utp: Dict[str, Any]) -> str:
        """Format the comprehensive synthesis response"""
        formatted_parts = [
            "🎯 **Travel Planning Synthesis**\n",
            f"**Comprehensive Analysis:** {response}\n"
        ]
        
        # Add structured summary sections
        if context.get("session_type") == "recording":
            formatted_parts.append("**📋 Session Summary:**")
            formatted_parts.append("- Full conversation analyzed")
            formatted_parts.append("- Travel preferences extracted and updated")
            formatted_parts.append("- Comprehensive recommendations generated")
        
        # Add key insights from UTP
        formatted_parts.append("**👤 Your Travel Profile Insights:**")
        if utp.get("destinations_of_interest"):
            formatted_parts.append(f"- Favorite destinations: {', '.join(utp['destinations_of_interest'][-3:])}")
        if utp.get("activity_preferences"):
            formatted_parts.append(f"- Preferred activities: {', '.join(utp['activity_preferences'])}")
        if utp.get("travel_pace"):
            formatted_parts.append(f"- Travel pace: {utp['travel_pace']}")
        
        # Add next steps checklist
        next_steps = self._generate_next_steps(context, utp)
        if next_steps:
            formatted_parts.append("\n**✅ Recommended Next Steps:**")
            for i, step in enumerate(next_steps, 1):
                formatted_parts.append(f"{i}. {step}")
        
        formatted_parts.append(f"\n**Profile Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        formatted_parts.append("\n**Trip Summary Synthesizer** | Bringing it all together for your perfect trip")
        
        return "\n".join(formatted_parts)
    
    def _generate_next_steps(self, context: Dict[str, Any], utp: Dict[str, Any]) -> List[str]:
        """Generate actionable next steps based on synthesis"""
        steps = []
        
        if context.get("session_type") == "recording":
            # Batch mode next steps
            steps = [
                "Review the comprehensive analysis and identify your top priorities",
                "Start with the most time-sensitive bookings (flights, accommodation)",
                "Create a detailed itinerary based on the recommendations",
                "Set up alerts for any price changes on preferred options",
                "Share the plan with travel companions for feedback"
            ]
        else:
            # Chat mode next steps
            if utp.get("destinations_of_interest"):
                steps.append(f"Research detailed information about {utp['destinations_of_interest'][-1]}")
            
            steps.extend([
                "Set a budget range based on your preferences",
                "Compare 2-3 accommodation options in your preferred area",
                "Create a rough itinerary with must-see attractions",
                "Check visa requirements and travel documents"
            ])
        
        return steps[:5]  # Maximum 5 steps
    
    def _get_profile_changes(self, old_utp: Dict[str, Any], new_utp: Dict[str, Any]) -> Dict[str, Any]:
        """Identify what changed in the profile"""
        changes = {
            "destinations_added": [],
            "preferences_updated": [],
            "behavioral_insights": []
        }
        
        # Check destinations
        old_destinations = set(old_utp.get("destinations_of_interest", []))
        new_destinations = set(new_utp.get("destinations_of_interest", []))
        changes["destinations_added"] = list(new_destinations - old_destinations)
        
        # Check activity preferences
        old_activities = set(old_utp.get("activity_preferences", []))
        new_activities = set(new_utp.get("activity_preferences", []))
        if new_activities != old_activities:
            changes["preferences_updated"].append("activities")
        
        # Check travel pace
        if old_utp.get("travel_pace") != new_utp.get("travel_pace"):
            changes["preferences_updated"].append("travel_pace")
        
        return changes
    
    def synthesize_multi_agent_response(self, agent_responses: Dict[str, str], user_id: int) -> str:
        """Synthesize responses from multiple travel agents"""
        synthesis_parts = ["🎯 **Comprehensive Travel Guidance**\n"]
        
        # Define agent emoji mapping
        agent_emojis = {
            "WeatherAgent": "🌤️",
            "DiningAgent": "🍽️", 
            "ScenicLocationFinderAgent": "🏞️",
            "ForestAnalyzerAgent": "🌲",
            "TextTripAnalyzer": "🔍",
            "TripMoodDetector": "😊",
            "TripCommsCoach": "💬",
            "TripBehaviorGuide": "🧭",
            "TripCalmPractice": "🧘"
        }
        
        # Add each agent's contribution
        for agent_name, response in agent_responses.items():
            emoji = agent_emojis.get(agent_name, "🤖")
            clean_name = agent_name.replace("Agent", "").replace("Trip", "").replace("Finder", "")
            synthesis_parts.append(f"## {emoji} {clean_name}")
            synthesis_parts.append(response[:300] + "..." if len(response) > 300 else response)
            synthesis_parts.append("")
        
        # Add integrated summary
        synthesis_parts.append("## 🔗 **Integrated Summary**")
        synthesis_parts.append("🌟 **Perfect Planning Combination**: All specialist insights combined for your ideal travel experience.")
        
        return "\n".join(synthesis_parts)
    
    def can_handle(self, query: str) -> float:
        """Determine if this agent can handle the query"""
        base_confidence = super().can_handle(query)
        
        query_lower = query.lower()
        
        # High confidence for synthesis queries
        synthesis_terms = ["summary", "overall", "combine", "synthesize", "comprehensive"]
        if any(term in query_lower for term in synthesis_terms):
            base_confidence = min(base_confidence + 0.4, 1.0)
        
        # Medium confidence for profile-related queries
        profile_terms = ["profile", "preferences", "pattern", "learn", "update"]
        if any(term in query_lower for term in profile_terms):
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        return base_confidence