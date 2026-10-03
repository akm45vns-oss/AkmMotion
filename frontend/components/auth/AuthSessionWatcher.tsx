"use client";

import { useEffect, useRef } from "react";
import { useUserStore } from "@/lib/stores/userStore";
import { useRouter } from "next/navigation";

const INACTIVITY_TIMEOUT_MS = 3 * 60 * 1000; // 3 minutes

export default function AuthSessionWatcher() {
  const router = useRouter();
  const { isAuthenticated, logout, token } = useUserStore();
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Only monitor if the user is logged in with an authenticated account
    const hasActiveToken = Boolean(
      token && token !== "guest_studio_session_token" && token !== "guest_studio_token"
    );

    if (!isAuthenticated && !hasActiveToken) {
      return;
    }

    const resetInactivityTimer = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      timeoutRef.current = setTimeout(() => {
        console.warn("[Security] 3-minute inactivity reached. Automatically logging out.");
        logout();
        router.push("/login?reason=inactivity");
      }, INACTIVITY_TIMEOUT_MS);
    };

    // Tab visibility switch handler (defense against unattended session hijacking)
    const handleVisibilityChange = () => {
      if (document.hidden || document.visibilityState === "hidden") {
        console.warn("[Security] Tab switched away / hidden. Immediately terminating authenticated session.");
        logout();
        sessionStorage.clear();
        router.push("/login?reason=tab_hidden");
      }
    };

    // Cross-tab synchronization: If user logs out in another tab, log out here immediately
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === "akmmotion_jwt_token" && !e.newValue) {
        logout();
        router.push("/login?reason=logged_out_elsewhere");
      }
    };

    // User activity listeners
    const activityEvents = ["mousemove", "mousedown", "keydown", "scroll", "touchstart", "click"];
    activityEvents.forEach((ev) => {
      window.addEventListener(ev, resetInactivityTimer, { passive: true });
    });

    document.addEventListener("visibilitychange", handleVisibilityChange);
    window.addEventListener("pagehide", handleVisibilityChange);
    window.addEventListener("storage", handleStorageChange);

    // Initialize timer
    resetInactivityTimer();

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      activityEvents.forEach((ev) => {
        window.removeEventListener(ev, resetInactivityTimer);
      });
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      window.removeEventListener("pagehide", handleVisibilityChange);
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [isAuthenticated, token, logout, router]);

  return null;
}
