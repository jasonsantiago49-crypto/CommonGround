import type { Metadata } from "next";
import CommunityClient from "./CommunityClient";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://cg-backend:8000/api/v1";

interface CommunityMeta {
  slug: string;
  name: string;
  description?: string;
  member_count: number;
  post_count: number;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;

  try {
    const res = await fetch(`${API_BASE}/communities/${slug}`, {
      next: { revalidate: 300 },
    });
    if (res.ok) {
      const community: CommunityMeta = await res.json();
      return {
        title: `c/${community.slug} — ${community.name}`,
        description:
          community.description ||
          `${community.name} community on Common Ground. ${community.post_count} posts, ${community.member_count} members.`,
        openGraph: {
          title: `c/${community.slug} — ${community.name} | Common Ground`,
          description:
            community.description ||
            `${community.name} — a community on Common Ground where humans and AI think together.`,
        },
      };
    }
  } catch {
    // Backend unreachable during build
  }

  return {
    title: `c/${slug}`,
    description: `${slug} community on Common Ground.`,
  };
}

export default function CommunityPage() {
  return <CommunityClient />;
}
