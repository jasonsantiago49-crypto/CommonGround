"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PostPublic } from "@/lib/types";
import PostCard from "./PostCard";
import FeedSortBar from "./FeedSortBar";

interface FeedListProps {
  community?: string;
}

export default function FeedList({ community }: FeedListProps) {
  const [posts, setPosts] = useState<PostPublic[]>([]);
  const [sort, setSort] = useState("hot");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadFeed() {
      setLoading(true);
      try {
        const params = new URLSearchParams({ sort, limit: "25" });
        if (community) params.set("community", community);
        const data = await api.get<PostPublic[]>(`/feed?${params}`);
        setPosts(data);
      } catch {
        setPosts([]);
      } finally {
        setLoading(false);
      }
    }
    loadFeed();
  }, [sort, community]);

  return (
    <div className="space-y-4">
      <FeedSortBar sort={sort} onSortChange={setSort} />
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-28 animate-pulse rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)]"
            />
          ))}
        </div>
      ) : posts.length === 0 ? (
        <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-8 text-center text-[var(--cg-text-muted)]">
          <p className="text-lg font-medium">No posts yet</p>
          <p className="mt-1 text-sm">Be the first to start a conversation.</p>
        </div>
      ) : (
        posts.map((post) => <PostCard key={post.id} post={post} />)
      )}
    </div>
  );
}
