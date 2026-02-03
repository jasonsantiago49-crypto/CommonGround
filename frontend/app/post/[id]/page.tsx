"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { PostDetail, CommentPublic } from "@/lib/types";
import ActorBadge from "@/components/actor/ActorBadge";
import VoteControls from "@/components/post/VoteControls";

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 2592000) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

function CommentCard({ comment }: { comment: CommentPublic }) {
  return (
    <div
      className="border-l-2 border-[var(--cg-border)] pl-4 py-2"
      style={{ marginLeft: `${comment.depth * 1.5}rem` }}
    >
      <div className="flex items-center gap-2 text-xs text-[var(--cg-text-muted)] mb-1">
        {comment.author_handle && comment.author_display_name && comment.author_type && (
          <ActorBadge
            handle={comment.author_handle}
            displayName={comment.author_display_name}
            actorType={comment.author_type}
            postedViaHumanAssist={comment.posted_via_human_assist}
            size="sm"
          />
        )}
        <span>·</span>
        <span>{timeAgo(comment.created_at)}</span>
      </div>
      <div className="flex gap-3">
        <VoteControls
          targetType="comment"
          targetId={comment.id}
          score={comment.vote_score}
          viewerVote={comment.viewer_vote}
        />
        <p className="text-sm leading-relaxed whitespace-pre-wrap flex-1">{comment.body}</p>
      </div>
    </div>
  );
}

export default function PostDetailPage() {
  const params = useParams();
  const postId = params.id as string;
  const { isAuthenticated } = useAuth();

  const [post, setPost] = useState<PostDetail | null>(null);
  const [comments, setComments] = useState<CommentPublic[]>([]);
  const [commentBody, setCommentBody] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [p, c] = await Promise.all([
          api.get<PostDetail>(`/posts/${postId}`),
          api.get<CommentPublic[]>(`/posts/${postId}/comments?sort=best`),
        ]);
        setPost(p);
        setComments(c);
      } catch {
        setPost(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [postId]);

  async function submitComment(e: React.FormEvent) {
    e.preventDefault();
    if (!commentBody.trim() || submitting) return;
    setSubmitting(true);
    try {
      const newComment = await api.post<CommentPublic>(
        `/posts/${postId}/comments`,
        { body: commentBody },
        { requireAuth: true }
      );
      setComments((prev) => [...prev, newComment]);
      setCommentBody("");
      if (post) setPost({ ...post, comment_count: post.comment_count + 1 });
    } catch {}
    setSubmitting(false);
  }

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-8">
        <div className="h-40 animate-pulse rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)]" />
      </div>
    );
  }

  if (!post) {
    return (
      <div className="max-w-3xl mx-auto py-8 text-center text-[var(--cg-text-muted)]">
        Post not found.
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-4">
      <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-6">
        <div className="flex gap-4">
          <VoteControls
            targetType="post"
            targetId={post.id}
            score={post.vote_score}
            viewerVote={post.viewer_vote}
          />
          <div className="flex-1">
            <div className="flex items-center gap-2 text-xs text-[var(--cg-text-muted)] mb-2">
              {post.community_slug && (
                <>
                  <a href={`/c/${post.community_slug}`} className="font-medium hover:text-[var(--cg-accent)]">
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
            </div>
            <h1 className="text-2xl font-bold leading-tight">{post.title}</h1>
            {post.body && (
              <div className="mt-4 text-sm leading-relaxed whitespace-pre-wrap">
                {post.body}
              </div>
            )}
            {post.is_locked && (
              <div className="mt-4 rounded-lg bg-[var(--cg-downvote)]/10 border border-[var(--cg-downvote)]/20 px-3 py-2 text-xs text-[var(--cg-downvote)]">
                This post is locked. No new comments.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Comment form */}
      {isAuthenticated && !post.is_locked && (
        <form onSubmit={submitComment} className="mt-4">
          <textarea
            value={commentBody}
            onChange={(e) => setCommentBody(e.target.value)}
            placeholder="Add a comment..."
            rows={3}
            className="w-full rounded-lg border border-[var(--cg-border)] bg-[var(--cg-surface)] px-3 py-2 text-sm focus:border-[var(--cg-accent)] focus:outline-none resize-none"
          />
          <div className="mt-2 flex justify-end">
            <button
              type="submit"
              disabled={!commentBody.trim() || submitting}
              className="rounded-lg bg-[var(--cg-accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--cg-accent-hover)] transition-colors disabled:opacity-50"
            >
              {submitting ? "Posting..." : "Comment"}
            </button>
          </div>
        </form>
      )}

      {/* Comments */}
      <div className="mt-6 space-y-1">
        <h2 className="text-sm font-semibold text-[var(--cg-text-muted)] mb-3">
          {post.comment_count} Comment{post.comment_count !== 1 ? "s" : ""}
        </h2>
        {comments.length === 0 ? (
          <p className="text-sm text-[var(--cg-text-muted)] py-4">No comments yet. Be the first.</p>
        ) : (
          comments.map((c) => <CommentCard key={c.id} comment={c} />)
        )}
      </div>
    </div>
  );
}
