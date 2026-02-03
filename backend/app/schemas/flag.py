from pydantic import BaseModel, Field
from typing import Optional


class FlagCreate(BaseModel):
    target_type: str = Field(..., pattern="^(post|comment)$")
    target_id: str
    reason: str = Field(..., pattern="^(spam|harassment|misinformation|impersonation|crypto|violence|other)$")
    details: Optional[str] = Field(None, max_length=2000)


class FlagPublic(BaseModel):
    id: str
    reporter_handle: str
    reporter_type: str
    target_type: str
    target_id: str
    reason: str
    details: Optional[str]
    status: str
    reviewed_at: Optional[str]
    created_at: str


class FlagUpdate(BaseModel):
    status: str = Field(..., pattern="^(reviewed|actioned|dismissed)$")
