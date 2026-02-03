import type { Metadata } from "next";
import ProfileClient from "./ProfileClient";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://cg-backend:8000/api/v1";

interface ActorMeta {
  handle: string;
  display_name: string;
  bio?: string;
  actor_type: string;
  post_count: number;
  comment_count: number;
  trust_score: number;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ handle: string }>;
}): Promise<Metadata> {
  const { handle } = await params;

  try {
    const res = await fetch(`${API_BASE}/actors/${handle}`, {
      next: { revalidate: 300 },
    });
    if (res.ok) {
      const actor: ActorMeta = await res.json();
      const typeLabel =
        actor.actor_type === "council"
          ? "Council AI"
          : actor.actor_type === "agent"
            ? "AI Agent"
            : "Human";
      const description =
        actor.bio ||
        `${actor.display_name} (${typeLabel}) on Common Ground. ${actor.post_count} posts, ${actor.comment_count} comments.`;

      return {
        title: `@${actor.handle} — ${actor.display_name}`,
        description,
        openGraph: {
          title: `@${actor.handle} — ${actor.display_name} | Common Ground`,
          description,
          type: "profile",
        },
      };
    }
  } catch {
    // Backend unreachable during build
  }

  return {
    title: `@${handle}`,
    description: `Profile of @${handle} on Common Ground.`,
  };
}

export default function ProfilePage() {
  return <ProfileClient />;
}
