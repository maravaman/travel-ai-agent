# memory.py
import redis
import mysql.connector
from datetime import datetime, timedelta
import json
import time
import logging
from typing import List, Dict, Optional, Any
from config import Config

# Optional imports with fallbacks
try:
    import numpy as np
except ImportError:
    np = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self):
        # Get connection parameters from config
        redis_params = Config.get_redis_connection_params()
        mysql_params = Config.get_mysql_connection_params()
        
        # Redis setup
        self.redis_conn = redis.StrictRedis(**redis_params)
        try:
            self.redis_conn.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")

        # MySQL setup
        try:
            self.mysql_conn = mysql.connector.connect(**mysql_params)
            logger.info("✅ MySQL connected successfully")
        except Exception as e:
            logger.error(f"❌ MySQL connection failed: {e}")
            self.mysql_conn = None
        
        # Initialize sentence transformer for embeddings
        self.embedding_model = None
        if SentenceTransformer:
            try:
                self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                logger.info("✅ Embedding model loaded")
            except Exception as e:
                logger.warning(f"⚠️ Could not load embedding model: {e}")
        else:
            logger.info("📝 SentenceTransformer not available, vector search disabled")

    # ----------------------
    # SHORT-TERM MEMORY (Redis)
    # ----------------------
    def set_stm(self, user_id, agent_id, value, expiry=3600):
        """Set short-term memory with dynamic user ID"""
        key = f"stm:{user_id}:{agent_id}"
        result = self.redis_conn.setex(key, expiry, value)
        logger.debug(f"[SET] {key} => {value} (expires in {expiry}s)")
        return result

    def get_stm(self, user_id, agent_id):
        """Get short-term memory for dynamic user ID"""
        key = f"stm:{user_id}:{agent_id}"
        value = self.redis_conn.get(key)
        logger.debug(f"[GET] {key} => {value}")
        return value

    def get_all_stm_for_user(self, user_id):
        pattern = f"stm:{user_id}:*"
        keys = self.redis_conn.keys(pattern)
        result = {}
        for key in keys:
            agent_id = key.split(":")[-1]
            value = self.redis_conn.get(key)
            result[agent_id] = value
        return result


    # ----------------------
    # LONG-TERM MEMORY (MySQL)
    # ----------------------
    def store_ltm(self, user_id, agent_id, input_text, output_text):
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            """
            INSERT INTO agent_history (user_id, agent_id, input_text, output_text)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, agent_id, input_text, output_text)
        )
        self.mysql_conn.commit()
        cursor.close()

    def get_ltm_by_user(self, user_id):
        cursor = self.mysql_conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM ltm WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        results = cursor.fetchall()
        cursor.close()
        return results



    def get_ltm_by_agent(self, user_id, agent_id):
        cursor = self.mysql_conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM agent_history
            WHERE user_id = %s AND agent_id = %s
            ORDER BY timestamp DESC
            """,
            (user_id, agent_id)
        )
        results = cursor.fetchall()
        cursor.close()
        return results
    
    # def get_all_stm_for_user(self, user_id):
    #     pattern = f"stm:{user_id}:*"
    #     keys = self.redis_conn.keys(pattern)
    #     result = {}
    #     for key in keys:
    #         agent_id = key.decode().split(":")[-1]
    #         value = self.redis_conn.get(key).decode()
    #         result[agent_id] = value
    #     return result
    
    def set_ltm(self, user_id: str, agent_id: str, value: str):
        cursor = self.mysql_conn.cursor()
        cursor.execute(
            "REPLACE INTO ltm (user_id, agent_id, value) VALUES (%s, %s, %s)",
            (user_id, agent_id, value)
        )
        self.mysql_conn.commit()
    
    def get_recent_stm(self, user_id, agent_id=None, hours=1):
        """Get recent STM data for any user ID (supports dynamic users)"""
        pattern = f"stm:{user_id}:*"
        recent_data = []

        for key in self.redis_conn.scan_iter(pattern):
            ttl = self.redis_conn.ttl(key)
            if ttl != -2 and ttl > 0 and ttl <= hours * 3600:
                value = self.redis_conn.get(key)
                extracted_agent_id = key.decode('utf-8').split(":")[-1]
                recent_data.append({
                    "agent_id": extracted_agent_id,
                    "value": value.decode('utf-8') if value else None,
                    "ttl_seconds_remaining": ttl
                })

        return recent_data

    
    def get_recent_ltm(self, user_id, agent_id=None, days=1):
        cursor = self.mysql_conn.cursor(dictionary=True)
        cutoff_query = """
            SELECT * FROM ltm
            WHERE user_id = %s AND created_at >= NOW() - INTERVAL %s DAY
        """
        cursor.execute(cutoff_query, (user_id, days))
        return cursor.fetchall()


    
    def get_ltm_by_agent(self, user_id, agent_id):
        cursor = self.mysql_conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT * FROM ltm
            WHERE user_id = %s AND agent_id = %s
            ORDER BY created_at DESC
            """,
            (user_id, agent_id)
        )
        results = cursor.fetchall()
        cursor.close()
        return results

    
    # ----------------------
    # AGENT-BASED LTM METHODS (New constraint requirement)
    # ----------------------
    def store_agent_memory(self, agent_name: str, user_id: int, memory_key: str, memory_value: str, metadata: Dict = None):
        """Store LTM grouped by agent name rather than user_id"""
        try:
            cursor = self.mysql_conn.cursor()
            cursor.execute(
                """
                INSERT INTO ltm_by_agent (agent_name, user_id, memory_key, memory_value, context_metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                memory_value = VALUES(memory_value),
                context_metadata = VALUES(context_metadata),
                updated_at = CURRENT_TIMESTAMP
                """,
                (agent_name, user_id, memory_key, memory_value, json.dumps(metadata or {}))
            )
            cursor.close()
            logger.info(f"Stored memory for agent {agent_name}: {memory_key}")
        except Exception as e:
            logger.error(f"Error storing agent memory: {e}")
    
    def get_agent_memories(self, agent_name: str, user_id: Optional[int] = None, limit: int = 50) -> List[Dict]:
        """Get memories for a specific agent, optionally filtered by user"""
        try:
            cursor = self.mysql_conn.cursor(dictionary=True)
            if user_id:
                cursor.execute(
                    """
                    SELECT * FROM ltm_by_agent 
                    WHERE agent_name = %s AND user_id = %s 
                    ORDER BY updated_at DESC LIMIT %s
                    """,
                    (agent_name, user_id, limit)
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM ltm_by_agent 
                    WHERE agent_name = %s 
                    ORDER BY updated_at DESC LIMIT %s
                    """,
                    (agent_name, limit)
                )
            results = cursor.fetchall()
            cursor.close()
            return results
        except Exception as e:
            logger.error(f"Error getting agent memories: {e}")
            return []
    
    def store_interaction(self, user_id: int, agent_name: str, query: str, response: str, interaction_type: str = 'single'):
        """Store agent interaction with user"""
        try:
            cursor = self.mysql_conn.cursor()
            cursor.execute(
                """
                INSERT INTO agent_interactions (user_id, agent_name, query, response, interaction_type)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, agent_name, query, response, interaction_type)
            )
            cursor.close()
        except Exception as e:
            logger.error(f"Error storing interaction: {e}")
    
    def store_query(self, user_id: int, query: str, response: str, agent_name: str = 'general'):
        """Store query for search functionality - compatibility method"""
        # This method provides compatibility for the test suite
        # It stores the query as an interaction and as a vector embedding
        try:
            # Store as interaction
            self.store_interaction(user_id, agent_name, query, response)
            
            # Store as vector embedding for similarity search
            self.store_vector_embedding(user_id, agent_name, query, {'response': response})
            
            logger.info(f"Stored query for user {user_id}: {query[:50]}...")
        except Exception as e:
            logger.error(f"Error storing query: {e}")
    
    # ----------------------
    # VECTOR SIMILARITY SEARCH METHODS
    # ----------------------
    def store_vector_embedding(self, user_id: int, agent_name: str, content: str, metadata: Dict = None):
        """Store content with its vector embedding"""
        if not self.embedding_model:
            logger.error("Embedding model not available")
            return
        
        try:
            # Generate embedding
            embedding = self.embedding_model.encode(content)
            embedding_json = json.dumps(embedding.tolist())
            
            cursor = self.mysql_conn.cursor()
            cursor.execute(
                """
                INSERT INTO vector_embeddings (user_id, agent_name, content, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, agent_name, content, embedding_json, json.dumps(metadata or {}))
            )
            cursor.close()
            logger.info(f"Stored vector embedding for {agent_name}")
        except Exception as e:
            logger.error(f"Error storing vector embedding: {e}")
    
    def similarity_search(self, query: str, user_id: int, agent_name: Optional[str] = None, limit: int = 5) -> List[Dict]:
        """Perform similarity search on stored content"""
        if not self.embedding_model:
            logger.error("Embedding model not available")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query)
            
            # Get stored embeddings
            cursor = self.mysql_conn.cursor(dictionary=True)
            if agent_name:
                cursor.execute(
                    """
                    SELECT id, content, embedding, metadata, agent_name, created_at
                    FROM vector_embeddings 
                    WHERE user_id = %s AND agent_name = %s
                    """,
                    (user_id, agent_name)
                )
            else:
                cursor.execute(
                    """
                    SELECT id, content, embedding, metadata, agent_name, created_at
                    FROM vector_embeddings 
                    WHERE user_id = %s
                    """,
                    (user_id,)
                )
            
            stored_embeddings = cursor.fetchall()
            cursor.close()
            
            # Calculate similarities
            results = []
            for item in stored_embeddings:
                try:
                    stored_embedding = np.array(json.loads(item['embedding']))
                    similarity = np.dot(query_embedding, stored_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
                    )
                    
                    results.append({
                        'content': item['content'],
                        'agent_name': item['agent_name'],
                        'similarity': float(similarity),
                        'metadata': json.loads(item['metadata']),
                        'created_at': item['created_at']
                    })
                except Exception as e:
                    logger.warning(f"Error calculating similarity for item {item['id']}: {e}")
                    continue
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            return []
    
    def get_search_history_json(self, query: str, user_id: int, agent_name: Optional[str] = None) -> Dict:
        """Get similarity search results as JSON response (constraint requirement)"""
        similar_content = self.similarity_search(query, user_id, agent_name)
        
        # Also get recent interactions for context
        cursor = self.mysql_conn.cursor(dictionary=True)
        if agent_name:
            cursor.execute(
                """
                SELECT agent_name, query, response, timestamp 
                FROM agent_interactions 
                WHERE user_id = %s AND agent_name = %s 
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id, agent_name)
            )
        else:
            cursor.execute(
                """
                SELECT agent_name, query, response, timestamp 
                FROM agent_interactions 
                WHERE user_id = %s 
                ORDER BY timestamp DESC LIMIT 10
                """,
                (user_id,)
            )
        
        recent_interactions = cursor.fetchall()
        cursor.close()
        
        return {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "similar_content": similar_content,
            "recent_interactions": recent_interactions,
            "total_matches": len(similar_content)
        }
    
    @staticmethod
    def load_edges_only():
        with open("core/agents.json", "r") as f:
            config = json.load(f)
        return config.get("edges", {})
