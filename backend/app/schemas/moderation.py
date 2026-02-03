from pydantic import BaseModel, Field
from typing import Optional


class ModActionCreate(BaseModel):
    target_type: str = Field(..., pattern="^(post|comment)$")
    target_id: str
    action: str = Field(..., pattern="^(remove|restore|warn|mute|ban|pin|unpin|lock|unlock)$")
    reason: str = Field(..., min_length=1, max_length=2000)
    duration_hours: Optional[int] = Field(None, ge=1)
    flag_id: Optional[str] = None


class ModActionPublic(BaseModel):
    id: str
    moderator_handle: str
    moderator_type: str
    target_type: str
    target_id: str
    action: str
    reason: str
    duration_hours: Optional[int]
    is_reversed: bool
    created_at: str


class AuditEntry(BaseModel):
    id: str
    actor_handle: Optional[str]
    actor_type: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[dict]
    created_at: str
