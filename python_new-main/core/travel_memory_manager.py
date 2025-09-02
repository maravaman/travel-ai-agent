"""
Travel-specific Memory Manager
Implements session-based STM structure for Travel Assistant
"""

import redis
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from core.memory import MemoryManager

logger = logging.getLogger(__name__)


class TravelMemoryManager(MemoryManager):
    """Extended memory manager with travel-specific session management"""
    
    def __init__(self):
        super().__init__()
        self.session_timeout = 3600  # 60 minutes session timeout
    
    # Session Management
    def get_active_session(self, user_id: int) -> Optional[str]:
        """Get active session ID for user"""
        try:
            session_id = self.redis_conn.get(f"stm:active:{user_id}")
            if session_id:
                # Check if session is still valid (not expired)
                session_data = self.get_session_metadata(user_id, session_id)
                if session_data and self._is_session_active(session_data):
                    return session_id
                else:
                    # Session expired, clear it
                    self.redis_conn.delete(f"stm:active:{user_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting active session: {e}")
            return None
    
    def start_new_session(self, user_id: int, mode: str = "chat", title: str = None) -> str:
        """Start a new travel planning session"""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.now()
            
            # Set active session pointer
            self.redis_conn.setex(f"stm:active:{user_id}", self.session_timeout, session_id)
            
            # Create session metadata
            session_data = {
                "title": title or f"Travel Planning - {now.strftime('%Y-%m-%d %H:%M')}",
                "started_at": now.isoformat(),
                "last_at": now.isoformat(),
                "mode": mode,  # "chat" or "recording"
                "turn_count": 0
            }
            
            self.redis_conn.hmset(f"stm:sess:{user_id}:{session_id}", session_data)
            self.redis_conn.expire(f"stm:sess:{user_id}:{session_id}", 30 * 24 * 3600)  # 30 days
            
            # Initialize turn list
            self.redis_conn.expire(f"stm:sess:{user_id}:{session_id}:turns", 30 * 24 * 3600)
            
            logger.info(f"Started new {mode} session {session_id} for user {user_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting new session: {e}")
            return str(uuid.uuid4())  # Fallback
    
    def add_turn(self, user_id: int, role: str, text: str, metadata: Dict = None) -> str:
        """Add a turn to the current session"""
        try:
            # Get or create active session
            session_id = self.get_active_session(user_id)
            if not session_id:
                session_id = self.start_new_session(user_id)
            
            # Create turn
            turn_id = str(uuid.uuid4())
            turn_data = {
                "role": role,  # "user", "assistant", or "agent:AgentName"
                "text": text,
                "ts": datetime.now().isoformat(),
                "metadata": json.dumps(metadata or {})
            }
            
            # Store turn data
            self.redis_conn.hmset(f"stm:turn:{user_id}:{turn_id}", turn_data)
            self.redis_conn.expire(f"stm:turn:{user_id}:{turn_id}", 30 * 24 * 3600)
            
            # Add to session turn list
            self.redis_conn.lpush(f"stm:sess:{user_id}:{session_id}:turns", turn_id)
            
            # Update session metadata
            self.redis_conn.hset(f"stm:sess:{user_id}:{session_id}", "last_at", datetime.now().isoformat())
            self.redis_conn.hincrby(f"stm:sess:{user_id}:{session_id}", "turn_count", 1)
            
            # Add to recent index
            self.redis_conn.zadd(f"stm:recent:{user_id}", {turn_id: time.time()})
            self.redis_conn.zremrangebyrank(f"stm:recent:{user_id}", 0, -201)  # Keep last 200
            
            logger.debug(f"Added turn {turn_id} to session {session_id}")
            return turn_id
            
        except Exception as e:
            logger.error(f"Error adding turn: {e}")
            return str(uuid.uuid4())
    
    def get_session_context(self, user_id: int, turn_limit: int = 10) -> Dict[str, Any]:
        """Get context from current session for chat mode"""
        try:
            session_id = self.get_active_session(user_id)
            if not session_id:
                return {"turns": [], "session_id": None}
            
            # Get recent turns
            turn_ids = self.redis_conn.lrange(f"stm:sess:{user_id}:{session_id}:turns", 0, turn_limit - 1)
            
            turns = []
            for turn_id in turn_ids:
                turn_data = self.redis_conn.hgetall(f"stm:turn:{user_id}:{turn_id}")
                if turn_data:
                    turn_data["metadata"] = json.loads(turn_data.get("metadata", "{}"))
                    turns.append(turn_data)
            
            # Get session metadata
            session_data = self.get_session_metadata(user_id, session_id)
            
            return {
                "session_id": session_id,
                "session_data": session_data,
                "turns": turns,
                "turn_count": len(turns)
            }
            
        except Exception as e:
            logger.error(f"Error getting session context: {e}")
            return {"turns": [], "session_id": None}
    
    def get_session_metadata(self, user_id: int, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata"""
        try:
            return self.redis_conn.hgetall(f"stm:sess:{user_id}:{session_id}")
        except Exception as e:
            logger.error(f"Error getting session metadata: {e}")
            return None
    
    def _is_session_active(self, session_data: Dict[str, Any]) -> bool:
        """Check if session is still active (not timed out)"""
        try:
            last_at = datetime.fromisoformat(session_data.get("last_at", ""))
            return datetime.now() - last_at < timedelta(seconds=self.session_timeout)
        except Exception:
            return False
    
    def get_user_travel_profile(self, user_id: int) -> Dict[str, Any]:
        """Get cached User Travel Profile from STM"""
        try:
            utp_json = self.redis_conn.get(f"stm:utp:{user_id}")
            if utp_json:
                return json.loads(utp_json)
            return {}
        except Exception as e:
            logger.error(f"Error getting UTP from cache: {e}")
            return {}
    
    def cache_user_travel_profile(self, user_id: int, utp: Dict[str, Any]):
        """Cache User Travel Profile in STM"""
        try:
            utp_json = json.dumps(utp)
            self.redis_conn.setex(f"stm:utp:{user_id}", 7 * 24 * 3600, utp_json)  # 7 days
            logger.debug(f"Cached UTP for user {user_id}")
        except Exception as e:
            logger.error(f"Error caching UTP: {e}")
    
    def get_weekly_digest(self, user_id: int) -> Dict[str, Any]:
        """Get weekly digest from cache"""
        try:
            digest_json = self.redis_conn.get(f"stm:digest:{user_id}")
            if digest_json:
                return json.loads(digest_json)
            return {}
        except Exception as e:
            logger.error(f"Error getting weekly digest: {e}")
            return {}
    
    def cache_weekly_digest(self, user_id: int, digest: Dict[str, Any]):
        """Cache weekly digest in STM"""
        try:
            digest_json = json.dumps(digest)
            self.redis_conn.setex(f"stm:digest:{user_id}", 7 * 24 * 3600, digest_json)  # 7 days
            logger.debug(f"Cached weekly digest for user {user_id}")
        except Exception as e:
            logger.error(f"Error caching weekly digest: {e}")
    
    def end_session(self, user_id: int, session_id: str = None):
        """End current session"""
        try:
            if not session_id:
                session_id = self.get_active_session(user_id)
            
            if session_id:
                # Mark session as ended
                self.redis_conn.hset(f"stm:sess:{user_id}:{session_id}", "ended_at", datetime.now().isoformat())
                
                # Clear active session pointer
                self.redis_conn.delete(f"stm:active:{user_id}")
                
                logger.info(f"Ended session {session_id} for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error ending session: {e}")
    
    def get_session_summary(self, user_id: int, session_id: str) -> Dict[str, Any]:
        """Get summary of a completed session"""
        try:
            session_data = self.get_session_metadata(user_id, session_id)
            if not session_data:
                return {}
            
            # Get all turns
            turn_ids = self.redis_conn.lrange(f"stm:sess:{user_id}:{session_id}:turns", 0, -1)
            
            turns = []
            for turn_id in turn_ids:
                turn_data = self.redis_conn.hgetall(f"stm:turn:{user_id}:{turn_id}")
                if turn_data:
                    turns.append(turn_data)
            
            return {
                "session_data": session_data,
                "turns": turns,
                "total_turns": len(turns)
            }
            
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")
            return {}


# Global travel memory manager instance
travel_memory_manager = TravelMemoryManager()