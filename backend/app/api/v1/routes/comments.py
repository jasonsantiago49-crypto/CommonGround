import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_actor, get_optional_actor
from app.core.constants import ActorRole
from app.core.database import get_db
from app.core.rate_limiter import rate_limit_comment, rate_limit_vote
from app.core.sanitizer import sanitize_html
from app.models.actor import Actor
from app.models.comment import Comment
from app.models.moderation import AuditLog, ModerationAction
from app.models.post import Post
from app.models.vote import Vote
from app.schemas.comment import CommentCreate, CommentPublic, CommentUpdate

router = APIRouter(tags=["comments"])


async def _enrich_comment(comment: Comment, db: AsyncSession, viewer_id=None) -> CommentPublic:
    """Build CommentPublic from a Comment with author info."""
    author_handle = None
    author_display_name = None
    author_type = None
    if comment.author_id:
        result = await db.execute(select(Actor).where(Actor.id == comment.author_id))
        author = result.scalar_one_or_none()
        if author:
            author_handle = author.handle
            author_display_name = author.display_name
            author_type = author.actor_type

    viewer_vote = None
    if viewer_id:
        result = await db.execute(
            select(Vote).where(
                Vote.actor_id == viewer_id,
                Vote.target_type == "comment",
                Vote.target_id == comment.id,
            )
        )
        vote = result.scalar_one_or_none()
        if vote:
            viewer_vote = vote.value

    return CommentPublic(
        id=str(comment.id),
        post_id=str(comment.post_id),
        author_id=str(comment.author_id) if comment.author_id else None,
        author_handle=author_handle,
        author_display_name=author_display_name,
        author_type=author_type,
        parent_id=str(comment.parent_id) if comment.parent_id else None,
        body=comment.body,
        depth=comment.depth,
        vote_score=comment.vote_score,
        posted_via_human_assist=comment.posted_via_human_assist,
        created_at=comment.created_at.isoformat(),
        viewer_vote=viewer_vote,
    )


@router.get("/posts/{post_id}/comments", response_model=list[CommentPublic])
async def list_comments(
    post_id: uuid.UUID,
    sort: str = Query("best", regex="^(best|new|old)$"),
    actor: Actor = Depends(get_optional_actor),
    db: AsyncSession = Depends(get_db),
):
    """List comments for a post, sorted by best/new/old."""
    query = select(Comment).where(
        Comment.post_id == post_id,
        Comment.is_removed == False,
    )

    if sort == "best":
        query = query.order_by(Comment.weighted_score.desc(), Comment.created_at.asc())
    elif sort == "new":
        query = query.order_by(Comment.created_at.desc())
    else:  # old
        query = query.order_by(Comment.created_at.asc())

    result = await db.execute(query)
    comments = result.scalars().all()

    viewer_id = actor.id if actor else None
    return [await _enrich_comment(c, db, viewer_id) for c in comments]


@router.post("/posts/{post_id}/comments", response_model=CommentPublic, status_code=201)
async def create_comment(
    post_id: uuid.UUID,
    req: CommentCreate,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit_comment),
):
    """Create a comment on a post."""
    result = await db.execute(
        select(Post).where(Post.id == post_id, Post.is_removed == False)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found.")
    if post.is_locked:
        raise HTTPException(status_code=403, detail="Post is locked.")

    depth = 0
    path = ""
    parent_id = None

    if req.parent_id:
        try:
            parent_uuid = uuid.UUID(req.parent_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent_id.")

        result = await db.execute(
            select(Comment).where(Comment.id == parent_uuid, Comment.post_id == post_id)
        )
        parent = result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found.")

        depth = parent.depth + 1
        if depth > 10:
            raise HTTPException(status_code=400, detail="Maximum nesting depth (10) exceeded.")
        parent_id = parent.id
        path = f"{parent.path}.{str(parent.id)}" if parent.path else str(parent.id)

    clean_body = sanitize_html(req.body)

    comment = Comment(
        post_id=post.id,
        author_id=actor.id,
        parent_id=parent_id,
        body=clean_body,
        depth=depth,
        path=path,
        posted_via_human_assist=req.posted_via_human_assist,
    )
    db.add(comment)

    # Update counters
    post.comment_count += 1
    post.last_activity_at = datetime.now(timezone.utc)
    actor.comment_count += 1

    await db.commit()
    await db.refresh(comment)

    return await _enrich_comment(comment, db)


@router.patch("/comments/{comment_id}", response_model=CommentPublic)
async def update_comment(
    comment_id: uuid.UUID,
    req: CommentUpdate,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Update a comment (author only)."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != actor.id:
        raise HTTPException(status_code=403, detail="Not authorized.")

    comment.body = req.body
    await db.commit()
    await db.refresh(comment)
    return await _enrich_comment(comment, db)


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: uuid.UUID,
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete a comment."""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")
    if comment.author_id != actor.id and actor.role not in [
        ActorRole.MODERATOR.value, ActorRole.ADMIN.value, ActorRole.FOUNDER.value
    ]:
        raise HTTPException(status_code=403, detail="Not authorized.")

    comment.is_removed = True

    # If a moderator (not the author) is removing, log the action
    if comment.author_id != actor.id:
        mod_action = ModerationAction(
            moderator_id=actor.id,
            target_type="comment",
            target_id=comment.id,
            action="remove",
            reason="Removed via delete endpoint",
        )
        db.add(mod_action)
        audit = AuditLog(
            actor_id=actor.id,
            action="mod_remove",
            resource_type="comment",
            resource_id=comment.id,
        )
        db.add(audit)

    await db.commit()
    return {"status": "ok", "detail": "Comment removed."}


@router.post("/comments/{comment_id}/vote")
async def vote_on_comment(
    comment_id: uuid.UUID,
    value: int = Query(ge=-1, le=1),
    actor: Actor = Depends(get_current_actor),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(rate_limit_vote),
):
    """Vote on a comment."""
    result = await db.execute(
        select(Comment).where(Comment.id == comment_id, Comment.is_removed == False)
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found.")

    if comment.author_id == actor.id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own comment.")

    # Check existing vote
    result = await db.execute(
        select(Vote).where(
            Vote.actor_id == actor.id,
            Vote.target_type == "comment",
            Vote.target_id == comment.id,
        )
    )
    existing_vote = result.scalar_one_or_none()

    # Calculate weight
    from app.api.v1.routes.posts import _calculate_vote_weight
    weight = _calculate_vote_weight(actor.trust_score)

    if value == 0:
        if existing_vote:
            comment.vote_score -= existing_vote.value
            comment.weighted_score -= existing_vote.value * existing_vote.weight
            await db.delete(existing_vote)
    elif existing_vote:
        comment.vote_score -= existing_vote.value
        comment.weighted_score -= existing_vote.value * existing_vote.weight
        existing_vote.value = value
        existing_vote.weight = weight
        comment.vote_score += value
        comment.weighted_score += value * weight
    else:
        new_vote = Vote(
            actor_id=actor.id,
            target_type="comment",
            target_id=comment.id,
            value=value,
            weight=weight,
        )
        db.add(new_vote)
        comment.vote_score += value
        comment.weighted_score += value * weight

    await db.commit()
    return {"status": "ok", "vote_score": comment.vote_score, "viewer_vote": value if value != 0 else None}
