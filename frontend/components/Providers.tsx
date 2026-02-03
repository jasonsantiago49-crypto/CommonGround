"use client";

import { useEffect } from "react";
import { useAuth } from "@/lib/auth";

export default function Providers({ children }: { children: React.ReactNode }) {
  const { loadUser } = useAuth();

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  return <>{children}</>;
}
