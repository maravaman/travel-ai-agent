"""
Water Body Analyzer Agent
Specializes in analyzing water bodies, hydrological features, aquatic ecosystems,
and providing insights about water resources and activities.
"""

from typing import Dict, Any, List
import logging
from core.base_agent import BaseAgent, GraphState

logger = logging.getLogger(__name__)


class WaterBodyAnalyzerAgent(BaseAgent):
    """Agent specialized in water body and aquatic systems analysis"""
    
    def __init__(self, memory_manager=None, name: str = "WaterBodyAnalyzer"):
        super().__init__(memory_manager, name)
        self._description = "Water body and aquatic systems analysis agent for hydrological and marine insights"
        self._capabilities = [
            "water_quality_assessment",
            "aquatic_ecosystem_analysis", 
            "hydrological_modeling",
            "marine_biology_insights",
            "water_resource_management",
            "coastal_zone_analysis",
            "water_recreation_guidance"
        ]
    
    @property
    def keywords(self) -> List[str]:
        """Keywords that trigger this agent"""
        return [
            "water", "lake", "river", "ocean", "sea", "pond", "backwater",
            "aquatic", "marine", "coastal", "dam", "stream", "wetland",
            "hydrology", "watershed", "estuary", "reef"
        ]
    
    @property
    def system_prompt(self) -> str:
        """System prompt for this agent"""
        return """You are WaterBodyAnalyzer, an expert hydrologist and aquatic ecosystem specialist.
        Analyze water bodies and provide comprehensive insights about:
        - Water quality and environmental conditions
        - Aquatic biodiversity and ecosystem health
        - Hydrological processes and water cycle dynamics
        - Marine and freshwater conservation issues
        - Water resource management and sustainability
        - Recreation and tourism opportunities
        - Climate change impacts on water systems
        
        Provide scientifically accurate information tailored to different audiences and applications."""
    
    def get_capabilities(self) -> List[str]:
        """Return list of agent capabilities"""
        return self._capabilities
    
    def process(self, state: GraphState) -> GraphState:
        """Process water body analysis queries"""
        if not self.validate_state(state):
            return self.handle_error(state, ValueError("Invalid state received"))
        
        query = state.get("question", "")
        user_id = state.get("user_id", 0)
        
        try:
            self.log_processing(query, user_id)
            
            # Search for similar water-related queries
            search_results = self.search_similar_content(query, user_id, limit=3)
            
            # Get historical water research context
            historical_context = self.get_historical_context(user_id, days=7)
            
            # Build specialized context for water analysis
            context_parts = []
            if search_results.get("similar_content"):
                context_parts.append("Previous water-related research:")
                for item in search_results["similar_content"][:2]:
                    if isinstance(item, dict) and "content" in item:
                        context_parts.append(f"- {item['content'][:150]}...")
            
            if historical_context:
                context_parts.append("Your water research history:")
                for item in historical_context[-2:]:
                    if isinstance(item, dict) and "value" in item:
                        context_parts.append(f"- {item['value'][:150]}...")
            
            # Add water body type detection
            water_body_type = self._detect_water_body_type(query)
            if water_body_type != "general":
                context_parts.append(f"Detected water body type: {water_body_type}")
            
            context = "\n".join(context_parts) if context_parts else ""
            
            # Generate specialized water analysis response
            response = self.generate_response_with_context(
                query=query,
                context=context,
                temperature=0.6  # Balanced between factual and descriptive
            )
            
            # Store interaction with water-specific metadata
            self.store_interaction(
                user_id=user_id,
                query=query,
                response=response,
                interaction_type="water_body_analysis",
                metadata={
                    "water_body_type": water_body_type,
                    "analysis_focus": self._detect_analysis_focus(query)
                }
            )
            
            # Store vector embedding for future water research
            self.store_vector_embedding(
                user_id=user_id,
                content=f"Water Analysis Query: {query}\nAnalysis: {response}",
                metadata={
                    "agent": self.name,
                    "domain": "aquatic_systems", 
                    "water_body_type": water_body_type,
                    "analysis_focus": self._detect_analysis_focus(query)
                }
            )
            
            return self.format_state_response(
                state=state,
                response=response,
                additional_data={
                    "orchestration": {
                        "strategy": "water_body_analysis",
                        "selected_agents": [self.name],
                        "water_body_type": water_body_type,
                        "analysis_focus": self._detect_analysis_focus(query),
                        "context_used": bool(context_parts)
                    }
                }
            )
            
        except Exception as e:
            return self.handle_error(state, e)
    
    def can_handle(self, query: str) -> float:
        """
        Determine if this agent can handle the query
        Enhanced logic for water-related detection
        """
        base_confidence = super().can_handle(query)
        
        query_lower = query.lower()
        
        # High-confidence water system terms
        high_confidence_terms = ["water quality", "aquatic ecosystem", "marine life", "hydrology"]
        if any(term in query_lower for term in high_confidence_terms):
            base_confidence = min(base_confidence + 0.4, 1.0)
        
        # Specific water body names
        water_bodies = ["lake", "river", "ocean", "sea", "pond", "stream"]
        if any(body in query_lower for body in water_bodies):
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        # Water activities and properties
        water_activities = ["swimming", "fishing", "boating", "diving"]
        if any(activity in query_lower for activity in water_activities):
            base_confidence = min(base_confidence + 0.2, 1.0)
        
        # Environmental and conservation terms
        environmental_terms = ["pollution", "conservation", "ecosystem", "biodiversity"]
        if any(term in query_lower for term in environmental_terms):
            base_confidence = min(base_confidence + 0.1, 1.0)
        
        return base_confidence
    
    def _detect_water_body_type(self, query: str) -> str:
        """Detect the type of water body being discussed"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["ocean", "sea", "marine", "saltwater"]):
            return "marine"
        elif any(term in query_lower for term in ["river", "stream", "flowing"]):
            return "river_system"
        elif any(term in query_lower for term in ["lake", "pond", "reservoir"]):
            return "standing_water"
        elif any(term in query_lower for term in ["wetland", "marsh", "swamp"]):
            return "wetland"
        elif any(term in query_lower for term in ["coastal", "estuary", "bay"]):
            return "coastal"
        else:
            return "general"
    
    def _detect_analysis_focus(self, query: str) -> str:
        """Detect the focus area of the water analysis"""
        query_lower = query.lower()
        
        if any(term in query_lower for term in ["quality", "pollution", "contamination"]):
            return "water_quality"
        elif any(term in query_lower for term in ["ecosystem", "biodiversity", "species"]):
            return "ecological_analysis"
        elif any(term in query_lower for term in ["recreation", "tourism", "activities"]):
            return "recreation_assessment"
        elif any(term in query_lower for term in ["management", "conservation", "protection"]):
            return "resource_management"
        elif any(term in query_lower for term in ["climate", "change", "warming"]):
            return "climate_impact"
        else:
            return "general_inquiry"
    
    def assess_water_quality(self, water_parameters: Dict[str, float]) -> Dict[str, Any]:
        """
        Assess water quality based on provided parameters
        
        Args:
            water_parameters: Dictionary with water quality measurements
            
        Returns:
            Dictionary with quality assessment
        """
        assessment = {
            "overall_quality": "unknown",
            "parameter_status": {},
            "recommendations": [],
            "concerns": []
        }
        
        # Example parameter analysis (would use real standards)
        if "ph" in water_parameters:
            ph = water_parameters["ph"]
            if 6.5 <= ph <= 8.5:
                assessment["parameter_status"]["pH"] = "optimal"
            else:
                assessment["parameter_status"]["pH"] = "suboptimal"
                assessment["concerns"].append(f"pH level ({ph}) outside optimal range")
        
        if "dissolved_oxygen" in water_parameters:
            do = water_parameters["dissolved_oxygen"]
            if do >= 6.0:
                assessment["parameter_status"]["dissolved_oxygen"] = "good"
            elif do >= 4.0:
                assessment["parameter_status"]["dissolved_oxygen"] = "fair"
            else:
                assessment["parameter_status"]["dissolved_oxygen"] = "poor"
                assessment["concerns"].append("Low dissolved oxygen levels")
        
        return assessment
    
    def analyze_aquatic_habitat(self, habitat_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze aquatic habitat suitability and health
        
        Args:
            habitat_data: Dictionary with habitat information
            
        Returns:
            Dictionary with habitat analysis
        """
        habitat_analysis = {
            "habitat_quality": "unknown",
            "key_features": [],
            "species_suitability": {},
            "recommendations": []
        }
        
        # Analyze based on habitat characteristics
        if "vegetation_cover" in habitat_data:
            cover = habitat_data["vegetation_cover"]
            if cover > 0.6:
                habitat_analysis["key_features"].append("Rich aquatic vegetation")
            elif cover < 0.2:
                habitat_analysis["recommendations"].append("Consider habitat restoration")
        
        if "depth_variation" in habitat_data:
            if habitat_data["depth_variation"]:
                habitat_analysis["key_features"].append("Good depth diversity")
            else:
                habitat_analysis["recommendations"].append("Depth variation would improve habitat")
        
        return habitat_analysis
    
    def get_recreation_recommendations(self, water_body_type: str, season: str = "summer") -> List[str]:
        """
        Get recreation recommendations for specific water bodies
        
        Args:
            water_body_type: Type of water body
            season: Season for recommendations
            
        Returns:
            List of recreation recommendations
        """
        recommendations = []
        
        if water_body_type == "marine":
            recommendations.extend([
                "Check tide schedules for optimal timing",
                "Be aware of marine life and safety protocols", 
                "Consider water temperature and currents"
            ])
        elif water_body_type == "lake":
            recommendations.extend([
                "Perfect for swimming and water sports",
                "Great for fishing and boating",
                "Consider seasonal temperature variations"
            ])
        elif water_body_type == "river":
            recommendations.extend([
                "Ideal for kayaking and rafting",
                "Check flow rates and safety conditions",
                "Be aware of seasonal water level changes"
            ])
        
        if season == "winter":
            recommendations.append("Consider cold water safety precautions")
        elif season == "summer":
            recommendations.append("Peak season for water activities")
        
        return recommendations
