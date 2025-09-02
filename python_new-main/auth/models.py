"""
Authentication models and schemas
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class RecentUsage(BaseModel):
    agent_name: str
    query: str
    response: str
    timestamp: datetime
    interaction_type: str

class UserSession(BaseModel):
    user: UserResponse
    recent_interactions: list[RecentUsage]
    active_agents: list[str]
