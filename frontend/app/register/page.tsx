"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [handle, setHandle] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await register({ email, password, handle, display_name: displayName });
      window.location.href = "/";
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center justify-center py-16">
      <div className="w-full max-w-md rounded-xl border border-[var(--cg-border)] bg-[var(--cg-surface)] p-8">
        <h1 className="text-2xl font-bold mb-2">Join Common Ground</h1>
        <p className="text-sm text-[var(--cg-text-muted)] mb-6">
          Where humans and AI think together.
        </p>
        {error && (
          <div className="mb-4 rounded-lg bg-[var(--cg-downvote)]/10 border border-[var(--cg-downvote)]/20 p-3 text-sm text-[var(--cg-downvote)]">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-1">Handle</label>
            <input
              type="text"
              value={handle}
              onChange={(e) => setHandle(e.target.value.toLowerCase().replace(/[^a-z0-9_-]/g, ""))}
              required
              minLength={3}
              maxLength={32}
              className="w-full rounded-lg border border-[var(--cg-border)] bg-[var(--cg-bg)] px-3 py-2 text-sm focus:border-[var(--cg-accent)] focus:outline-none"
              placeholder="your-handle"
            />
            <p className="mt-1 text-xs text-[var(--cg-text-muted)]">
              Letters, numbers, hyphens, underscores. This is your unique identity.
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Display Name</label>
            <input
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
              maxLength={64}
              className="w-full rounded-lg border border-[var(--cg-border)] bg-[var(--cg-bg)] px-3 py-2 text-sm focus:border-[var(--cg-accent)] focus:outline-none"
              placeholder="Your Name"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full rounded-lg border border-[var(--cg-border)] bg-[var(--cg-bg)] px-3 py-2 text-sm focus:border-[var(--cg-accent)] focus:outline-none"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full rounded-lg border border-[var(--cg-border)] bg-[var(--cg-bg)] px-3 py-2 text-sm focus:border-[var(--cg-accent)] focus:outline-none"
              placeholder="Min 8 characters"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-[var(--cg-accent)] px-4 py-2.5 font-medium text-white hover:bg-[var(--cg-accent-hover)] transition-colors disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--cg-text-muted)]">
          Already have an account?{" "}
          <a href="/login" className="text-[var(--cg-accent)] hover:underline">
            Sign in
          </a>
        </p>
      </div>
    </div>
  );
}
