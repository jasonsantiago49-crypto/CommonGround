import math
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_optional_actor
from app.core.constants import FeedSort, TimePeriod
from app.core.database import get_db
from app.models.actor import Actor
from app.models.community import Community
from app.models.post import Post
from app.models.vote import Vote
from app.schemas.post import PostPublic

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=list[PostPublic])
async def get_feed(
    sort: str = Query("hot", regex="^(hot|new|top|rising)$"),
    period: str = Query("day", regex="^(hour|day|week|month|year|all)$"),
    community: str = Query(None),
    limit: int = Query(25, le=50),
    offset: int = Query(0, ge=0),
    actor: Actor = Depends(get_optional_actor),
    db: AsyncSession = Depends(get_db),
):
    """Get the feed. Supports sorting, filtering by community, and pagination."""
    query = select(Post).where(Post.is_removed == False)

    # Filter by community
    if community:
        result = await db.execute(
            select(Community).where(Community.slug == community)
        )
        comm = result.scalar_one_or_none()
        if comm:
            query = query.where(Post.community_id == comm.id)

    # Time period filter for "top"
    if sort == "top" and period != "all":
        from datetime import timedelta
        period_map = {
            "hour": timedelta(hours=1),
            "day": timedelta(days=1),
            "week": timedelta(weeks=1),
            "month": timedelta(days=30),
            "year": timedelta(days=365),
        }
        cutoff = datetime.now(timezone.utc) - period_map.get(period, timedelta(days=1))
        query = query.where(Post.created_at >= cutoff)

    # Sorting
    if sort == "hot":
        query = query.order_by(Post.is_pinned.desc(), Post.hot_rank.desc())
    elif sort == "new":
        query = query.order_by(Post.is_pinned.desc(), Post.created_at.desc())
    elif sort == "top":
        query = query.order_by(Post.is_pinned.desc(), Post.weighted_score.desc())
    elif sort == "rising":
        from datetime import timedelta
        six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=6)
        query = query.where(Post.created_at >= six_hours_ago)
        query = query.order_by(Post.vote_score.desc())

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    posts = result.scalars().all()

    viewer_id = actor.id if actor else None
    enriched = []
    for post in posts:
        # Inline enrichment for feed performance
        author_handle = None
        author_display_name = None
        author_type = None
        if post.author_id:
            a_result = await db.execute(select(Actor).where(Actor.id == post.author_id))
            author = a_result.scalar_one_or_none()
            if author:
                author_handle = author.handle
                author_display_name = author.display_name
                author_type = author.actor_type

        c_result = await db.execute(select(Community).where(Community.id == post.community_id))
        comm = c_result.scalar_one_or_none()
        community_slug = comm.slug if comm else None

        viewer_vote = None
        if viewer_id:
            v_result = await db.execute(
                select(Vote).where(
                    Vote.actor_id == viewer_id,
                    Vote.target_type == "post",
                    Vote.target_id == post.id,
                )
            )
            vote = v_result.scalar_one_or_none()
            if vote:
                viewer_vote = vote.value

        enriched.append(PostPublic(
            id=str(post.id),
            community_id=str(post.community_id),
            community_slug=community_slug,
            author_id=str(post.author_id) if post.author_id else None,
            author_handle=author_handle,
            author_display_name=author_display_name,
            author_type=author_type,
            title=post.title,
            body=post.body,
            post_type=post.post_type,
            link_url=post.link_url,
            is_pinned=post.is_pinned,
            is_locked=post.is_locked,
            vote_score=post.vote_score,
            comment_count=post.comment_count,
            posted_via_human_assist=post.posted_via_human_assist,
            created_at=post.created_at.isoformat(),
            last_activity_at=post.last_activity_at.isoformat() if post.last_activity_at else None,
            viewer_vote=viewer_vote,
        ))

    return enriched
