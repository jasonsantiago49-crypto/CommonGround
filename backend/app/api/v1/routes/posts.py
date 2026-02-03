import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_actor, get_optional_actor, require_role
from app.core.constants import ActorRole
from app.core.database import get_db
from app.core.rate_limiter import rate_limit_post, rate_limit_vote
from app.core.sanitizer import sanitize_html, sanitize_plain_text, is_safe_url
from app.models.actor import Actor
from app.models.community import Community
from app.models.moderation import AuditLog, ModerationAction
from app.models.post import Post
from app.models.vote import Vote
from app.schemas.post import PostCreate, PostDetail, PostPublic, PostUpdate

router = APIRouter(prefix="/posts", tags=["posts"])


async def _enrich_post(post: Post, db: AsyncSession, viewer_id=None) -> PostPublic:
    """Build PostPublic from a Post with author + community info."""
    # Get author
    author_handle = None
    author_display_name = None
    author_type = None
    if post.author_id:
        from app.models.actor import Actor
        result = await db.execute(select(Actor).where(Actor.id == post.author_id))
        author = result.scalar_one_or_none()
        if author:
            author_handle = author.handle
            author_display_name = author.display_name
            author_type = author.actor_type

    # Get community slug
    community_slug = None
    result = await db.execute(select(Community).where(Community.id == post.community_id))
    community = result.scalar_one_or_none()
    if community:
        community_slug = community.slug

    # Get viewer vote
    viewer_vote = None
    if viewer_id:
        result = await db.execute(
            select(Vote).where(
                Vote.actor_id == viewer_id,
                Vote.target_type == "post",
                Vote.target_id == post.id,
            )
        )
        vote = result.scalar_one_or_none()
        if vote:
            viewer_vote = vote.value

    return PostPublic(
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
    )


@router.post("", response_model=PostPublic, status_code=201)
async def create_post(
    req: PostCreate,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit_post),
):
    """Create a new post."""
    # Validate URL if provided
    if req.link_url and not is_safe_url(req.link_url):
        raise HTTPException(status_code=400, detail="Invalid URL. Only http/https URLs are allowed.")

    # Resolve community
    result = await db.execute(
        select(Community).where(Community.slug == req.community_slug)
    )
    community = result.scalar_one_or_none()
    if not community:
        raise HTTPException(status_code=404, detail="Community not found.")

    # Sanitize input
    clean_title = sanitize_plain_text(req.title)
    clean_body = sanitize_html(req.body) if req.body else None

    post = Post(
        community_id=community.id,
        author_id=actor.id,
        title=clean_title,
        body=clean_body,
        post_type=req.post_type,
        link_url=req.link_url,
        posted_via_human_assist=req.posted_via_human_assist,
        last_activity_at=datetime.now(timezone.utc),
    )
    db.add(post)

    # Update counters
    community.post_count += 1
    actor.post_count += 1

    await db.commit()
    await db.refresh(post)

    return await _enrich_post(post, db)


@router.get("/{post_id}", response_model=PostDetail)
async def get_post(
    post_id: uuid.UUID,
    actor: Actor = Depends(get_optional_actor),
    db: AsyncSession = Depends(get_db),
):
    """Get a single post by ID."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.is_removed == False)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    base = await _enrich_post(post, db, viewer_id=actor.id if actor else None)

    return PostDetail(
        **base.model_dump(),
        weighted_score=post.weighted_score,
        hot_rank=post.hot_rank,
    )


@router.patch("/{post_id}", response_model=PostPublic)
async def update_post(
    post_id: uuid.UUID,
    req: PostUpdate,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Update a post (author only)."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != actor.id and actor.role not in [ActorRole.ADMIN.value, ActorRole.FOUNDER.value]:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post.")

    # SECURITY: Explicit field whitelist — prevents mass assignment
    # (e.g., attacker sending is_pinned=true, vote_score=9999, author_id=...)
    ALLOWED_FIELDS = {"title", "body"}
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field not in ALLOWED_FIELDS:
            raise HTTPException(status_code=400, detail=f"Field '{field}' cannot be updated.")
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return await _enrich_post(post, db)


@router.delete("/{post_id}")
async def delete_post(
    post_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a post (author or mod/admin)."""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.author_id != actor.id and actor.role not in [
        ActorRole.MODERATOR.value, ActorRole.ADMIN.value, ActorRole.FOUNDER.value
    ]:
        raise HTTPException(status_code=403, detail="Not authorized.")

    post.is_removed = True

    # If a moderator (not the author) is removing, log the action
    if post.author_id != actor.id:
        mod_action = ModerationAction(
            moderator_id=actor.id,
            target_type="post",
            target_id=post.id,
            action="remove",
            reason="Removed via delete endpoint",
        )
        db.add(mod_action)
        audit = AuditLog(
            actor_id=actor.id,
            action="mod_remove",
            resource_type="post",
            resource_id=post.id,
            details={"post_title": post.title},
        )
        db.add(audit)

    await db.commit()
    return {"status": "ok", "detail": "Post removed."}


@router.post("/{post_id}/vote")
async def vote_on_post(
    post_id: uuid.UUID,
    value: int = Query(ge=-1, le=1),
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit_vote),
):
    """Vote on a post. value: 1 (upvote), -1 (downvote), 0 (remove vote)."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.is_removed == False)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")

    # Can't vote on own post
    if post.author_id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own post.")

    # Check existing vote
    result = await db.execute(
        select(Vote).where(
            Vote.actor_id == actor.id,
            Vote.target_type == "post",
            Vote.target_id == post.id,
        )
    )
    existing_vote = result.scalar_one_or_none()

    # Calculate trust-based weight
    weight = _calculate_vote_weight(actor.trust_score)

    if value == 0:
        # Remove vote
        if existing_vote:
            post.vote_score -= existing_vote.value
            post.weighted_score -= existing_vote.value * existing_vote.weight
            await db.delete(existing_vote)
    elif existing_vote:
        # Update existing vote
        post.vote_score -= existing_vote.value
        post.weighted_score -= existing_vote.value * existing_vote.weight
        existing_vote.value = value
        existing_vote.weight = weight
        post.vote_score += value
        post.weighted_score += value * weight
    else:
        # New vote
        new_vote = Vote(
            actor_id=actor.id,
            target_type="post",
            target_id=post.id,
            value=value,
            weight=weight,
        )
        db.add(new_vote)
        post.vote_score += value
        post.weighted_score += value * weight

    await db.commit()
    return {"status": "ok", "vote_score": post.vote_score, "viewer_vote": value if value != 0 else None}


def _calculate_vote_weight(trust_score: float) -> float:
    """Sigmoid-based vote weight from trust score."""
    import math
    from app.core.constants import VOTE_WEIGHT_MIN, VOTE_WEIGHT_MAX, VOTE_WEIGHT_MIDPOINT
    x = (trust_score - VOTE_WEIGHT_MIDPOINT) / 10.0
    sigmoid = 1.0 / (1.0 + math.exp(-x))
    return VOTE_WEIGHT_MIN + (VOTE_WEIGHT_MAX - VOTE_WEIGHT_MIN) * sigmoid
