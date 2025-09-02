"""
Travel Assistant API Endpoints
Implements /travel/chat, /travel/batch, and /travel/profile endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime

from core.travel_memory_manager import travel_memory_manager
from auth.auth_endpoints import get_current_user

logger = logging.getLogger(__name__)

# Request/Response models
class ChatRequest(BaseModel):
    user_id: int
    text: str

class BatchRequest(BaseModel):
    user_id: int
    transcript: str

class TravelResponse(BaseModel):
    user_id: int
    response: str
    agents_involved: List[str]
    processing_time: float
    session_id: str
    mode: str

class UserTravelProfile(BaseModel):
    user_id: int
    destinations_of_interest: List[str]
    cuisine_preferences: List[str]
    climate_tolerance: Dict[str, Any]
    travel_pace: str
    behavioral_notes: Dict[str, Any]
    budget_patterns: Dict[str, Any]
    group_preferences: Dict[str, Any]
    activity_preferences: List[str]
    accommodation_preferences: List[str]
    last_updated: str
    profile_version: str

# Router
router = APIRouter(prefix="/travel", tags=["travel"])

@router.post("/chat", response_model=TravelResponse)
async def travel_chat(
    request: ChatRequest,
    current_user: Dict = Depends(get_current_user) if get_current_user else None
):
    """
    Chat Mode: Quick reflections, one query at a time
    SLA: < 3s typical response
    """
    start_time = time.time()
    
    try:
        user_id = request.user_id
        text = request.text
        
        logger.info(f"Processing chat request for user {user_id}: {text[:50]}...")
        
        # Get session context (last 7 days + UTP)
        session_context = travel_memory_manager.get_session_context(user_id, turn_limit=10)
        utp = travel_memory_manager.get_user_travel_profile(user_id)
        weekly_digest = travel_memory_manager.get_weekly_digest(user_id)
        
        # Add user turn to session
        travel_memory_manager.add_turn(user_id, "user", text)
        
        # Import and use the travel orchestrator
        from core.travel_orchestrator import travel_orchestrator
        
        # Process through travel orchestrator
        result = travel_orchestrator.process_chat_request(
            user_id=user_id,
            text=text,
            session_context=session_context,
            user_travel_profile=utp,
            weekly_digest=weekly_digest
        )
        
        # Add assistant turn to session
        travel_memory_manager.add_turn(
            user_id, 
            "assistant", 
            result["response"],
            metadata={
                "agents_involved": result["agents_involved"],
                "processing_time": result["processing_time"]
            }
        )
        
        processing_time = time.time() - start_time
        
        # Ensure SLA compliance
        if processing_time > 3.0:
            logger.warning(f"Chat SLA exceeded: {processing_time:.2f}s > 3s")
        
        return TravelResponse(
            user_id=user_id,
            response=result["response"],
            agents_involved=result["agents_involved"],
            processing_time=processing_time,
            session_id=session_context.get("session_id", ""),
            mode="chat"
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@router.post("/batch", response_model=TravelResponse)
async def travel_batch(
    request: BatchRequest,
    current_user: Dict = Depends(get_current_user) if get_current_user else None
):
    """
    Recording Mode: Analyze whole trip-planning conversation
    SLA: < 60s end-to-end
    """
    start_time = time.time()
    
    try:
        user_id = request.user_id
        transcript = request.transcript
        
        logger.info(f"Processing batch request for user {user_id}: {len(transcript)} characters")
        
        # Start new recording session
        session_id = travel_memory_manager.start_new_session(
            user_id, 
            mode="recording",
            title=f"Trip Recording - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Add transcript as single user turn
        travel_memory_manager.add_turn(user_id, "user", transcript, metadata={"type": "transcript"})
        
        # Get current UTP for context
        current_utp = travel_memory_manager.get_user_travel_profile(user_id)
        
        # Import and use the travel orchestrator
        from core.travel_orchestrator import travel_orchestrator
        
        # Process through travel orchestrator (batch mode)
        result = travel_orchestrator.process_batch_request(
            user_id=user_id,
            transcript=transcript,
            current_utp=current_utp
        )
        
        # Add synthesized response as assistant turn
        travel_memory_manager.add_turn(
            user_id,
            "assistant", 
            result["response"],
            metadata={
                "type": "batch_synthesis",
                "agents_involved": result["agents_involved"],
                "utp_updated": result.get("utp_updated", False)
            }
        )
        
        # End the recording session
        travel_memory_manager.end_session(user_id, session_id)
        
        processing_time = time.time() - start_time
        
        # Ensure SLA compliance
        if processing_time > 60.0:
            logger.warning(f"Batch SLA exceeded: {processing_time:.2f}s > 60s")
        
        return TravelResponse(
            user_id=user_id,
            response=result["response"],
            agents_involved=result["agents_involved"],
            processing_time=processing_time,
            session_id=session_id,
            mode="recording"
        )
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@router.get("/profile/{user_id}", response_model=UserTravelProfile)
async def get_travel_profile(
    user_id: int,
    current_user: Dict = Depends(get_current_user) if get_current_user else None
):
    """Get current User Travel Profile"""
    try:
        # Get UTP from cache or LTM
        utp = travel_memory_manager.get_user_travel_profile(user_id)
        
        if not utp:
            # Get from LTM if not cached
            from agents.trip_summary_synth import TripSummarySynthAgent
            synth_agent = TripSummarySynthAgent(travel_memory_manager)
            utp = synth_agent._get_user_travel_profile(user_id)
        
        return UserTravelProfile(
            user_id=user_id,
            destinations_of_interest=utp.get("destinations_of_interest", []),
            cuisine_preferences=utp.get("cuisine_preferences", []),
            climate_tolerance=utp.get("climate_tolerance", {}),
            travel_pace=utp.get("travel_pace", "balanced"),
            behavioral_notes=utp.get("behavioral_notes", {}),
            budget_patterns=utp.get("budget_patterns", {}),
            group_preferences=utp.get("group_preferences", {}),
            activity_preferences=utp.get("activity_preferences", []),
            accommodation_preferences=utp.get("accommodation_preferences", []),
            last_updated=utp.get("last_updated", datetime.now().isoformat()),
            profile_version=utp.get("profile_version", "1.0")
        )
        
    except Exception as e:
        logger.error(f"Error getting travel profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get travel profile: {str(e)}")

@router.put("/profile/{user_id}")
async def update_travel_profile(
    user_id: int,
    profile_updates: Dict[str, Any] = Body(...),
    current_user: Dict = Depends(get_current_user) if get_current_user else None
):
    """Update User Travel Profile"""
    try:
        # Get current profile
        current_utp = travel_memory_manager.get_user_travel_profile(user_id)
        
        if not current_utp:
            from agents.trip_summary_synth import TripSummarySynthAgent
            synth_agent = TripSummarySynthAgent(travel_memory_manager)
            current_utp = synth_agent._get_default_travel_profile()
        
        # Update profile with new data
        updated_utp = current_utp.copy()
        updated_utp.update(profile_updates)
        updated_utp["last_updated"] = datetime.now().isoformat()
        
        # Store updated profile
        travel_memory_manager.cache_user_travel_profile(user_id, updated_utp)
        
        # Also store in LTM
        from agents.trip_summary_synth import TripSummarySynthAgent
        synth_agent = TripSummarySynthAgent(travel_memory_manager)
        synth_agent._store_user_travel_profile(user_id, updated_utp)
        
        return {"message": "Profile updated successfully", "profile": updated_utp}
        
    except Exception as e:
        logger.error(f"Error updating travel profile: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update travel profile: {str(e)}")

@router.get("/sessions/{user_id}")
async def get_user_sessions(
    user_id: int,
    limit: int = 10,
    current_user: Dict = Depends(get_current_user) if get_current_user else None
):
    """Get user's recent travel planning sessions"""
    try:
        # Get recent session IDs from Redis
        recent_turns = travel_memory_manager.redis_conn.zrevrange(f"stm:recent:{user_id}", 0, limit-1, withscores=True)
        
        sessions = []
        seen_sessions = set()
        
        for turn_id, timestamp in recent_turns:
            # Extract session info from turn
            turn_data = travel_memory_manager.redis_conn.hgetall(f"stm:turn:{user_id}:{turn_id}")
            if turn_data:
                # Find session this turn belongs to
                session_keys = travel_memory_manager.redis_conn.keys(f"stm:sess:{user_id}:*:turns")
                for session_key in session_keys:
                    if travel_memory_manager.redis_conn.lpos(session_key, turn_id) is not None:
                        session_id = session_key.split(":")[3]
                        if session_id not in seen_sessions:
                            session_data = travel_memory_manager.get_session_metadata(user_id, session_id)
                            if session_data:
                                sessions.append({
                                    "session_id": session_id,
                                    "title": session_data.get("title", "Travel Planning"),
                                    "mode": session_data.get("mode", "chat"),
                                    "started_at": session_data.get("started_at"),
                                    "turn_count": int(session_data.get("turn_count", 0))
                                })
                                seen_sessions.add(session_id)
                        break
        
        return {"sessions": sessions[:limit]}
        
    except Exception as e:
        logger.error(f"Error getting user sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.get("/session/{user_id}/{session_id}")
async def get_session_details(
    user_id: int,
    session_id: str,
    current_user: Dict = Depends(get_current_user) if get_current_user else None
):
    """Get detailed information about a specific session"""
    try:
        session_summary = travel_memory_manager.get_session_summary(user_id, session_id)
        return session_summary
        
    except Exception as e:
        logger.error(f"Error getting session details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session details: {str(e)}")

# Export router
__all__ = ['router']