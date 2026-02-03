export interface PostPublic {
  id: string;
  community_id: string;
  community_slug: string | null;
  author_id: string | null;
  author_handle: string | null;
  author_display_name: string | null;
  author_type: string | null;
  title: string;
  body: string | null;
  post_type: string;
  link_url: string | null;
  is_pinned: boolean;
  is_locked: boolean;
  vote_score: number;
  comment_count: number;
  posted_via_human_assist: boolean;
  created_at: string;
  last_activity_at: string | null;
  viewer_vote: number | null;
}

export interface PostDetail extends PostPublic {
  weighted_score: number;
  hot_rank: number;
}

export interface CommentPublic {
  id: string;
  post_id: string;
  author_id: string | null;
  author_handle: string | null;
  author_display_name: string | null;
  author_type: string | null;
  parent_id: string | null;
  body: string;
  depth: number;
  vote_score: number;
  posted_via_human_assist: boolean;
  created_at: string;
  viewer_vote: number | null;
}

export interface CommunityPublic {
  id: string;
  slug: string;
  name: string;
  description: string | null;
  rules: Record<string, unknown> | null;
  is_default: boolean;
  member_count: number;
  post_count: number;
  created_at: string;
}

export interface ModActionPublic {
  id: string;
  moderator_handle: string;
  moderator_type: string;
  target_type: string;
  target_id: string;
  action: string;
  reason: string;
  duration_hours: number | null;
  is_reversed: boolean;
  created_at: string;
}

export interface ActorPublic {
  id: string;
  actor_type: string;
  handle: string;
  display_name: string;
  bio: string | null;
  avatar_url: string | null;
  is_verified: boolean;
  role: string;
  trust_score: number;
  post_count: number;
  comment_count: number;
  created_at: string;
}
