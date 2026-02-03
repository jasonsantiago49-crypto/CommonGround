"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const FLAG_REASONS = [
  { value: "spam", label: "Spam" },
  { value: "harassment", label: "Harassment" },
  { value: "misinformation", label: "Misinformation" },
  { value: "impersonation", label: "Impersonation" },
  { value: "crypto", label: "Crypto / financial promotion" },
  { value: "violence", label: "Violence advocacy" },
  { value: "other", label: "Other" },
];

interface FlagButtonProps {
  targetType: "post" | "comment";
  targetId: string;
}

export default function FlagButton({ targetType, targetId }: FlagButtonProps) {
  const { actor } = useAuth();
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!actor) return null;

  async function handleFlag(reason: string) {
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/flags", {
        target_type: targetType,
        target_id: targetId,
        reason,
      });
      setSubmitted(true);
      setTimeout(() => setOpen(false), 1500);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to flag";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <span className="text-xs text-[var(--cg-text-muted)]">Flagged</span>
    );
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="text-xs text-[var(--cg-text-muted)] hover:text-[var(--cg-downvote)] transition-colors"
        title="Flag this content"
      >
        flag
      </button>
      {open && (
        <div className="absolute right-0 top-6 z-50 w-56 rounded-lg border border-[var(--cg-border)] bg-[var(--cg-surface)] p-2 shadow-lg">
          <p className="px-2 py-1 text-xs font-medium text-[var(--cg-text-muted)]">
            Report reason:
          </p>
          {FLAG_REASONS.map((r) => (
            <button
              key={r.value}
              onClick={() => handleFlag(r.value)}
              disabled={submitting}
              className="block w-full rounded-md px-2 py-1.5 text-left text-sm hover:bg-[var(--cg-surface-hover)] transition-colors disabled:opacity-50"
            >
              {r.label}
            </button>
          ))}
          {error && (
            <p className="px-2 py-1 text-xs text-[var(--cg-downvote)]">{error}</p>
          )}
        </div>
      )}
    </div>
  );
}
