#!/usr/bin/env python3
"""
🔐 Authentication Service
Handles user registration, login, session management, and activity tracking
"""
import bcrypt
import jwt
import secrets
import mysql.connector
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
import json
import os

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, 
                 mysql_host="localhost", 
                 mysql_user="root", 
                 mysql_password="root",
                 mysql_database="langgraph_ai_system",
                 jwt_secret=None,
                 session_expire_hours=24):
        
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.session_expire_hours = session_expire_hours
        
        # Database connection
        try:
            self.db = mysql.connector.connect(
                host=mysql_host,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                autocommit=True
            )
            logger.info("✅ Authentication service connected to database")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def _generate_session_token(self, user_id: int, username: str) -> str:
        """Generate JWT session token"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=self.session_expire_hours),
            'iat': datetime.utcnow()
        }
        try:
            token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
            logger.info(f"🔑 JWT Token generated: {token[:50]}... (length: {len(token)})")
            return token
        except Exception as e:
            logger.error(f"❌ JWT generation failed: {e}")
            return ""
    
    def _verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT session token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def register_user(self, username: str, email: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """Register a new user"""
        cursor = self.db.cursor(dictionary=True)
        
        try:
            # Check if username or email already exists
            cursor.execute(
                "SELECT id, username, email FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            existing = cursor.fetchone()
            
            if existing:
                if existing['username'] == username:
                    return {'success': False, 'error': 'Username already exists'}
                else:
                    return {'success': False, 'error': 'Email already exists'}
            
            # Hash password and create user
            password_hash = self._hash_password(password)
            cursor.execute(
                """INSERT INTO users (username, email, hashed_password, is_active, created_at) 
                   VALUES (%s, %s, %s, TRUE, NOW())""",
                (username, email, password_hash)
            )
            
            user_id = cursor.lastrowid
            
            # Log registration activity
            cursor.execute(
                """INSERT INTO user_activity (user_id, activity_type, activity_data, ip_address) 
                   VALUES (%s, 'register', %s, %s)""",
                (user_id, json.dumps({'username': username, 'email': email}), ip_address)
            )
            
            # Generate session token
            token = self._generate_session_token(user_id, username)
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=self.session_expire_hours)
            
            # Create session record
            cursor.execute(
                """INSERT INTO user_sessions (session_id, user_id, expires_at, ip_address) 
                   VALUES (%s, %s, %s, %s)""",
                (session_id, user_id, expires_at, ip_address)
            )
            
            logger.info(f"✅ User registered: {username} (ID: {user_id})")
            
            return {
                'success': True,
                'user_id': user_id,
                'username': username,
                'email': email,
                'token': token,
                'session_id': session_id,
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Registration error: {e}")
            return {'success': False, 'error': 'Registration failed'}
        finally:
            cursor.close()
    
    def login_user(self, username: str, password: str, ip_address: str = None) -> Dict[str, Any]:
        """Login user and create session"""
        cursor = self.db.cursor(dictionary=True)
        
        try:
            # Get user by username
            cursor.execute(
                "SELECT id, username, email, hashed_password, is_active FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                return {'success': False, 'error': 'Invalid username or password'}
            
            if not user['is_active']:
                return {'success': False, 'error': 'Account is disabled'}
            
            # Verify password
            if not self._verify_password(password, user['hashed_password']):
                return {'success': False, 'error': 'Invalid username or password'}
            
            # Update last login
            cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE id = %s",
                (user['id'],)
            )
            
            # Log login activity
            cursor.execute(
                """INSERT INTO user_activity (user_id, activity_type, activity_data, ip_address) 
                   VALUES (%s, 'login', %s, %s)""",
                (user['id'], json.dumps({'username': username}), ip_address)
            )
            
            # Generate session token and create session
            token = self._generate_session_token(user['id'], user['username'])
            session_id = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=self.session_expire_hours)
            
            cursor.execute(
                """INSERT INTO user_sessions (session_id, user_id, expires_at, ip_address) 
                   VALUES (%s, %s, %s, %s)""",
                (session_id, user['id'], expires_at, ip_address)
            )
            
            logger.info(f"✅ User logged in: {username} (ID: {user['id']})")
            
            return {
                'success': True,
                'user_id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'token': token,
                'session_id': session_id,
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return {'success': False, 'error': 'Login failed'}
        finally:
            cursor.close()
    
    def logout_user(self, session_id: str, ip_address: str = None) -> bool:
        """Logout user and invalidate session"""
        cursor = self.db.cursor()
        
        try:
            # Get user_id from session
            cursor.execute(
                "SELECT user_id FROM user_sessions WHERE session_id = %s AND is_active = TRUE",
                (session_id,)
            )
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                
                # Invalidate session
                cursor.execute(
                    "UPDATE user_sessions SET is_active = FALSE WHERE session_id = %s",
                    (session_id,)
                )
                
                # Log logout activity
                cursor.execute(
                    """INSERT INTO user_activity (user_id, session_id, activity_type, activity_data, ip_address) 
                       VALUES (%s, %s, 'logout', %s, %s)""",
                    (user_id, session_id, json.dumps({'logout_time': datetime.now().isoformat()}), ip_address)
                )
                
                logger.info(f"✅ User logged out: session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Logout error: {e}")
            return False
        finally:
            cursor.close()
    
    def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user from token"""
        # Verify JWT token
        payload = self._verify_session_token(token)
        if not payload:
            return None
        
        cursor = self.db.cursor(dictionary=True)
        
        try:
            # Get user details
            cursor.execute(
                "SELECT id, username, email, is_active, created_at, last_login FROM users WHERE id = %s",
                (payload['user_id'],)
            )
            user = cursor.fetchone()
            
            if user and user['is_active']:
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Get current user error: {e}")
            return None
        finally:
            cursor.close()
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user activity history"""
        cursor = self.db.cursor(dictionary=True)
        
        try:
            cursor.execute(
                """SELECT activity_type, activity_data, created_at, ip_address 
                   FROM user_activity 
                   WHERE user_id = %s 
                   ORDER BY created_at DESC 
                   LIMIT %s""",
                (user_id, limit)
            )
            
            activities = cursor.fetchall()
            
            # Parse JSON activity_data
            for activity in activities:
                if activity['activity_data']:
                    try:
                        activity['activity_data'] = json.loads(activity['activity_data'])
                    except:
                        activity['activity_data'] = {}
            
            return activities
            
        except Exception as e:
            logger.error(f"❌ Get user activity error: {e}")
            return []
        finally:
            cursor.close()
    
    def get_user_queries(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user query history"""
        cursor = self.db.cursor(dictionary=True)
        
        try:
            cursor.execute(
                """SELECT query_id, question, agent_used, response_text, edges_traversed, 
                          processing_time, created_at 
                   FROM user_queries 
                   WHERE user_id = %s 
                   ORDER BY created_at DESC 
                   LIMIT %s""",
                (user_id, limit)
            )
            
            queries = cursor.fetchall()
            
            # Parse JSON edges_traversed
            for query in queries:
                if query['edges_traversed']:
                    try:
                        query['edges_traversed'] = json.loads(query['edges_traversed'])
                    except:
                        query['edges_traversed'] = []
                
                # Truncate long responses for list view
                if len(query['response_text']) > 200:
                    query['response_preview'] = query['response_text'][:200] + "..."
                else:
                    query['response_preview'] = query['response_text']
            
            return queries
            
        except Exception as e:
            logger.error(f"❌ Get user queries error: {e}")
            return []
        finally:
            cursor.close()
    
    def log_user_query(self, user_id: int, session_id: str, question: str, 
                      agent_used: str, response_text: str, edges_traversed: List[str], 
                      processing_time: float = None) -> bool:
        """Log a user query for activity tracking"""
        cursor = self.db.cursor()
        
        try:
            # First check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            user_exists = cursor.fetchone()
            
            if not user_exists:
                # For non-existent users (like test users), create a temporary/anonymous user record
                # or simply skip logging to avoid foreign key constraint
                logger.debug(f"Skipping query log for non-existent user {user_id}")
                return True  # Return True to not break the flow
            
            # Check if session exists, if not create a temporary one or use None
            cursor.execute(
                "SELECT session_id FROM user_sessions WHERE session_id = %s AND user_id = %s",
                (session_id, user_id)
            )
            session_exists = cursor.fetchone()
            
            # If session doesn't exist, set session_id to None to avoid foreign key constraint
            actual_session_id = session_id if session_exists else None
            
            cursor.execute(
                """INSERT INTO user_queries (user_id, session_id, question, agent_used, 
                                           response_text, edges_traversed, processing_time) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, actual_session_id, question, agent_used, response_text,
                 json.dumps(edges_traversed), processing_time)
            )
            
            # Also log as activity
            cursor.execute(
                """INSERT INTO user_activity (user_id, session_id, activity_type, activity_data) 
                   VALUES (%s, %s, 'query', %s)""",
                (user_id, actual_session_id, json.dumps({
                    'question': question[:100] + "..." if len(question) > 100 else question,
                    'agent_used': agent_used,
                    'processing_time': processing_time
                }))
            )
            
            logger.info(f"✅ Query logged for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Log user query error: {e}")
            return False
        finally:
            cursor.close()
    
    def create_anonymous_user(self, user_id: int, username: str = None) -> bool:
        """Create an anonymous user for testing purposes"""
        cursor = self.db.cursor()
        
        try:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if cursor.fetchone():
                return True  # User already exists
            
            # Create anonymous user
            username = username or f"anonymous_user_{user_id}"
            email = f"anonymous_{user_id}@test.local"
            
            cursor.execute(
                """INSERT INTO users (id, username, email, hashed_password, is_active, created_at) 
                   VALUES (%s, %s, %s, %s, TRUE, NOW())
                   ON DUPLICATE KEY UPDATE username = VALUES(username)""",
                (user_id, username, email, "anonymous_hash")
            )
            
            logger.info(f"✅ Created anonymous user: {username} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Create anonymous user error: {e}")
            return False
        finally:
            cursor.close()
    
    def ensure_user_exists(self, user_id: int, username: str = None) -> bool:
        """Ensure a user exists, create anonymous if needed"""
        cursor = self.db.cursor()
        
        try:
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if cursor.fetchone():
                return True
            
            # Create anonymous user
            return self.create_anonymous_user(user_id, username)
            
        except Exception as e:
            logger.error(f"❌ Ensure user exists error: {e}")
            return False
        finally:
            cursor.close()
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        cursor = self.db.cursor()
        
        try:
            cursor.execute(
                "DELETE FROM user_sessions WHERE expires_at < NOW() OR is_active = FALSE"
            )
            
            deleted_count = cursor.rowcount
            logger.info(f"🧹 Cleaned up {deleted_count} expired sessions")
            return deleted_count
            
        except Exception as e:
            logger.error(f"❌ Cleanup sessions error: {e}")
            return 0
        finally:
            cursor.close()

# Global auth service instance
from config import config as app_config
auth_service = AuthService(
    mysql_host=app_config.MYSQL_HOST,
    mysql_user=app_config.MYSQL_USER,
    mysql_password=app_config.MYSQL_PASSWORD,
    mysql_database=app_config.MYSQL_DATABASE,
    jwt_secret=app_config.SECRET_KEY,
    session_expire_hours=int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '480')) // 60 if os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES') else 24
)
