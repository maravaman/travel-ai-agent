"""
Travel-specific Orchestrator
Handles routing and coordination for travel agents with UTP integration
"""

import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from core.travel_memory_manager import travel_memory_manager

logger = logging.getLogger(__name__)


class TravelOrchestrator:
    """Orchestrator specifically designed for travel assistant agents"""
    
    def __init__(self):
        self.travel_agents = {
            "TextTripAnalyzer": None,
            "TripMoodDetector": None, 
            "TripCommsCoach": None,
            "TripBehaviorGuide": None,
            "TripCalmPractice": None,
            "TripSummarySynth": None,
            # Extended existing agents for travel
            "WeatherAgent": None,
            "DiningAgent": None,
            "ScenicLocationFinderAgent": None
        }
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize travel agents"""
        try:
            # Import and initialize new travel agents
            from agents.text_trip_analyzer import TextTripAnalyzerAgent
            from agents.trip_mood_detector import TripMoodDetectorAgent
            from agents.trip_comms_coach import TripCommsCoachAgent
            from agents.trip_behavior_guide import TripBehaviorGuideAgent
            from agents.trip_calm_practice import TripCalmPracticeAgent
            from agents.trip_summary_synth import TripSummarySynthAgent
            
            self.travel_agents["TextTripAnalyzer"] = TextTripAnalyzerAgent(travel_memory_manager)
            self.travel_agents["TripMoodDetector"] = TripMoodDetectorAgent(travel_memory_manager)
            self.travel_agents["TripCommsCoach"] = TripCommsCoachAgent(travel_memory_manager)
            self.travel_agents["TripBehaviorGuide"] = TripBehaviorGuideAgent(travel_memory_manager)
            self.travel_agents["TripCalmPractice"] = TripCalmPracticeAgent(travel_memory_manager)
            self.travel_agents["TripSummarySynth"] = TripSummarySynthAgent(travel_memory_manager)
            
            # Try to import existing agents for travel extension
            try:
                from agents.weather_agent import WeatherAgent
                self.travel_agents["WeatherAgent"] = WeatherAgent(travel_memory_manager)
            except ImportError:
                logger.warning("WeatherAgent not available")
            
            try:
                from agents.dining_agent import DiningAgent
                self.travel_agents["DiningAgent"] = DiningAgent(travel_memory_manager)
            except ImportError:
                logger.warning("DiningAgent not available")
            
            try:
                from agents.scenic_location_finder import ScenicLocationFinderAgent
                self.travel_agents["ScenicLocationFinderAgent"] = ScenicLocationFinderAgent(travel_memory_manager)
            except ImportError:
                logger.warning("ScenicLocationFinderAgent not available")
            
            # Remove None agents
            self.travel_agents = {k: v for k, v in self.travel_agents.items() if v is not None}
            
            logger.info(f"Initialized {len(self.travel_agents)} travel agents")
            
        except Exception as e:
            logger.error(f"Error initializing travel agents: {e}")
    
    def process_chat_request(self, user_id: int, text: str, session_context: Dict, 
                           user_travel_profile: Dict, weekly_digest: Dict) -> Dict[str, Any]:
        """
        Process chat mode request with shallow guidance from relevant agents
        Target: < 3s response time
        """
        start_time = time.time()
        
        try:
            # Determine relevant agents for this query
            relevant_agents = self._select_chat_agents(text)
            
            logger.info(f"Chat mode: Selected {len(relevant_agents)} agents for query")
            
            # Execute relevant agents with shallow processing
            agent_responses = {}
            agents_involved = []
            
            for agent_name in relevant_agents:
                if agent_name in self.travel_agents:
                    try:
                        agent = self.travel_agents[agent_name]
                        
                        # Create state for agent
                        state = {
                            "question": text,
                            "user_id": user_id,
                            "user": str(user_id),
                            "mode": "chat",
                            "context": {
                                "session": session_context,
                                "utp": user_travel_profile,
                                "digest": weekly_digest
                            }
                        }
                        
                        # Process with timeout for chat SLA
                        result = agent.process(state)
                        agent_responses[agent_name] = result.get("response", "")
                        agents_involved.append(agent_name)
                        
                        # Break early if approaching SLA limit
                        if time.time() - start_time > 2.5:  # 2.5s limit for agent processing
                            logger.warning("Approaching chat SLA limit, stopping agent execution")
                            break
                            
                    except Exception as e:
                        logger.warning(f"Agent {agent_name} failed in chat mode: {e}")
                        continue
            
            # Always finish with synthesis
            if "TripSummarySynth" in self.travel_agents and "TripSummarySynth" not in agents_involved:
                try:
                    synth_agent = self.travel_agents["TripSummarySynth"]
                    synth_response = synth_agent.synthesize_multi_agent_response(agent_responses, user_id)
                    agent_responses["TripSummarySynth"] = synth_response
                    agents_involved.append("TripSummarySynth")
                except Exception as e:
                    logger.warning(f"Synthesis failed in chat mode: {e}")
            
            # Format final response
            final_response = self._format_chat_response(agent_responses)
            
            processing_time = time.time() - start_time
            
            return {
                "response": final_response,
                "agents_involved": agents_involved,
                "processing_time": processing_time,
                "mode": "chat"
            }
            
        except Exception as e:
            logger.error(f"Chat processing error: {e}")
            return {
                "response": f"Error processing chat request: {str(e)}",
                "agents_involved": ["ErrorHandler"],
                "processing_time": time.time() - start_time,
                "mode": "chat"
            }
    
    def process_batch_request(self, user_id: int, transcript: str, current_utp: Dict) -> Dict[str, Any]:
        """
        Process batch mode request with comprehensive analysis
        Target: < 60s response time
        """
        start_time = time.time()
        
        try:
            logger.info(f"Batch mode: Processing {len(transcript)} character transcript")
            
            # Run ALL travel agents for comprehensive analysis
            agent_responses = {}
            agents_involved = []
            
            # Process with all relevant agents
            for agent_name, agent in self.travel_agents.items():
                if agent_name == "TripSummarySynth":
                    continue  # Save synthesis for last
                
                try:
                    # Create state for agent
                    state = {
                        "question": transcript,
                        "user_id": user_id,
                        "user": str(user_id),
                        "mode": "recording",
                        "context": {
                            "utp": current_utp,
                            "transcript_length": len(transcript)
                        }
                    }
                    
                    # Process with agent
                    result = agent.process(state)
                    agent_responses[agent_name] = result.get("response", "")
                    agents_involved.append(agent_name)
                    
                    logger.debug(f"Batch: {agent_name} completed")
                    
                except Exception as e:
                    logger.warning(f"Agent {agent_name} failed in batch mode: {e}")
                    continue
            
            # Always finish with synthesis and UTP update
            if "TripSummarySynth" in self.travel_agents:
                try:
                    synth_agent = self.travel_agents["TripSummarySynth"]
                    
                    # Create synthesis state with all agent outputs
                    synth_state = {
                        "question": f"Synthesize comprehensive travel analysis from transcript",
                        "user_id": user_id,
                        "user": str(user_id),
                        "mode": "recording",
                        "agent_responses": agent_responses,
                        "context": {
                            "utp": current_utp,
                            "transcript": transcript
                        }
                    }
                    
                    synth_result = synth_agent.process(synth_state)
                    agent_responses["TripSummarySynth"] = synth_result.get("response", "")
                    agents_involved.append("TripSummarySynth")
                    
                except Exception as e:
                    logger.error(f"Synthesis failed in batch mode: {e}")
            
            # Format comprehensive response
            final_response = self._format_batch_response(agent_responses, transcript)
            
            processing_time = time.time() - start_time
            
            # Check SLA compliance
            if processing_time > 60.0:
                logger.warning(f"Batch SLA exceeded: {processing_time:.2f}s > 60s")
            
            return {
                "response": final_response,
                "agents_involved": agents_involved,
                "processing_time": processing_time,
                "mode": "recording",
                "utp_updated": True
            }
            
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            return {
                "response": f"Error processing batch request: {str(e)}",
                "agents_involved": ["ErrorHandler"],
                "processing_time": time.time() - start_time,
                "mode": "recording",
                "utp_updated": False
            }
    
    def _select_chat_agents(self, text: str) -> List[str]:
        """Select relevant agents for chat mode (shallow processing)"""
        text_lower = text.lower()
        selected_agents = []
        
        # Always include text analyzer for any planning text
        if any(word in text_lower for word in ["plan", "trip", "travel", "vacation"]):
            selected_agents.append("TextTripAnalyzer")
        
        # Mood detector for emotional indicators
        if any(word in text_lower for word in ["feel", "excited", "nervous", "stressed", "worried"]):
            selected_agents.append("TripMoodDetector")
        
        # Communication coach for interaction needs
        if any(word in text_lower for word in ["ask", "tell", "communicate", "hotel", "guide"]):
            selected_agents.append("TripCommsCoach")
        
        # Behavior guide for action/decision needs
        if any(word in text_lower for word in ["what should", "next step", "help", "how to"]):
            selected_agents.append("TripBehaviorGuide")
        
        # Calm practice for stress indicators
        if any(word in text_lower for word in ["calm", "relax", "overwhelmed", "anxious"]):
            selected_agents.append("TripCalmPractice")
        
        # Weather for weather-related queries
        if any(word in text_lower for word in ["weather", "climate", "temperature", "rain"]):
            selected_agents.append("WeatherAgent")
        
        # Dining for food-related queries
        if any(word in text_lower for word in ["restaurant", "food", "dining", "eat"]):
            selected_agents.append("DiningAgent")
        
        # Scenic for location queries
        if any(word in text_lower for word in ["scenic", "beautiful", "location", "destination"]):
            selected_agents.append("ScenicLocationFinderAgent")
        
        # Limit to 3 agents for chat mode SLA
        return selected_agents[:3]
    
    def _format_chat_response(self, agent_responses: Dict[str, str]) -> str:
        """Format chat mode response (quick format)"""
        if not agent_responses:
            return "No agents were able to process your request."
        
        if len(agent_responses) == 1:
            return list(agent_responses.values())[0]
        
        # Multi-agent chat response
        formatted_parts = ["🎯 **Quick Travel Guidance**\n"]
        
        agent_emojis = {
            "TextTripAnalyzer": "🔍",
            "TripMoodDetector": "😊", 
            "TripCommsCoach": "💬",
            "TripBehaviorGuide": "🧭",
            "TripCalmPractice": "🧘",
            "WeatherAgent": "🌤️",
            "DiningAgent": "🍽️",
            "ScenicLocationFinderAgent": "🏞️"
        }
        
        for agent_name, response in agent_responses.items():
            if agent_name == "TripSummarySynth":
                continue  # Skip synthesis in chat mode
            
            emoji = agent_emojis.get(agent_name, "🤖")
            clean_name = agent_name.replace("Agent", "").replace("Trip", "")
            
            # Truncate for chat mode
            truncated_response = response[:200] + "..." if len(response) > 200 else response
            formatted_parts.append(f"**{emoji} {clean_name}:** {truncated_response}")
        
        return "\n\n".join(formatted_parts)
    
    def _format_batch_response(self, agent_responses: Dict[str, str], transcript: str) -> str:
        """Format batch mode response (comprehensive format)"""
        formatted_parts = ["🎯 **Comprehensive Travel Analysis**\n"]
        formatted_parts.append(f"**Transcript Length:** {len(transcript)} characters")
        formatted_parts.append(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        # Agent emoji mapping
        agent_emojis = {
            "TextTripAnalyzer": "🔍",
            "TripMoodDetector": "😊",
            "TripCommsCoach": "💬", 
            "TripBehaviorGuide": "🧭",
            "TripCalmPractice": "🧘",
            "TripSummarySynth": "🎯",
            "WeatherAgent": "🌤️",
            "DiningAgent": "🍽️",
            "ScenicLocationFinderAgent": "🏞️"
        }
        
        # Add each agent's full analysis
        for agent_name, response in agent_responses.items():
            emoji = agent_emojis.get(agent_name, "🤖")
            clean_name = agent_name.replace("Agent", "").replace("Trip", "")
            
            formatted_parts.append(f"## {emoji} {clean_name}")
            formatted_parts.append(response)
            formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    def get_execution_log(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """Get detailed execution log for a session"""
        try:
            session_summary = travel_memory_manager.get_session_summary(user_id, session_id)
            
            execution_log = {
                "session_id": session_id,
                "user_id": user_id,
                "session_data": session_summary.get("session_data", {}),
                "total_turns": session_summary.get("total_turns", 0),
                "agents_used": [],
                "execution_timeline": []
            }
            
            # Analyze turns for agent usage
            for turn in session_summary.get("turns", []):
                if turn.get("role", "").startswith("agent:"):
                    agent_name = turn["role"].split(":")[1]
                    if agent_name not in execution_log["agents_used"]:
                        execution_log["agents_used"].append(agent_name)
                
                execution_log["execution_timeline"].append({
                    "timestamp": turn.get("ts"),
                    "role": turn.get("role"),
                    "text_length": len(turn.get("text", "")),
                    "metadata": turn.get("metadata", {})
                })
            
            return execution_log
            
        except Exception as e:
            logger.error(f"Error getting execution log: {e}")
            return {"error": str(e)}


# Global travel orchestrator instance
travel_orchestrator = TravelOrchestrator()