from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str   # 支持用户名或邮箱
    password: str

class UserUpdate(BaseModel):
    avatar_url:       Optional[str] = None
    preferred_genres: Optional[str] = None

class UserResponse(BaseModel):
    id:               int
    username:         str
    email:            str
    avatar_url:       Optional[str]
    preferred_genres: Optional[str]
    created_at:       datetime

    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse

class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)