from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class HumanRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    handle: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str = Field(min_length=1, max_length=64)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    actor_id: str
    handle: str
    actor_type: str


class RefreshRequest(BaseModel):
    refresh_token: str


class AgentRegisterRequest(BaseModel):
    handle: str = Field(min_length=3, max_length=32, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str = Field(min_length=1, max_length=64)
    agent_description: Optional[str] = Field(None, max_length=500)
    homepage_url: Optional[str] = Field(None, max_length=512)
    model_family: Optional[str] = Field(None, max_length=64)
    operator_contact: Optional[str] = Field(None, max_length=255)
    capabilities: Optional[dict] = None


class AgentRegisterResponse(BaseModel):
    actor_id: str
    handle: str
    api_key: str  # Only returned once at registration
    key_prefix: str


class ApiKeyCreateRequest(BaseModel):
    name: str = Field(default="default", min_length=1, max_length=64)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None


class ApiKeyCreatedResponse(ApiKeyResponse):
    api_key: str  # Only returned once at creation
