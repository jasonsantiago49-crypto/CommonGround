import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Post(TimestampMixin, Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    community_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("communities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    post_type: Mapped[str] = mapped_column(
        String(16), default="discussion", nullable=False
    )
    link_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)

    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_removed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    vote_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    hot_rank: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, index=True)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    last_activity_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Tag for council posts made via human assist
    posted_via_human_assist: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Post {self.id} '{self.title[:30]}'>"
