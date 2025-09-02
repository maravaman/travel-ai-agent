"""
Authentication utilities and password hashing
"""
import bcrypt
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from decouple import config
import mysql.connector
import logging

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = config("SECRET_KEY", default="your-super-secret-key-change-this-in-production")
ALGORITHM = config("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = config("ACCESS_TOKEN_EXPIRE_MINUTES", default=30, cast=int)

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, credentials_exception):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

class UserManager:
    """User management operations"""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def create_user(self, username: str, email: str, password: str) -> dict:
        """Create a new user"""
        try:
            hashed_password = get_password_hash(password)
            cursor = self.db.cursor(dictionary=True)
            
            # Check if user already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = %s OR email = %s",
                (username, email)
            )
            if cursor.fetchone():
                raise ValueError("Username or email already exists")
            
            # Insert new user
            cursor.execute(
                """INSERT INTO users (username, email, hashed_password) 
                   VALUES (%s, %s, %s)""",
                (username, email, hashed_password)
            )
            user_id = cursor.lastrowid
            
            # Get created user
            cursor.execute(
                "SELECT * FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            cursor.close()
            return user
            
        except mysql.connector.Error as e:
            logger.error(f"Database error creating user: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """Authenticate user credentials"""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND is_active = TRUE",
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            
            if not user:
                return None
            
            if not verify_password(password, user['hashed_password']):
                return None
            
            # Update last login
            self.update_last_login(user['id'])
            return user
            
        except mysql.connector.Error as e:
            logger.error(f"Database error authenticating user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username"""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                "SELECT * FROM users WHERE username = %s AND is_active = TRUE",
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()
            return user
        except mysql.connector.Error as e:
            logger.error(f"Database error getting user: {e}")
            return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                "UPDATE users SET last_login = NOW() WHERE id = %s",
                (user_id,)
            )
            cursor.close()
        except mysql.connector.Error as e:
            logger.error(f"Database error updating last login: {e}")
    
    def get_recent_usage(self, user_id: int, limit: int = 10) -> list:
        """Get user's recent interactions"""
        try:
            cursor = self.db.cursor(dictionary=True)
            cursor.execute(
                """SELECT agent_name, query, response, timestamp, interaction_type
                   FROM agent_interactions 
                   WHERE user_id = %s 
                   ORDER BY timestamp DESC 
                   LIMIT %s""",
                (user_id, limit)
            )
            interactions = cursor.fetchall()
            cursor.close()
            return interactions
        except mysql.connector.Error as e:
            logger.error(f"Database error getting recent usage: {e}")
            return []
    
    def get_active_agents_for_user(self, user_id: int) -> list:
        """Get list of agents user has interacted with"""
        try:
            cursor = self.db.cursor()
            cursor.execute(
                """SELECT DISTINCT agent_name 
                   FROM agent_interactions 
                   WHERE user_id = %s 
                   ORDER BY agent_name""",
                (user_id,)
            )
            agents = [row[0] for row in cursor.fetchall()]
            cursor.close()
            return agents
        except mysql.connector.Error as e:
            logger.error(f"Database error getting active agents: {e}")
            return []
