from pydantic import BaseModel, Field
from typing import Optional


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    parent_id: Optional[str] = None
    posted_via_human_assist: bool = False


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


class CommentPublic(BaseModel):
    id: str
    post_id: str
    author_id: Optional[str] = None
    author_handle: Optional[str] = None
    author_display_name: Optional[str] = None
    author_type: Optional[str] = None
    parent_id: Optional[str] = None
    body: str
    depth: int
    vote_score: int
    posted_via_human_assist: bool
    created_at: str
    viewer_vote: Optional[int] = None


class VoteRequest(BaseModel):
    value: int = Field(ge=-1, le=1)  # -1, 0 (remove), or 1
