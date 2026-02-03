"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { CommunityPublic } from "@/lib/types";
import FeedList from "@/components/feed/FeedList";

export default function CommunityPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [community, setCommunity] = useState<CommunityPublic | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<CommunityPublic>(`/communities/${slug}`);
        setCommunity(data);
      } catch {
        setCommunity(null);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [slug]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-8">
        <div className="h-24 animate-pulse rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)]" />
      </div>
    );
  }

  if (!community) {
    return (
      <div className="max-w-4xl mx-auto py-8 text-center text-[var(--cg-text-muted)]">
        Community not found.
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-4">
      <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-6 mb-6">
        <h1 className="text-2xl font-bold">c/{community.slug}</h1>
        <p className="text-sm text-[var(--cg-text-muted)] mt-1">{community.name}</p>
        {community.description && (
          <p className="mt-2 text-sm text-[var(--cg-text-muted)]">{community.description}</p>
        )}
        <div className="mt-3 flex gap-4 text-xs text-[var(--cg-text-muted)]">
          <span>{community.member_count} members</span>
          <span>{community.post_count} posts</span>
        </div>
      </div>
      <FeedList community={slug} />
    </div>
  );
}
