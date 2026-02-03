"use client";

import { create } from "zustand";
import { api } from "./api";

interface Actor {
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
}

interface AuthState {
  actor: Actor | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    email: string;
    password: string;
    handle: string;
    display_name: string;
  }) => Promise<void>;
  logout: () => void;
  loadUser: () => Promise<void>;
}

export const useAuth = create<AuthState>((set, get) => ({
  actor: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const res = await api.post<{
      access_token: string;
      actor_id: string;
      handle: string;
      actor_type: string;
    }>("/auth/login", { email, password });
    api.setToken(res.access_token);
    await get().loadUser();
  },

  register: async (data) => {
    const res = await api.post<{
      access_token: string;
      actor_id: string;
      handle: string;
      actor_type: string;
    }>("/auth/register", data);
    api.setToken(res.access_token);
    await get().loadUser();
  },

  logout: () => {
    api.setToken(null);
    set({ actor: null, isAuthenticated: false });
  },

  loadUser: async () => {
    const token = api.getToken();
    if (!token) {
      set({ isLoading: false, isAuthenticated: false, actor: null });
      return;
    }
    try {
      const actor = await api.get<Actor>("/actors/me", { requireAuth: true });
      set({ actor, isAuthenticated: true, isLoading: false });
    } catch {
      api.setToken(null);
      set({ actor: null, isAuthenticated: false, isLoading: false });
    }
  },
}));
