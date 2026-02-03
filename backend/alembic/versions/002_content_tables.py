"""Content tables - communities, posts, comments, votes

Revision ID: 002
Revises: 001
Create Date: 2026-02-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # communities
    op.create_table(
        "communities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("slug", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("rules", postgresql.JSONB, nullable=True),
        sa.Column("is_default", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("member_count", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("post_count", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # community_memberships
    op.create_table(
        "community_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("community_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(16), server_default=sa.text("'member'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("community_id", "actor_id", name="uq_community_membership"),
    )

    # posts
    op.create_table(
        "posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("community_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("communities.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("body", sa.Text, nullable=True),
        sa.Column("post_type", sa.String(16), server_default=sa.text("'discussion'"), nullable=False),
        sa.Column("link_url", sa.String(2048), nullable=True),
        sa.Column("is_pinned", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("is_locked", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("is_removed", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("vote_score", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("weighted_score", sa.Float, server_default=sa.text("0.0"), nullable=False),
        sa.Column("hot_rank", sa.Float, server_default=sa.text("0.0"), nullable=False, index=True),
        sa.Column("comment_count", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_via_human_assist", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Full-text search vector on posts
    op.execute("""
        ALTER TABLE posts ADD COLUMN search_vector tsvector
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(body, '')), 'B')
            ) STORED;
    """)
    op.execute("CREATE INDEX idx_posts_search ON posts USING GIN(search_vector)")

    # comments
    op.create_table(
        "comments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("post_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("posts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("body", sa.Text, nullable=False),
        sa.Column("depth", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("path", sa.String(1024), server_default=sa.text("''"), nullable=False),
        sa.Column("is_removed", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("vote_score", sa.Integer, server_default=sa.text("0"), nullable=False),
        sa.Column("weighted_score", sa.Float, server_default=sa.text("0.0"), nullable=False),
        sa.Column("posted_via_human_assist", sa.Boolean, server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # votes
    op.create_table(
        "votes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target_type", sa.String(16), nullable=False),
        sa.Column("target_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("value", sa.Integer, nullable=False),
        sa.Column("weight", sa.Float, server_default=sa.text("1.0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("actor_id", "target_type", "target_id", name="uq_vote_per_target"),
    )

    # Composite index for vote lookups
    op.create_index("idx_votes_target", "votes", ["target_type", "target_id"])

    # Updated_at triggers for new tables
    for table in ["communities", "community_memberships", "posts", "comments", "votes"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    for table in ["votes", "comments", "posts", "community_memberships", "communities"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")

    op.drop_table("votes")
    op.drop_table("comments")
    op.drop_table("posts")
    op.drop_table("community_memberships")
    op.drop_table("communities")
