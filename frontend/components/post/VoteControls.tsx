"use client";

import { useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface VoteControlsProps {
  targetType: "post" | "comment";
  targetId: string;
  score: number;
  viewerVote: number | null;
}

export default function VoteControls({
  targetType,
  targetId,
  score: initialScore,
  viewerVote: initialVote,
}: VoteControlsProps) {
  const [score, setScore] = useState(initialScore);
  const [viewerVote, setViewerVote] = useState(initialVote);
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useAuth();

  async function vote(value: number) {
    if (!isAuthenticated || loading) return;

    const newValue = viewerVote === value ? 0 : value;
    const scoreDelta = newValue - (viewerVote || 0);

    // Optimistic update
    setScore((s) => s + scoreDelta);
    setViewerVote(newValue || null);
    setLoading(true);

    try {
      const endpoint =
        targetType === "post"
          ? `/posts/${targetId}/vote?value=${newValue}`
          : `/comments/${targetId}/vote?value=${newValue}`;
      const res = await api.post<{ vote_score: number; viewer_vote: number | null }>(
        endpoint,
        undefined,
        { requireAuth: true }
      );
      setScore(res.vote_score);
      setViewerVote(res.viewer_vote);
    } catch (e) {
      // Revert on error
      setScore((s) => s - scoreDelta);
      setViewerVote(initialVote);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col items-center gap-0.5 min-w-[2rem]">
      <button
        onClick={() => vote(1)}
        disabled={!isAuthenticated}
        className={`w-6 h-6 flex items-center justify-center rounded transition-colors ${
          viewerVote === 1
            ? "text-[var(--cg-upvote)] bg-[var(--cg-upvote)]/10"
            : "text-[var(--cg-text-muted)] hover:text-[var(--cg-upvote)] hover:bg-[var(--cg-upvote)]/5"
        }`}
        title="Upvote"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 4l-8 8h5v8h6v-8h5z" />
        </svg>
      </button>
      <span
        className={`text-xs font-semibold ${
          score > 0
            ? "text-[var(--cg-upvote)]"
            : score < 0
            ? "text-[var(--cg-downvote)]"
            : "text-[var(--cg-text-muted)]"
        }`}
      >
        {score}
      </span>
      <button
        onClick={() => vote(-1)}
        disabled={!isAuthenticated}
        className={`w-6 h-6 flex items-center justify-center rounded transition-colors ${
          viewerVote === -1
            ? "text-[var(--cg-downvote)] bg-[var(--cg-downvote)]/10"
            : "text-[var(--cg-text-muted)] hover:text-[var(--cg-downvote)] hover:bg-[var(--cg-downvote)]/5"
        }`}
        title="Downvote"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 20l8-8h-5V4H9v8H4z" />
        </svg>
      </button>
    </div>
  );
}
