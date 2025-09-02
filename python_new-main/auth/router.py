"""
Authentication router with FastAPI endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta
from typing import Optional

from .models import UserCreate, UserLogin, Token, UserResponse, UserSession, RecentUsage
from .utils import (
    UserManager, 
    create_access_token, 
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from database.connection import get_mysql_conn

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

def get_user_manager():
    """Dependency to get UserManager instance"""
    db_conn = get_mysql_conn()
    return UserManager(db_conn)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_manager: UserManager = Depends(get_user_manager)
) -> dict:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    username = verify_token(credentials.credentials, credentials_exception)
    user = user_manager.get_user_by_username(username)
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Register a new user"""
    try:
        user = user_manager.create_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password
        )
        return UserResponse(
            id=user['id'],
            username=user['username'],
            email=user['email'],
            is_active=user['is_active'],
            created_at=user['created_at'],
            last_login=user['last_login']
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/login", response_model=Token)
async def login_user(
    user_data: UserLogin,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Authenticate user and return access token"""
    user = user_manager.authenticate_user(
        username=user_data.username,
        password=user_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username']}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information"""
    return UserResponse(
        id=current_user['id'],
        username=current_user['username'],
        email=current_user['email'],
        is_active=current_user['is_active'],
        created_at=current_user['created_at'],
        last_login=current_user['last_login']
    )

@router.get("/session", response_model=UserSession)
async def get_user_session(
    current_user: dict = Depends(get_current_user),
    user_manager: UserManager = Depends(get_user_manager)
):
    """Get user session with recent usage and active agents"""
    user_id = current_user['id']
    
    # Get recent interactions
    recent_interactions_raw = user_manager.get_recent_usage(user_id, limit=10)
    recent_interactions = [
        RecentUsage(
            agent_name=interaction['agent_name'],
            query=interaction['query'],
            response=interaction['response'],
            timestamp=interaction['timestamp'],
            interaction_type=interaction['interaction_type']
        )
        for interaction in recent_interactions_raw
    ]
    
    # Get active agents
    active_agents = user_manager.get_active_agents_for_user(user_id)
    
    return UserSession(
        user=UserResponse(
            id=current_user['id'],
            username=current_user['username'],
            email=current_user['email'],
            is_active=current_user['is_active'],
            created_at=current_user['created_at'],
            last_login=current_user['last_login']
        ),
        recent_interactions=recent_interactions,
        active_agents=active_agents
    )

@router.post("/logout")
async def logout_user(
    current_user: dict = Depends(get_current_user)
):
    """Logout user (client-side token removal)"""
    return {"message": "Successfully logged out"}

@router.get("/users/{username}/exists")
async def check_username_exists(
    username: str,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Check if username already exists"""
    user = user_manager.get_user_by_username(username)
    return {"exists": user is not None}
