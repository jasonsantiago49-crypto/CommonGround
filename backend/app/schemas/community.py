from pydantic import BaseModel, Field
from typing import Optional


class CommunityCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=1000)
    rules: Optional[dict] = None
    is_default: bool = False


class CommunityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=128)
    description: Optional[str] = Field(None, max_length=1000)
    rules: Optional[dict] = None


class CommunityPublic(BaseModel):
    id: str
    slug: str
    name: str
    description: Optional[str] = None
    rules: Optional[dict] = None
    is_default: bool
    member_count: int
    post_count: int
    created_at: str

    class Config:
        from_attributes = True
