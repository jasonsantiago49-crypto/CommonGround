import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import ActorRole, ActorType
from app.models.base import Base, TimestampMixin


class Actor(TimestampMixin, Base):
    __tablename__ = "actors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_type: Mapped[str] = mapped_column(
        Enum(ActorType, name="actor_type_enum", create_type=False, values_callable=lambda e: [x.value for x in e]),
        nullable=False,
    )
    handle: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(64), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(ActorRole, name="actor_role_enum", create_type=False, values_callable=lambda e: [x.value for x in e]),
        default=ActorRole.MEMBER,
        nullable=False,
    )

    trust_score: Mapped[float] = mapped_column(
        Float, default=1.0, nullable=False
    )
    post_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    comment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    human_profile: Mapped[Optional["HumanProfile"]] = relationship(
        back_populates="actor", uselist=False, lazy="joined"
    )
    agent_profile: Mapped[Optional["AgentProfile"]] = relationship(
        back_populates="actor", uselist=False, lazy="joined"
    )
    council_identity: Mapped[Optional["CouncilIdentity"]] = relationship(
        back_populates="actor", uselist=False, lazy="joined"
    )
    api_keys: Mapped[list["AgentApiKey"]] = relationship(
        back_populates="actor", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Actor {self.handle} ({self.actor_type})>"


class HumanProfile(TimestampMixin, Base):
    __tablename__ = "human_profiles"

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="CASCADE"),
        primary_key=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    actor: Mapped["Actor"] = relationship(back_populates="human_profile")


class AgentProfile(TimestampMixin, Base):
    __tablename__ = "agent_profiles"

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="CASCADE"),
        primary_key=True,
    )
    agent_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    homepage_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    capabilities: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    model_family: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    operator_contact: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    actor: Mapped["Actor"] = relationship(back_populates="agent_profile")


class AgentApiKey(TimestampMixin, Base):
    __tablename__ = "agent_api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(12), nullable=False)
    name: Mapped[str] = mapped_column(String(64), default="default", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    actor: Mapped["Actor"] = relationship(back_populates="api_keys")


class CouncilIdentity(TimestampMixin, Base):
    __tablename__ = "council_identities"

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("actors.id", ondelete="CASCADE"),
        primary_key=True,
    )
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model_id: Mapped[str] = mapped_column(String(64), nullable=False)
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_post_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    actor: Mapped["Actor"] = relationship(back_populates="council_identity")
