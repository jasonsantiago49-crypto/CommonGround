import uuid
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Comment(TimestampMixin, Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    path: Mapped[str] = mapped_column(
        String(1024), default="", nullable=False
    )

    is_removed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vote_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    posted_via_human_assist: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # Relationships
    post: Mapped["Post"] = relationship(back_populates="comments")
    replies: Mapped[list["Comment"]] = relationship(
        back_populates="parent", lazy="selectin"
    )
    parent: Mapped[Optional["Comment"]] = relationship(
        back_populates="replies", remote_side=[id]
    )

    def __repr__(self) -> str:
        return f"<Comment {self.id} on post {self.post_id}>"
