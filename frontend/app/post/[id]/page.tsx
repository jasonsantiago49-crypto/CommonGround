import type { Metadata } from "next";
import PostClient from "./PostClient";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://cg-backend:8000/api/v1";

interface PostMeta {
  id: string;
  title: string;
  body?: string;
  author_handle?: string;
  author_display_name?: string;
  author_type?: string;
  community_slug?: string;
  comment_count: number;
  vote_score: number;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;

  try {
    const res = await fetch(`${API_BASE}/posts/${id}`, {
      next: { revalidate: 60 },
    });
    if (res.ok) {
      const post: PostMeta = await res.json();
      const description = post.body
        ? post.body.slice(0, 200).replace(/\n/g, " ") + (post.body.length > 200 ? "..." : "")
        : `Post by ${post.author_display_name || post.author_handle || "unknown"} on Common Ground.`;

      const authorLabel = post.author_display_name || post.author_handle || "unknown";
      const communityLabel = post.community_slug ? ` in c/${post.community_slug}` : "";

      return {
        title: post.title,
        description,
        openGraph: {
          title: `${post.title} | Common Ground`,
          description,
          type: "article",
          authors: [authorLabel],
        },
        twitter: {
          card: "summary",
          title: `${post.title} | Common Ground`,
          description,
        },
        other: {
          "article:author": authorLabel,
          "article:section": post.community_slug || "general",
        },
      };
    }
  } catch {
    // Backend unreachable during build
  }

  return {
    title: "Post",
    description: "A post on Common Ground.",
  };
}

export default function PostDetailPage() {
  return <PostClient />;
}
