const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

interface FetchOptions extends RequestInit {
  requireAuth?: boolean;
}

class ApiClient {
  private accessToken: string | null = null;

  setToken(token: string | null) {
    this.accessToken = token;
    if (token) {
      if (typeof window !== "undefined") {
        localStorage.setItem("cg_token", token);
      }
    } else {
      if (typeof window !== "undefined") {
        localStorage.removeItem("cg_token");
      }
    }
  }

  getToken(): string | null {
    if (this.accessToken) return this.accessToken;
    if (typeof window !== "undefined") {
      return localStorage.getItem("cg_token");
    }
    return null;
  }

  async fetch<T = unknown>(path: string, options: FetchOptions = {}): Promise<T> {
    const { requireAuth = false, headers: customHeaders, ...rest } = options;

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(customHeaders as Record<string, string>),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    } else if (requireAuth) {
      throw new Error("Authentication required");
    }

    const res = await fetch(`${API_BASE}${path}`, {
      headers,
      ...rest,
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: res.statusText }));
      throw new ApiError(res.status, error.detail || "Request failed");
    }

    if (res.status === 204) return {} as T;
    return res.json();
  }

  async get<T = unknown>(path: string, options?: FetchOptions): Promise<T> {
    return this.fetch<T>(path, { method: "GET", ...options });
  }

  async post<T = unknown>(path: string, body?: unknown, options?: FetchOptions): Promise<T> {
    return this.fetch<T>(path, {
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
      ...options,
    });
  }

  async patch<T = unknown>(path: string, body: unknown, options?: FetchOptions): Promise<T> {
    return this.fetch<T>(path, {
      method: "PATCH",
      body: JSON.stringify(body),
      ...options,
    });
  }

  async del<T = unknown>(path: string, options?: FetchOptions): Promise<T> {
    return this.fetch<T>(path, { method: "DELETE", ...options });
  }
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export const api = new ApiClient();
