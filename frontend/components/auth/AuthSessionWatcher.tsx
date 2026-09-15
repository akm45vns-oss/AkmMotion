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
      if (document.hidden) {
        // Tab went to background
        sessionStorage.setItem("akm_tab_hidden_at", Date.now().toString());
      } else {
        const hiddenAt = sessionStorage.getItem("akm_tab_hidden_at");
        if (hiddenAt) {
          const elapsed = Date.now() - parseInt(hiddenAt, 10);
          if (elapsed > INACTIVITY_TIMEOUT_MS) {
            console.warn("[Security] Session expired while tab was in background.");
            logout();
            router.push("/login?reason=session_expired");
          }
          sessionStorage.removeItem("akm_tab_hidden_at");
        }
      }
    };

    // User activity listeners
    const activityEvents = ["mousemove", "mousedown", "keydown", "scroll", "touchstart"];
    activityEvents.forEach((ev) => {
      window.addEventListener(ev, resetInactivityTimer, { passive: true });
    });

    document.addEventListener("visibilitychange", handleVisibilityChange);

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
    };
  }, [isAuthenticated, token, logout, router]);

  return null;
}
