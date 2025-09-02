"""
Trip Calm Practice Agent
Provides calming techniques and relaxation guidance for travel stress
"""

from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent, GraphState

logger = logging.getLogger(__name__)


class TripCalmPracticeAgent(BaseAgent):
    """Agent specialized in providing calming techniques and stress relief for travel planning"""
    
    def __init__(self, memory_manager=None, name: str = "TripCalmPractice"):
        super().__init__(memory_manager, name)
        self._description = "Provides calming techniques, stress relief, and relaxation guidance for travel planning"
        self._capabilities = [
            "stress_relief",
            "calming_techniques",
            "breathing_exercises",
            "mindfulness_practices",
            "anxiety_management",
            "relaxation_guidance"
        ]
    
    @property
    def keywords(self) -> List[str]:
        """Keywords that trigger this agent"""
        return [
            "calm", "relax", "stress", "anxiety", "nervous", "worried", "overwhelmed",
            "breathe", "meditation", "mindful", "peace", "tranquil", "soothe",
            "tension", "pressure", "panic", "fear", "comfort"
        ]
    
    @property
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        return """You are TripCalmPractice, a mindfulness and stress relief expert for travelers.
        
        Your role is to provide:
        - Quick calming techniques (90-second breathing exercises)
        - Stress management strategies for travel planning
        - Mindfulness practices for decision-making
        - Anxiety relief techniques for travel concerns
        - Relaxation methods for overwhelming situations
        - Grounding exercises for travel stress
        
        Always provide practical, immediate techniques that can be used anywhere, anytime."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self._capabilities
    
    def process(self, state: GraphState) -> GraphState:
        """Process calming practice queries"""
        if not self.validate_state(state):
            return self.handle_error(state, ValueError("Invalid state received"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            self.log_processing(query, user_id)
            
            # Analyze stress/calm needs
            calm_analysis = self._analyze_calm_needs(query)
            
            # Search for previous calming techniques used
            search_results = self.search_similar_content(query, user_id, limit=3)
            
            # Get user's stress patterns from history
            historical_context = self.get_historical_context(user_id, days=14)
            
            # Build context for calming guidance
            context_parts = []
            if search_results.get("similar_content"):
                context_parts.append("Previous calming techniques:")
                for item in search_results["similar_content"][:2]:
                    if isinstance(item, dict) and "content" in item:
                        context_parts.append(f"- {item['content'][:150]}...")
            
            if historical_context:
                context_parts.append("Stress management history:")
                for item in historical_context[-2:]:
                    if isinstance(item, dict) and "value" in item:
                        context_parts.append(f"- {item['value'][:100]}...")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            # Generate calming guidance
            response = self.generate_response_with_context(
                query=f"Provide calming techniques and stress relief for this travel situation: {query}",
                context=context,
                temperature=0.6  # Balanced for empathy and practical advice
            )
            
            # Enhance response with specific calming techniques
            enhanced_response = self._format_calm_response(response, calm_analysis)
            
            # Store interaction with calming metadata
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type="calming_guidance",
                metadata={
                    "analysis_type": "travel_stress_relief",
                    "calm_analysis": calm_analysis,
                    "stress_type": calm_analysis.get("stress_type"),
                    "technique_type": calm_analysis.get("recommended_technique")
                }
            )
            
            # Store vector embedding for stress pattern recognition
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Calming Practice: {query}\nTechniques: {calm_analysis}",
                metadata={
                    "agent": self.name,
                    "domain": "travel_wellness",
                    "stress_type": calm_analysis.get("stress_type", "general")
                }
            )
            
            return self.format_state_response(
                state=state,
                response=enhanced_response,
                additional_data={
                    "calm_analysis": calm_analysis,
                    "orchestration": {
                        "strategy": "calming_practice",
                        "selected_agents": [self.name],
                        "stress_type": calm_analysis.get("stress_type"),
                        "technique_provided": True
                    }
                }
            )
            
        except Exception as e:
            return self.handle_error(state, e)
    
    def _analyze_calm_needs(self, text: str) -> Dict[str, Any]:
        """Analyze text for stress and calming needs"""
        analysis = {
            "stress_type": "general",
            "stress_level": "medium",
            "recommended_technique": "breathing",
            "urgency": "medium",
            "stress_indicators": [],
            "calm_preferences": []
        }
        
        text_lower = text.lower()
        
        # Identify stress type
        if any(word in text_lower for word in ["decision", "choose", "pick", "decide"]):
            analysis["stress_type"] = "decision_anxiety"
            analysis["recommended_technique"] = "grounding"
        elif any(word in text_lower for word in ["money", "budget", "cost", "expensive"]):
            analysis["stress_type"] = "financial_anxiety"
            analysis["recommended_technique"] = "perspective"
        elif any(word in text_lower for word in ["time", "deadline", "rush", "hurry"]):
            analysis["stress_type"] = "time_pressure"
            analysis["recommended_technique"] = "breathing"
        elif any(word in text_lower for word in ["unknown", "unfamiliar", "foreign", "new"]):
            analysis["stress_type"] = "uncertainty_anxiety"
            analysis["recommended_technique"] = "preparation"
        
        # Assess stress level
        high_stress_words = ["panic", "overwhelmed", "can't handle", "too much", "breaking down"]
        medium_stress_words = ["stressed", "worried", "anxious", "nervous", "concerned"]
        
        if any(word in text_lower for word in high_stress_words):
            analysis["stress_level"] = "high"
            analysis["urgency"] = "high"
        elif any(word in text_lower for word in medium_stress_words):
            analysis["stress_level"] = "medium"
        
        # Identify stress indicators
        stress_indicators = []
        if "?" in text and text.count("?") >= 3:
            stress_indicators.append("multiple_questions")
        if any(word in text_lower for word in ["help", "don't know", "confused"]):
            stress_indicators.append("seeking_help")
        if len(text.split()) > 100:
            stress_indicators.append("verbose_expression")
        
        analysis["stress_indicators"] = stress_indicators
        
        return analysis
    
    def _format_calm_response(self, response: str, analysis: Dict[str, Any]) -> str:
        """Format the calming practice response"""
        stress_emoji = {
            "decision_anxiety": "🤔",
            "financial_anxiety": "💰",
            "time_pressure": "⏰",
            "uncertainty_anxiety": "🌊",
            "general": "🧘"
        }
        
        stress_type = analysis.get("stress_type", "general")
        emoji = stress_emoji.get(stress_type, "🧘")
        
        formatted_parts = [
            f"{emoji} **Trip Calm Practice**\n",
            f"**Stress Type:** {stress_type.replace('_', ' ').title()}",
            f"**Stress Level:** {analysis.get('stress_level', 'medium').title()}",
            f"**Recommended Technique:** {analysis.get('recommended_technique', 'breathing').title()}\n",
            f"**Calming Guidance:** {response}\n"
        ]
        
        # Add quick calming technique
        quick_technique = self._get_quick_technique(analysis.get("recommended_technique", "breathing"))
        formatted_parts.append("**🧘 90-Second Quick Calm Technique:**")
        formatted_parts.append(quick_technique)
        
        # Add stress management tips
        stress_tips = self._get_stress_tips(stress_type)
        if stress_tips:
            formatted_parts.append(f"\n**💡 Stress Management Tips:**")
            for tip in stress_tips:
                formatted_parts.append(f"• {tip}")
        
        formatted_parts.append("\n**Trip Calm Practice** | Finding peace in travel planning")
        
        return "\n".join(formatted_parts)
    
    def _get_quick_technique(self, technique_type: str) -> str:
        """Get a specific 90-second calming technique"""
        techniques = {
            "breathing": """
