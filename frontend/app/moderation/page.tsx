"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ModActionPublic } from "@/lib/types";

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 2592000) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

const ACTION_LABELS: Record<string, { label: string; color: string }> = {
  remove: { label: "Removed", color: "text-[var(--cg-downvote)]" },
  restore: { label: "Restored", color: "text-[var(--cg-upvote)]" },
  warn: { label: "Warning issued", color: "text-yellow-500" },
  mute: { label: "Muted", color: "text-orange-500" },
  ban: { label: "Banned", color: "text-[var(--cg-downvote)]" },
  pin: { label: "Pinned", color: "text-[var(--cg-council)]" },
  unpin: { label: "Unpinned", color: "text-[var(--cg-text-muted)]" },
  lock: { label: "Locked", color: "text-orange-500" },
  unlock: { label: "Unlocked", color: "text-[var(--cg-upvote)]" },
};

export default function ModerationLogPage() {
  const [actions, setActions] = useState<ModActionPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const params = filter ? `?target_type=${filter}` : "";
        const data = await api.get<ModActionPublic[]>(`/moderation/log${params}`);
        setActions(data);
      } catch {
        setActions([]);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filter]);

  return (
    <div className="max-w-4xl mx-auto py-4">
      <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-6 mb-6">
        <h1 className="text-2xl font-bold">Moderation Log</h1>
        <p className="text-sm text-[var(--cg-text-muted)] mt-1">
          Every moderation action is public. Transparency is not optional.
        </p>
      </div>

      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-[var(--cg-text-muted)]">Filter:</span>
        {[
          { value: null, label: "All" },
          { value: "post", label: "Posts" },
          { value: "comment", label: "Comments" },
        ].map((opt) => (
          <button
            key={opt.label}
            onClick={() => { setFilter(opt.value); setLoading(true); }}
            className={`rounded-md px-3 py-1 text-sm font-medium transition-colors ${
              filter === opt.value
                ? "bg-[var(--cg-accent)] text-white"
                : "text-[var(--cg-text-muted)] hover:text-[var(--cg-text)] hover:bg-[var(--cg-surface-hover)]"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="h-20 animate-pulse rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)]"
            />
          ))}
        </div>
      ) : actions.length === 0 ? (
        <div className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-8 text-center">
          <p className="text-[var(--cg-text-muted)]">No moderation actions yet.</p>
          <p className="text-sm text-[var(--cg-text-muted)] mt-1">
            When moderators take action, it will appear here for everyone to see.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {actions.map((action) => {
            const meta = ACTION_LABELS[action.action] || {
              label: action.action,
              color: "text-[var(--cg-text-muted)]",
            };
            return (
              <div
                key={action.id}
                className="rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 text-sm">
                      <span className={`font-semibold ${meta.color}`}>
                        {meta.label}
                      </span>
                      <span className="text-[var(--cg-text-muted)]">·</span>
                      <span className="text-[var(--cg-text-muted)]">
                        {action.target_type}
                      </span>
                      <a
                        href={
                          action.target_type === "post"
                            ? `/post/${action.target_id}`
                            : `#${action.target_id}`
                        }
                        className="text-[var(--cg-accent)] hover:underline text-xs"
                      >
                        view
                      </a>
                      {action.is_reversed && (
                        <span className="rounded bg-yellow-500/20 px-1.5 py-0.5 text-xs text-yellow-500 font-medium">
                          reversed
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-sm">{action.reason}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-[var(--cg-text-muted)]">
                      <span>by @{action.moderator_handle}</span>
                      {action.duration_hours && (
                        <span>· {action.duration_hours}h duration</span>
                      )}
                      <span>· {timeAgo(action.created_at)}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
