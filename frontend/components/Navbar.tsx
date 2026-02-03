"use client";

import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const { actor, isAuthenticated, isLoading, logout } = useAuth();

  return (
    <header className="sticky top-0 z-50 border-b border-[var(--cg-border)] bg-[var(--cg-surface)]/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4">
        <a href="/" className="flex items-center gap-2 font-semibold text-lg">
          <span className="text-[var(--cg-accent)]">Common</span>
          <span>Ground</span>
        </a>
        <nav className="flex items-center gap-4 text-sm text-[var(--cg-text-muted)]">
          <a href="/c" className="hover:text-[var(--cg-text)] transition-colors">
            Communities
          </a>
          <a href="/manifesto" className="hover:text-[var(--cg-text)] transition-colors">
            Manifesto
          </a>
          <a href="/rules" className="hover:text-[var(--cg-text)] transition-colors">
            Rules
          </a>
          <a href="/moderation" className="hover:text-[var(--cg-text)] transition-colors">
            Mod Log
          </a>
          {isLoading ? (
            <span className="h-8 w-16 animate-pulse rounded-md bg-[var(--cg-border)]" />
          ) : isAuthenticated && actor ? (
            <div className="flex items-center gap-3">
              <a
                href={`/u/${actor.handle}`}
                className="hover:text-[var(--cg-text)] transition-colors font-medium"
              >
                {actor.display_name}
              </a>
              <button
                onClick={logout}
                className="text-xs hover:text-[var(--cg-downvote)] transition-colors"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <a
              href="/login"
              className="rounded-md bg-[var(--cg-accent)] px-3 py-1.5 text-white hover:bg-[var(--cg-accent-hover)] transition-colors"
            >
              Sign In
            </a>
          )}
        </nav>
      </div>
    </header>
  );
}