**4-7-8 Breathing (90 seconds):**
1. Inhale through nose for 4 counts
2. Hold breath for 7 counts  
3. Exhale through mouth for 8 counts
4. Repeat 4-5 times
*This activates your parasympathetic nervous system*""",
            
            "grounding": """
**5-4-3-2-1 Grounding (90 seconds):**
1. Name 5 things you can see
2. Name 4 things you can touch
3. Name 3 things you can hear
4. Name 2 things you can smell
5. Name 1 thing you can taste
*This brings you back to the present moment*""",
            
            "perspective": """
**Perspective Reset (90 seconds):**
1. Take 3 deep breaths
2. Ask: "Will this matter in 5 years?"
3. Remind yourself: "I can handle this step by step"
4. Focus on one small action you can take now
*This reduces overwhelm and builds confidence*""",
            
            "preparation": """
**Confidence Building (90 seconds):**
1. Write down 3 things you know for certain about your trip
2. List 2 resources you can use for help
3. Remind yourself of a past challenge you overcame
4. Take 5 slow, deep breaths
*This builds confidence through preparation*"""
        }
        
        return techniques.get(technique_type, techniques["breathing"])
    
    def _get_stress_tips(self, stress_type: str) -> List[str]:
        """Get stress management tips for specific stress types"""
        tips_map = {
            "decision_anxiety": [
                "Remember that most travel decisions can be changed or adjusted",
                "Focus on making 'good enough' decisions rather than perfect ones",
                "Set a decision deadline to avoid endless research"
            ],
            "financial_anxiety": [
                "Create a realistic budget with a 20% buffer for peace of mind",
                "Look for free activities and experiences at your destination",
                "Remember that experiences matter more than expensive accommodations"
            ],
            "time_pressure": [
                "Prioritize the most important bookings first (flights, accommodation)",
                "Accept that some planning can happen during the trip",
                "Use travel apps for last-minute bookings if needed"
            ],
            "uncertainty_anxiety": [
                "Research basic information about your destination for confidence",
                "Connect with other travelers online for tips and reassurance",
                "Remember that locals are usually helpful to tourists"
            ]
        }
        
        return tips_map.get(stress_type, [
            "Take breaks from planning to avoid burnout",
            "Focus on the excitement of the upcoming adventure",
            "Trust that you can handle unexpected situations"
        ])
    
    def can_handle(self, query: str) -> float:
        """Determine if this agent can handle the query"""
        base_confidence = super().can_handle(query)
        
        query_lower = query.lower()
        
        # High confidence for stress/calm queries
        stress_terms = ["stressed", "overwhelmed", "anxious", "calm", "relax"]
        if any(term in query_lower for term in stress_terms):
            base_confidence = min(base_confidence + 0.4, 1.0)
        
        # Medium confidence for emotional travel planning
        emotion_terms = ["feeling", "nervous", "excited", "worried", "peaceful"]
        if any(term in query_lower for term in emotion_terms):
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        return base_confidence