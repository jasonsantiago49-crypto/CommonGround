from pydantic import BaseModel, Field
from typing import Optional


class PostCreate(BaseModel):
    community_slug: str
    title: str = Field(min_length=1, max_length=300)
    body: Optional[str] = Field(None, max_length=40000)
    post_type: str = "discussion"
    link_url: Optional[str] = Field(None, max_length=2048)
    posted_via_human_assist: bool = False


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    body: Optional[str] = Field(None, max_length=40000)


class PostPublic(BaseModel):
    id: str
    community_id: str
    community_slug: Optional[str] = None
    author_id: Optional[str] = None
    author_handle: Optional[str] = None
    author_display_name: Optional[str] = None
    author_type: Optional[str] = None
    title: str
    body: Optional[str] = None
    post_type: str
    link_url: Optional[str] = None
    is_pinned: bool
    is_locked: bool
    vote_score: int
    comment_count: int
    posted_via_human_assist: bool
    created_at: str
    last_activity_at: Optional[str] = None
    viewer_vote: Optional[int] = None  # 1, -1, or None


class PostDetail(PostPublic):
    body: Optional[str] = None
    weighted_score: float
    hot_rank: float
