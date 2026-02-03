"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { CommunityPublic } from "@/lib/types";

export default function CommunitiesPage() {
  const [communities, setCommunities] = useState<CommunityPublic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.get<CommunityPublic[]>("/communities");
        setCommunities(data);
      } catch {
        setCommunities([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Communities</h1>
      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)]"
            />
          ))}
        </div>
      ) : communities.length === 0 ? (
        <p className="text-[var(--cg-text-muted)]">No communities yet.</p>
      ) : (
        <div className="space-y-3">
          {communities.map((c) => (
            <a
              key={c.id}
              href={`/c/${c.slug}`}
              className="block rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-4 hover:border-[var(--cg-accent)]/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-lg">c/{c.slug}</h3>
                  <p className="text-sm text-[var(--cg-text-muted)]">{c.name}</p>
                </div>
                <div className="text-right text-xs text-[var(--cg-text-muted)]">
                  <div>{c.member_count} members</div>
                  <div>{c.post_count} posts</div>
                </div>
              </div>
              {c.description && (
                <p className="mt-2 text-sm text-[var(--cg-text-muted)]">{c.description}</p>
              )}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
