"""
Trip Behavior Guide Agent
Provides behavioral nudges and next steps based on location and context
"""

from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent, GraphState

logger = logging.getLogger(__name__)


class TripBehaviorGuideAgent(BaseAgent):
    """Agent specialized in providing behavioral guidance and next steps for travelers"""
    
    def __init__(self, memory_manager=None, name: str = "TripBehaviorGuide"):
        super().__init__(memory_manager, name)
        self._description = "Provides behavioral nudges, next steps, and actionable guidance based on travel context"
        self._capabilities = [
            "behavioral_guidance",
            "next_step_planning",
            "decision_support",
            "action_prioritization",
            "habit_formation",
            "progress_tracking"
        ]
    
    @property
    def keywords(self) -> List[str]:
        """Keywords that trigger this agent"""
        return [
            "next", "step", "action", "do", "should", "behavior", "habit",
            "guide", "advice", "recommend", "suggest", "help", "what now",
            "priority", "first", "start", "begin", "organize", "plan"
        ]
    
    @property
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        return """You are TripBehaviorGuide, an expert behavioral coach for travelers.
        
        Your role is to provide:
        - Clear, actionable next steps for travel planning
        - Behavioral nudges to overcome decision paralysis
        - Prioritized action lists based on urgency and importance
        - Habit-forming suggestions for better travel planning
        - Progress tracking and milestone guidance
        - Location-specific behavioral recommendations
        
        Always provide concrete, specific actions that travelers can take immediately."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self._capabilities
    
    def process(self, state: GraphState) -> GraphState:
        """Process behavioral guidance queries"""
        if not self.validate_state(state):
            return self.handle_error(state, ValueError("Invalid state received"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            self.log_processing(query, user_id)
            
            # Analyze behavioral context and needs
            behavior_analysis = self._analyze_behavioral_needs(query)
            
            # Search for similar behavioral guidance scenarios
            search_results = self.search_similar_content(query, user_id, limit=3)
            
            # Get user's behavioral patterns from history
            historical_context = self.get_historical_context(user_id, days=21)
            
            # Build context for behavioral guidance
            context_parts = []
            if search_results.get("similar_content"):
                context_parts.append("Previous behavioral guidance:")
                for item in search_results["similar_content"][:2]:
                    if isinstance(item, dict) and "content" in item:
                        context_parts.append(f"- {item['content'][:150]}...")
            
            if historical_context:
                context_parts.append("User's behavioral patterns:")
                for item in historical_context[-3:]:
                    if isinstance(item, dict) and "value" in item:
                        context_parts.append(f"- {item['value'][:100]}...")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            # Generate behavioral guidance
            response = self.generate_response_with_context(
                query=f"Provide behavioral guidance and next steps for this travel situation: {query}",
                context=context,
                temperature=0.5  # Balanced for practical and creative advice
            )
            
            # Enhance response with structured action steps
            enhanced_response = self._format_behavior_response(response, behavior_analysis)
            
            # Store interaction with behavioral metadata
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=enhanced_response,
                interaction_type="behavioral_guidance",
                metadata={
                    "analysis_type": "travel_behavior",
                    "behavioral_context": behavior_analysis,
                    "guidance_type": behavior_analysis.get("guidance_type"),
                    "urgency_level": behavior_analysis.get("urgency_level")
                }
            )
            
            # Store vector embedding for behavioral pattern learning
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Behavioral Guidance: {query}\nAnalysis: {behavior_analysis}",
                metadata={
                    "agent": self.name,
                    "domain": "travel_behavior",
                    "guidance_type": behavior_analysis.get("guidance_type", "general")
                }
            )
            
            return self.format_state_response(
                state=state,
                response=enhanced_response,
                additional_data={
                    "behavioral_analysis": behavior_analysis,
                    "orchestration": {
                        "strategy": "behavioral_guidance",
                        "selected_agents": [self.name],
                        "guidance_type": behavior_analysis.get("guidance_type"),
                        "action_steps_provided": True
                    }
                }
            )
            
        except Exception as e:
            return self.handle_error(state, e)
    
    def _analyze_behavioral_needs(self, text: str) -> Dict[str, Any]:
        """Analyze text for behavioral guidance needs"""
        analysis = {
            "guidance_type": "general",
            "urgency_level": "medium",
            "decision_stage": "planning",
            "behavioral_barriers": [],
            "action_readiness": "medium",
            "support_needed": []
        }
        
        text_lower = text.lower()
        
        # Identify guidance type
        if any(word in text_lower for word in ["overwhelmed", "too many", "confused", "don't know where"]):
            analysis["guidance_type"] = "decision_simplification"
            analysis["behavioral_barriers"].append("overwhelm")
            analysis["support_needed"].append("prioritization")
        elif any(word in text_lower for word in ["procrastinating", "putting off", "later", "tomorrow"]):
            analysis["guidance_type"] = "motivation"
            analysis["behavioral_barriers"].append("procrastination")
            analysis["support_needed"].append("momentum")
        elif any(word in text_lower for word in ["organize", "structure", "plan", "systematic"]):
            analysis["guidance_type"] = "organization"
            analysis["support_needed"].append("structure")
        elif any(word in text_lower for word in ["budget", "money", "cost", "expensive"]):
            analysis["guidance_type"] = "financial_planning"
            analysis["support_needed"].append("budget_management")
        
        # Identify urgency level
        if any(word in text_lower for word in ["urgent", "asap", "soon", "deadline", "leaving"]):
            analysis["urgency_level"] = "high"
        elif any(word in text_lower for word in ["eventually", "someday", "future", "thinking about"]):
            analysis["urgency_level"] = "low"
        
        # Identify decision stage
        if any(word in text_lower for word in ["just started", "beginning", "first time"]):
            analysis["decision_stage"] = "initial"
        elif any(word in text_lower for word in ["almost done", "final", "last step", "booking"]):
            analysis["decision_stage"] = "final"
        elif any(word in text_lower for word in ["stuck", "can't decide", "between"]):
            analysis["decision_stage"] = "decision_point"
        
        # Assess action readiness
        action_words = ["ready", "let's do", "want to", "going to", "will"]
        if any(word in text_lower for word in action_words):
            analysis["action_readiness"] = "high"
        elif any(word in text_lower for word in ["maybe", "might", "considering", "thinking"]):
            analysis["action_readiness"] = "low"
        
        return analysis
    
    def _format_behavior_response(self, response: str, analysis: Dict[str, Any]) -> str:
        """Format the behavioral guidance response with action steps"""
        guidance_emoji = {
            "decision_simplification": "🎯",
            "motivation": "⚡",
            "organization": "📋",
            "financial_planning": "💰",
            "general": "🧭"
        }
        
        guidance_type = analysis.get("guidance_type", "general")
        emoji = guidance_emoji.get(guidance_type, "🧭")
        
        formatted_parts = [
            f"{emoji} **Travel Behavior Guide**\n",
            f"**Guidance Type:** {guidance_type.replace('_', ' ').title()}",
            f"**Urgency Level:** {analysis.get('urgency_level', 'medium').title()}",
            f"**Decision Stage:** {analysis.get('decision_stage', 'planning').replace('_', ' ').title()}\n",
            f"**Behavioral Guidance:** {response}\n"
        ]
        
        # Add specific action steps based on analysis
        action_steps = self._generate_action_steps(analysis)
        if action_steps:
            formatted_parts.append("**📋 Immediate Action Steps:**")
            for i, step in enumerate(action_steps, 1):
                formatted_parts.append(f"{i}. {step}")
        
        # Add behavioral tips
        behavioral_tips = self._get_behavioral_tips(analysis)
        if behavioral_tips:
            formatted_parts.append(f"\n**💡 Behavioral Tips:**")
            for tip in behavioral_tips:
                formatted_parts.append(f"• {tip}")
        
        formatted_parts.append("\n**Trip Behavior Guide** | Actionable guidance for effective travel planning")
        
        return "\n".join(formatted_parts)
    
    def _generate_action_steps(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate specific action steps based on behavioral analysis"""
        guidance_type = analysis.get("guidance_type", "general")
        urgency = analysis.get("urgency_level", "medium")
        
        if guidance_type == "decision_simplification":
            return [
                "List your top 3 must-have requirements for this trip",
                "Set a maximum budget range to narrow options",
                "Choose one decision to make today (destination, dates, or accommodation)"
            ]
        elif guidance_type == "motivation":
            return [
                "Set a 15-minute timer and complete one small planning task",
                "Book one refundable item (flight or hotel) to create momentum",
                "Share your travel plans with someone to create accountability"
            ]
        elif guidance_type == "organization":
            return [
                "Create a simple checklist with 5-7 main planning categories",
                "Set specific deadlines for each major decision",
                "Use a travel planning app or spreadsheet to track progress"
            ]
        elif guidance_type == "financial_planning":
            return [
                "Calculate your total available budget including all expenses",
                "Research average costs for your destination and activities",
                "Set aside 20% buffer for unexpected expenses"
            ]
        else:
            # General action steps
            if urgency == "high":
                return [
                    "Identify the most time-sensitive decision that needs to be made",
                    "Gather essential information for that decision only",
                    "Make the decision and move to the next priority"
                ]
            else:
                return [
                    "Define your travel goals and priorities clearly",
                    "Research your top 2-3 destination options",
                    "Set a timeline for making key decisions"
                ]
    
    def _get_behavioral_tips(self, analysis: Dict[str, Any]) -> List[str]:
        """Get behavioral tips based on analysis"""
        tips = []
        
        barriers = analysis.get("behavioral_barriers", [])
        support_needed = analysis.get("support_needed", [])
        
        if "overwhelm" in barriers:
            tips.append("Break large decisions into smaller, manageable choices")
            tips.append("Focus on one aspect at a time (destination first, then accommodation)")
        
        if "procrastination" in barriers:
            tips.append("Use the 2-minute rule: if it takes less than 2 minutes, do it now")
            tips.append("Set specific deadlines and share them with someone")
        
        if "prioritization" in support_needed:
            tips.append("Use the MoSCoW method: Must have, Should have, Could have, Won't have")
        
        if "structure" in support_needed:
            tips.append("Follow a systematic approach: When → Where → How → What")
        
        if "budget_management" in support_needed:
            tips.append("Track expenses in real-time using a travel budget app")
        
        # Add general tips if no specific ones
        if not tips:
            tips = [
                "Start with the most important decision and work your way down",
                "Set realistic deadlines and celebrate small wins",
                "Remember that perfect planning isn't necessary for great trips"
            ]
        
        return tips[:3]  # Maximum 3 tips
    
    def can_handle(self, query: str) -> float:
        """Determine if this agent can handle the query"""
        base_confidence = super().can_handle(query)
        
        query_lower = query.lower()
        
        # High confidence for action/behavior queries
        action_terms = ["what should i do", "next step", "how to", "help me", "guide me"]
        if any(term in query_lower for term in action_terms):
            base_confidence = min(base_confidence + 0.4, 1.0)
        
        # Medium confidence for planning guidance
        planning_terms = ["planning", "organize", "structure", "approach"]
        if any(term in query_lower for term in planning_terms):
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        return base_confidence