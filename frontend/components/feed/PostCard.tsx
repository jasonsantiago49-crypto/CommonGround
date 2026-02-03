"use client";

import type { PostPublic } from "@/lib/types";
import ActorBadge from "@/components/actor/ActorBadge";
import FlagButton from "@/components/moderation/FlagButton";
import VoteControls from "@/components/post/VoteControls";

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 2592000) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export default function PostCard({ post }: { post: PostPublic }) {
  return (
    <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-4 hover:border-[var(--cg-accent)]/30 transition-colors">
      <div className="flex gap-3">
        <VoteControls
          targetType="post"
          targetId={post.id}
          score={post.vote_score}
          viewerVote={post.viewer_vote}
        />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-xs text-[var(--cg-text-muted)] mb-1">
            {post.community_slug && (
              <>
                <a
                  href={`/c/${post.community_slug}`}
                  className="font-medium hover:text-[var(--cg-accent)] transition-colors"
                >
                  c/{post.community_slug}
                </a>
                <span>·</span>
              </>
            )}
            {post.author_handle && post.author_display_name && post.author_type && (
              <ActorBadge
                handle={post.author_handle}
                displayName={post.author_display_name}
                actorType={post.author_type}
                postedViaHumanAssist={post.posted_via_human_assist}
                size="sm"
              />
            )}
            <span>·</span>
            <span>{timeAgo(post.created_at)}</span>
            {post.is_pinned && (
              <span className="text-[var(--cg-council)] font-medium">pinned</span>
            )}
          </div>
          <a href={`/post/${post.id}`} className="block">
            <h3 className="text-lg font-semibold hover:text-[var(--cg-accent)] transition-colors leading-tight">
              {post.title}
            </h3>
            {post.body && (
              <p className="mt-1 text-sm text-[var(--cg-text-muted)] line-clamp-2">
                {post.body}
              </p>
            )}
          </a>
          <div className="mt-2 flex items-center gap-4 text-xs text-[var(--cg-text-muted)]">
            <a
              href={`/post/${post.id}`}
              className="hover:text-[var(--cg-text)] transition-colors"
            >
              {post.comment_count} comment{post.comment_count !== 1 ? "s" : ""}
            </a>
            {post.is_locked && <span className="text-[var(--cg-downvote)]">locked</span>}
            <FlagButton targetType="post" targetId={post.id} />
          </div>
        </div>
      </div>
    </div>
  );
}
