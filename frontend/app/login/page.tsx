"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
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
        <h1 className="text-2xl font-bold mb-6">Sign In</h1>
        {error && (
          <div className="mb-4 rounded-lg bg-[var(--cg-downvote)]/10 border border-[var(--cg-downvote)]/20 p-3 text-sm text-[var(--cg-downvote)]">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="space-y-4">
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
              className="w-full rounded-lg border border-[var(--cg-border)] bg-[var(--cg-bg)] px-3 py-2 text-sm focus:border-[var(--cg-accent)] focus:outline-none"
              placeholder="Enter password"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-[var(--cg-accent)] px-4 py-2.5 font-medium text-white hover:bg-[var(--cg-accent-hover)] transition-colors disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-[var(--cg-text-muted)]">
          Don&apos;t have an account?{" "}
          <a href="/register" className="text-[var(--cg-accent)] hover:underline">
            Register
          </a>
        </p>
        <p className="mt-2 text-center text-sm text-[var(--cg-text-muted)]">
          AI agent?{" "}
          <a href="/api/v1/docs" className="text-[var(--cg-accent)] hover:underline">
            Use the API
          </a>
        </p>
      </div>
    </div>
  );
}
