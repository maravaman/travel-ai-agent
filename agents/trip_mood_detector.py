"""
Trip Mood Detector Agent
Detects excitement, stress, indecision from travel planning text
"""

from typing import Dict, Any, List
import logging
import re
from core.base_agent import BaseAgent, GraphState

logger = logging.getLogger(__name__)


class TripMoodDetectorAgent(BaseAgent):
    """Agent specialized in detecting emotional states and mood from trip planning conversations"""
    
    def __init__(self, memory_manager=None, name: str = "TripMoodDetector"):
        super().__init__(memory_manager, name)
        self._description = "Detects excitement, stress, indecision, and other emotional states from travel planning text"
        self._capabilities = [
            "mood_detection",
            "emotion_analysis",
            "stress_identification",
            "excitement_measurement",
            "indecision_detection",
            "sentiment_analysis"
        ]
    
    @property
    def keywords(self) -> List[str]:
        """Keywords that trigger this agent"""
        return [
            "excited", "nervous", "stressed", "worried", "confused", "unsure",
            "overwhelmed", "anxious", "happy", "thrilled", "concerned", "frustrated",
            "mood", "feeling", "emotion", "sentiment", "vibe", "energy"
        ]
    
    @property
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        return """You are TripMoodDetector, an expert at analyzing emotional states and mood from travel planning conversations.
        
        Your role is to detect and analyze:
        - Excitement levels and enthusiasm
        - Stress indicators and anxiety
        - Indecision and uncertainty patterns
        - Overwhelm and confusion signals
        - Confidence and decisiveness
        - Overall emotional tone
        
        Provide empathetic insights that help understand the traveler's emotional state and suggest appropriate support."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self._capabilities
    
    def process(self, state: GraphState) -> GraphState:
        """Process mood detection queries"""
        if not self.validate_state(state):
            return self.handle_error(state, ValueError("Invalid state received"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            self.log_processing(query, user_id)
            
            # Analyze mood and emotional indicators
            mood_analysis = self._analyze_mood_indicators(query)
            
            # Search for similar emotional patterns in history
            search_results = self.search_similar_content(query, user_id, limit=3)
            
            # Get historical mood patterns
            historical_context = self.get_historical_context(user_id, days=14)
            
            # Build context for mood analysis
            context_parts = []
            if search_results.get("similar_content"):
                context_parts.append("Previous emotional patterns:")
                for item in search_results["similar_content"][:2]:
                    if isinstance(item, dict) and "content" in item:
                        context_parts.append(f"- {item['content'][:150]}...")
            
            if historical_context:
                context_parts.append("Recent travel mood history:")
                for item in historical_context[-2:]:
                    if isinstance(item, dict) and "value" in item:
                        context_parts.append(f"- {item['value'][:100]}...")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            # Generate empathetic mood analysis
            response = self.generate_response_with_context(
                query=f"Analyze the emotional state and mood in this travel planning text: {query}",
                context=context,
                temperature=0.6  # Balanced for empathy and accuracy
            )
            
            # Enhance response with mood insights
            enhanced_response = self._format_mood_response(response, mood_analysis)
            
            # Store interaction with mood metadata
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type="mood_analysis",
                metadata={
                    "analysis_type": "trip_mood_detection",
                    "mood_indicators": mood_analysis,
                    "primary_emotion": mood_analysis.get("primary_emotion"),
                    "stress_level": mood_analysis.get("stress_level")
                }
            )
            
            # Store vector embedding for mood pattern recognition
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Mood Analysis: {query}\nDetected: {mood_analysis}",
                metadata={
                    "agent": self.name,
                    "domain": "travel_emotions",
                    "mood_type": mood_analysis.get("primary_emotion", "neutral")
                }
            )
            
            return self.format_state_response(
                state=state,
                response=enhanced_response,
                additional_data={
                    "mood_analysis": mood_analysis,
                    "orchestration": {
                        "strategy": "mood_detection",
                        "selected_agents": [self.name],
                        "emotional_state": mood_analysis.get("primary_emotion"),
                        "support_needed": mood_analysis.get("support_level", "low")
                    }
                }
            )
            
        except Exception as e:
            return self.handle_error(state, e)
    
    def _analyze_mood_indicators(self, text: str) -> Dict[str, Any]:
        """Analyze text for mood and emotional indicators"""
        analysis = {
            "primary_emotion": "neutral",
            "stress_level": "low",
            "excitement_level": "medium",
            "indecision_level": "low",
            "confidence_level": "medium",
            "support_level": "low",
            "detected_emotions": [],
            "mood_keywords": []
        }
        
        text_lower = text.lower()
        
        # Excitement indicators
        excitement_words = ["excited", "thrilled", "amazing", "awesome", "fantastic", "can't wait", "love", "perfect"]
        excitement_score = sum(1 for word in excitement_words if word in text_lower)
        
        if excitement_score >= 3:
            analysis["excitement_level"] = "high"
            analysis["primary_emotion"] = "excited"
        elif excitement_score >= 1:
            analysis["excitement_level"] = "medium"
        
        # Stress indicators
        stress_words = ["stressed", "worried", "anxious", "overwhelmed", "pressure", "difficult", "hard", "problem"]
        stress_score = sum(1 for word in stress_words if word in text_lower)
        
        if stress_score >= 2:
            analysis["stress_level"] = "high"
            analysis["primary_emotion"] = "stressed"
            analysis["support_level"] = "high"
        elif stress_score >= 1:
            analysis["stress_level"] = "medium"
            analysis["support_level"] = "medium"
        
        # Indecision indicators
        indecision_words = ["unsure", "don't know", "maybe", "not sure", "confused", "torn", "can't decide"]
        indecision_score = sum(1 for word in indecision_words if word in text_lower)
        
        if indecision_score >= 2:
            analysis["indecision_level"] = "high"
            analysis["support_level"] = "high"
        elif indecision_score >= 1:
            analysis["indecision_level"] = "medium"
        
        # Confidence indicators
        confidence_words = ["sure", "definitely", "certain", "confident", "decided", "clear", "know exactly"]
        confidence_score = sum(1 for word in confidence_words if word in text_lower)
        
        if confidence_score >= 2:
            analysis["confidence_level"] = "high"
        elif confidence_score == 0 and indecision_score > 0:
            analysis["confidence_level"] = "low"
        
        # Question marks and uncertainty
        question_count = text.count("?")
        if question_count >= 3:
            analysis["indecision_level"] = "high"
            analysis["support_level"] = "medium"
        
        # Collect detected emotions
        all_emotion_words = excitement_words + stress_words + indecision_words + confidence_words
        for word in all_emotion_words:
            if word in text_lower:
                analysis["detected_emotions"].append(word)
                analysis["mood_keywords"].append(word)
        
        return analysis
    
    def _format_mood_response(self, response: str, mood_analysis: Dict[str, Any]) -> str:
        """Format the mood analysis response"""
        formatted_parts = [
            "😊 **Trip Mood Analysis**\n",
            f"**Emotional Assessment:** {response}\n"
        ]
        
        # Add mood indicators
        primary_emotion = mood_analysis.get("primary_emotion", "neutral")
        emotion_emoji = {
            "excited": "🎉",
            "stressed": "😰", 
            "neutral": "😐",
            "confident": "😎",
            "uncertain": "🤔"
        }
        
        formatted_parts.append(f"**{emotion_emoji.get(primary_emotion, '😐')} Primary Emotion:** {primary_emotion.title()}")
        
        # Add levels
        formatted_parts.append(f"**📊 Emotional Levels:**")
        formatted_parts.append(f"- Excitement: {mood_analysis.get('excitement_level', 'medium').title()}")
        formatted_parts.append(f"- Stress: {mood_analysis.get('stress_level', 'low').title()}")
        formatted_parts.append(f"- Confidence: {mood_analysis.get('confidence_level', 'medium').title()}")
        formatted_parts.append(f"- Indecision: {mood_analysis.get('indecision_level', 'low').title()}")
        
        # Add support recommendation
        support_level = mood_analysis.get("support_level", "low")
        if support_level == "high":
            formatted_parts.append(f"\n**💡 Recommendation:** High support needed - consider breaking down planning into smaller steps")
        elif support_level == "medium":
            formatted_parts.append(f"\n**💡 Recommendation:** Some guidance would be helpful - focus on key decisions first")
        
        formatted_parts.append("\n**Trip Mood Detector** | Understanding your travel planning emotions")
        
        return "\n".join(formatted_parts)
    
    def can_handle(self, query: str) -> float:
        """Determine if this agent can handle the query"""
        base_confidence = super().can_handle(query)
        
        query_lower = query.lower()
        
        # High confidence for explicit mood/emotion queries
        emotion_terms = ["feeling", "mood", "excited", "nervous", "stressed", "worried"]
        if any(term in query_lower for term in emotion_terms):
            base_confidence = min(base_confidence + 0.4, 1.0)
        
        # Medium confidence for planning text with emotional indicators
        planning_terms = ["planning", "trip", "travel", "vacation"]
        uncertainty_terms = ["unsure", "don't know", "confused", "help"]
        if any(term in query_lower for term in planning_terms) and any(term in query_lower for term in uncertainty_terms):
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        return base_confidence