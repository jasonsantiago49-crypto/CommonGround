from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ActorPublic(BaseModel):
    id: str
    actor_type: str
    handle: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    is_verified: bool
    role: str
    trust_score: float
    post_count: int
    comment_count: int
    created_at: str

    class Config:
        from_attributes = True


class ActorProfile(ActorPublic):
    """Full profile for the actor themselves."""
    is_active: bool
    updated_at: str


class ActorUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=64)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=512)


class AgentProfilePublic(BaseModel):
    agent_description: Optional[str] = None
    homepage_url: Optional[str] = None
    capabilities: Optional[dict] = None
    model_family: Optional[str] = None

    class Config:
        from_attributes = True


class HumanProfilePublic(BaseModel):
    email_verified: bool = False

    class Config:
        from_attributes = True


class CouncilProfilePublic(BaseModel):
    model_provider: str
    model_id: str
    is_automated: bool

    class Config:
        from_attributes = True


class ActorDetailPublic(ActorPublic):
    """Public actor detail with type-specific profile."""
    agent_profile: Optional[AgentProfilePublic] = None
    council_profile: Optional[CouncilProfilePublic] = None
