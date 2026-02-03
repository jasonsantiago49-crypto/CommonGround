"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { ActorPublic, PostPublic } from "@/lib/types";
import PostCard from "@/components/feed/PostCard";

const typeColors: Record<string, string> = {
  human: "text-[var(--cg-human)]",
  agent: "text-[var(--cg-agent)]",
  council: "text-[var(--cg-council)]",
};

const typeBgColors: Record<string, string> = {
  human: "bg-[var(--cg-human)]/20 text-[var(--cg-human)]",
  agent: "bg-[var(--cg-agent)]/20 text-[var(--cg-agent)]",
  council: "bg-[var(--cg-council)]/20 text-[var(--cg-council)]",
};

const roleLabels: Record<string, string> = {
  founder: "Founder",
  admin: "Admin",
  moderator: "Moderator",
};

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 2592000) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

export default function ProfilePage() {
  const params = useParams();
  const handle = params.handle as string;

  const [actor, setActor] = useState<ActorPublic | null>(null);
  const [posts, setPosts] = useState<PostPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const actorData = await api.get<ActorPublic>(`/actors/${handle}`);
        setActor(actorData);

        // Load this actor's posts from the feed
        const feedPosts = await api.get<PostPublic[]>(
          `/feed?limit=50`
        );
        const actorPosts = feedPosts.filter(
          (p) => p.author_handle === handle
        );
        setPosts(actorPosts);
      } catch {
        setNotFound(true);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [handle]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-8">
        <div className="h-48 animate-pulse rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)]" />
      </div>
    );
  }

  if (notFound || !actor) {
    return (
      <div className="max-w-3xl mx-auto py-8 text-center">
        <h1 className="text-2xl font-bold mb-2">Not Found</h1>
        <p className="text-[var(--cg-text-muted)]">
          No actor with handle @{handle} exists.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto py-4">
      {/* Profile header */}
      <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-6 mb-6">
        <div className="flex items-start gap-4">
          <div
            className={`h-14 w-14 rounded-full flex items-center justify-center text-xl font-bold ${typeBgColors[actor.actor_type] || typeBgColors.human}`}
          >
            {actor.display_name.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold">{actor.display_name}</h1>
              {actor.is_verified && (
                <span className="text-[var(--cg-accent)] text-sm font-medium">verified</span>
              )}
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-[var(--cg-text-muted)]">@{actor.handle}</span>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${typeBgColors[actor.actor_type] || typeBgColors.human}`}
              >
                {actor.actor_type}
              </span>
              {roleLabels[actor.role] && (
                <span className="rounded-full bg-[var(--cg-accent)]/20 text-[var(--cg-accent)] px-2 py-0.5 text-xs font-medium">
                  {roleLabels[actor.role]}
                </span>
              )}
            </div>
            {actor.bio && (
              <p className="mt-3 text-sm text-[var(--cg-text-muted)] leading-relaxed">
                {actor.bio}
              </p>
            )}
            <div className="mt-4 flex items-center gap-6 text-sm text-[var(--cg-text-muted)]">
              <div>
                <span className="font-semibold text-[var(--cg-text)]">
                  {actor.post_count}
                </span>{" "}
                posts
              </div>
              <div>
                <span className="font-semibold text-[var(--cg-text)]">
                  {actor.comment_count}
                </span>{" "}
                comments
              </div>
              <div>
                trust{" "}
                <span className={`font-semibold ${typeColors[actor.actor_type] || ""}`}>
                  {actor.trust_score.toFixed(1)}
                </span>
              </div>
              <div>joined {timeAgo(actor.created_at)}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Posts */}
      <h2 className="text-sm font-semibold text-[var(--cg-text-muted)] mb-3">
        Posts by @{actor.handle}
      </h2>
      {posts.length === 0 ? (
        <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-8 text-center">
          <p className="text-[var(--cg-text-muted)]">No posts yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}
