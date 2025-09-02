"""
Trip Communications Coach Agent
Provides 2-3 phrasing tips for partner/guide/hotel communications
"""

from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent, GraphState

logger = logging.getLogger(__name__)


class TripCommsCoachAgent(BaseAgent):
    """Agent specialized in providing communication tips for travel interactions"""
    
    def __init__(self, memory_manager=None, name: str = "TripCommsCoach"):
        super().__init__(memory_manager, name)
        self._description = "Provides communication tips and phrasing suggestions for travel interactions"
        self._capabilities = [
            "communication_coaching",
            "phrasing_suggestions",
            "cultural_communication",
            "negotiation_tips",
            "language_assistance",
            "interaction_guidance"
        ]
    
    @property
    def keywords(self) -> List[str]:
        """Keywords that trigger this agent"""
        return [
            "communicate", "talk", "speak", "ask", "tell", "say", "phrase",
            "language", "conversation", "discuss", "negotiate", "request",
            "hotel", "guide", "partner", "local", "staff", "service"
        ]
    
    @property
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        return """You are TripCommsCoach, an expert communication coach for travelers.
        
        Your role is to provide practical communication tips including:
        - Effective phrasing for hotel requests and bookings
        - Communication strategies with tour guides and local services
        - Partner/companion communication during travel planning
        - Cultural communication considerations
        - Polite and effective ways to ask for help or information
        - Negotiation tips for travel services
        
        Always provide 2-3 specific, actionable phrasing examples that travelers can use immediately."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self._capabilities
    
    def process(self, state: GraphState) -> GraphState:
        """Process communication coaching queries"""
        if not self.validate_state(state):
            return self.handle_error(state, ValueError("Invalid state received"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            self.log_processing(query, user_id)
            
            # Analyze communication context
            comm_context = self._analyze_communication_context(query)
            
            # Search for similar communication scenarios
            search_results = self.search_similar_content(query, user_id, limit=3)
            
            # Get historical communication patterns
            historical_context = self.get_historical_context(user_id, days=30)
            
            # Build context for communication coaching
            context_parts = []
            if search_results.get("similar_content"):
                context_parts.append("Previous communication scenarios:")
                for item in search_results["similar_content"][:2]:
                    if isinstance(item, dict) and "content" in item:
                        context_parts.append(f"- {item['content'][:150]}...")
            
            if historical_context:
                context_parts.append("Communication history:")
                for item in historical_context[-2:]:
                    if isinstance(item, dict) and "value" in item:
                        context_parts.append(f"- {item['value'][:100]}...")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            # Generate communication coaching response
            response = self.generate_response_with_context(
                query=f"Provide communication coaching and phrasing tips for this travel scenario: {query}",
                context=context,
                temperature=0.7  # Higher temperature for creative phrasing
            )
            
            # Enhance response with specific phrasing tips
            enhanced_response = self._format_coaching_response(response, comm_context)
            
            # Store interaction with communication metadata
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type="communication_coaching",
                metadata={
                    "analysis_type": "travel_communication",
                    "communication_context": comm_context,
                    "scenario_type": comm_context.get("scenario_type"),
                    "audience": comm_context.get("audience")
                }
            )
            
            # Store vector embedding for communication pattern learning
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Communication Coaching: {query}\nContext: {comm_context}",
                metadata={
                    "agent": self.name,
                    "domain": "travel_communication",
                    "scenario": comm_context.get("scenario_type", "general")
                }
            )
            
            return self.format_state_response(
                state=state,
                response=enhanced_response,
                additional_data={
                    "communication_context": comm_context,
                    "orchestration": {
                        "strategy": "communication_coaching",
                        "selected_agents": [self.name],
                        "scenario_type": comm_context.get("scenario_type"),
                        "phrasing_tips_provided": True
                    }
                }
            )
            
        except Exception as e:
            return self.handle_error(state, e)
    
    def _analyze_communication_context(self, text: str) -> Dict[str, Any]:
        """Analyze the communication context and scenario"""
        context = {
            "scenario_type": "general",
            "audience": "unknown",
            "communication_goal": "information",
            "formality_level": "medium",
            "cultural_considerations": [],
            "specific_needs": []
        }
        
        text_lower = text.lower()
        
        # Identify scenario type
        if any(word in text_lower for word in ["hotel", "booking", "reservation", "room"]):
            context["scenario_type"] = "hotel_communication"
            context["audience"] = "hotel_staff"
            context["formality_level"] = "formal"
        elif any(word in text_lower for word in ["guide", "tour", "local guide"]):
            context["scenario_type"] = "guide_communication"
            context["audience"] = "tour_guide"
            context["formality_level"] = "friendly"
        elif any(word in text_lower for word in ["partner", "spouse", "family", "friend"]):
            context["scenario_type"] = "companion_communication"
            context["audience"] = "travel_companion"
            context["formality_level"] = "casual"
        elif any(word in text_lower for word in ["restaurant", "waiter", "server", "dining"]):
            context["scenario_type"] = "dining_communication"
            context["audience"] = "restaurant_staff"
            context["formality_level"] = "polite"
        elif any(word in text_lower for word in ["taxi", "driver", "transport", "uber"]):
            context["scenario_type"] = "transport_communication"
            context["audience"] = "driver"
            context["formality_level"] = "friendly"
        
        # Identify communication goals
        if any(word in text_lower for word in ["book", "reserve", "request"]):
            context["communication_goal"] = "booking"
        elif any(word in text_lower for word in ["complain", "problem", "issue", "wrong"]):
            context["communication_goal"] = "complaint"
        elif any(word in text_lower for word in ["negotiate", "discount", "price", "deal"]):
            context["communication_goal"] = "negotiation"
        elif any(word in text_lower for word in ["help", "assistance", "lost", "confused"]):
            context["communication_goal"] = "assistance"
        
        # Identify specific needs
        if any(word in text_lower for word in ["dietary", "allergy", "vegetarian", "vegan"]):
            context["specific_needs"].append("dietary_requirements")
        if any(word in text_lower for word in ["accessibility", "wheelchair", "mobility"]):
            context["specific_needs"].append("accessibility")
        if any(word in text_lower for word in ["emergency", "urgent", "immediate"]):
            context["specific_needs"].append("urgency")
        
        return context
    
    def _format_coaching_response(self, response: str, context: Dict[str, Any]) -> str:
        """Format the communication coaching response"""
        scenario_emoji = {
            "hotel_communication": "🏨",
            "guide_communication": "🗺️",
            "companion_communication": "👥",
            "dining_communication": "🍽️",
            "transport_communication": "🚗",
            "general": "💬"
        }
        
        scenario_type = context.get("scenario_type", "general")
        emoji = scenario_emoji.get(scenario_type, "💬")
        
        formatted_parts = [
            f"{emoji} **Travel Communication Coach**\n",
            f"**Scenario:** {scenario_type.replace('_', ' ').title()}",
            f"**Audience:** {context.get('audience', 'unknown').replace('_', ' ').title()}",
            f"**Formality Level:** {context.get('formality_level', 'medium').title()}\n",
            f"**Communication Guidance:** {response}\n"
        ]
        
        # Add specific phrasing examples based on scenario
        phrasing_examples = self._get_phrasing_examples(scenario_type, context)
        if phrasing_examples:
            formatted_parts.append("**💬 Suggested Phrases:**")
            for i, phrase in enumerate(phrasing_examples, 1):
                formatted_parts.append(f"{i}. \"{phrase}\"")
        
        # Add cultural tips if relevant
        if context.get("cultural_considerations"):
            formatted_parts.append(f"\n**🌍 Cultural Tips:** {', '.join(context['cultural_considerations'])}")
        
        formatted_parts.append("\n**Trip Communications Coach** | Helping you communicate effectively while traveling")
        
        return "\n".join(formatted_parts)
    
    def _get_phrasing_examples(self, scenario_type: str, context: Dict[str, Any]) -> List[str]:
        """Get specific phrasing examples for the scenario"""
        examples = []
        
        if scenario_type == "hotel_communication":
            examples = [
                "Hi, I'd like to inquire about room availability for [dates]. Do you have any options with [specific requirements]?",
                "Could you please help me with [specific request]? I'd really appreciate your assistance.",
                "I'm having a small issue with [problem]. Would it be possible to help me resolve this?"
            ]
        elif scenario_type == "guide_communication":
            examples = [
                "We're really interested in [specific attraction/activity]. Could you tell us more about it?",
                "What would you recommend for someone who enjoys [interests]? We'd love your local perspective.",
                "Is there anything special we should know about [location/activity] before we go?"
            ]
        elif scenario_type == "companion_communication":
            examples = [
                "I've been thinking about our trip, and I'd love to hear your thoughts on [topic].",
                "What matters most to you for this trip? I want to make sure we're both excited about our plans.",
                "I found some options for [activity/location]. Which one appeals to you more?"
            ]
        elif scenario_type == "dining_communication":
            examples = [
                "Could you recommend something popular from your menu? We're excited to try local specialties.",
                "I have a dietary restriction - do you have options that are [dietary requirement]?",
                "This looks wonderful! Could you tell us a bit about how it's prepared?"
            ]
        elif scenario_type == "transport_communication":
            examples = [
                "Hi! We'd like to go to [destination]. What's the best route, and approximately how long will it take?",
                "Could you recommend the most scenic way to get to [destination]?",
                "We're not in a hurry - feel free to take the route you think we'd enjoy most."
            ]
        
        return examples[:3]  # Return maximum 3 examples
    
    def can_handle(self, query: str) -> float:
        """Determine if this agent can handle the query"""
        base_confidence = super().can_handle(query)
        
        query_lower = query.lower()
        
        # High confidence for communication-specific queries
        comm_terms = ["how to say", "how to ask", "how to tell", "phrasing", "communicate"]
        if any(term in query_lower for term in comm_terms):
            base_confidence = min(base_confidence + 0.4, 1.0)
        
        # Medium confidence for travel scenarios with people
        people_terms = ["hotel staff", "tour guide", "partner", "waiter", "driver"]
        if any(term in query_lower for term in people_terms):
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        return base_confidence