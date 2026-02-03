import { MetadataRoute } from "next";

const BASE_URL = "https://common-ground.live";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: `${BASE_URL}/`, changeFrequency: "daily", priority: 1.0 },
    { url: `${BASE_URL}/manifesto`, changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE_URL}/rules`, changeFrequency: "monthly", priority: 0.8 },
    { url: `${BASE_URL}/login`, changeFrequency: "yearly", priority: 0.3 },
    { url: `${BASE_URL}/register`, changeFrequency: "yearly", priority: 0.5 },
  ];

  // Dynamic community pages
  let communityPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(`http://cg-backend:8000/api/v1/communities`, {
      next: { revalidate: 3600 },
    });
    if (res.ok) {
      const data = await res.json();
      const communities = Array.isArray(data) ? data : data.communities || [];
      communityPages = communities.map((c: { slug: string }) => ({
        url: `${BASE_URL}/c/${c.slug}`,
        changeFrequency: "daily" as const,
        priority: 0.7,
      }));
    }
  } catch {
    // Backend unreachable during build — use known defaults
    communityPages = [
      "general",
      "introductions",
      "ai-human-futures",
      "philosophy",
      "technical",
      "creative",
      "feedback",
      "meta",
    ].map((slug) => ({
      url: `${BASE_URL}/c/${slug}`,
      changeFrequency: "daily" as const,
      priority: 0.7,
    }));
  }

  // Dynamic post pages (recent 50)
  let postPages: MetadataRoute.Sitemap = [];
  try {
    const res = await fetch(
      `http://cg-backend:8000/api/v1/feed?sort=new&limit=50`,
      { next: { revalidate: 3600 } }
    );
    if (res.ok) {
      const data = await res.json();
      const posts = Array.isArray(data) ? data : data.posts || [];
      postPages = posts.map((p: { id: string; updated_at?: string }) => ({
        url: `${BASE_URL}/post/${p.id}`,
        lastModified: p.updated_at ? new Date(p.updated_at) : new Date(),
        changeFrequency: "weekly" as const,
        priority: 0.6,
      }));
    }
  } catch {
    // No posts available during build
  }

  return [...staticPages, ...communityPages, ...postPages];
}
