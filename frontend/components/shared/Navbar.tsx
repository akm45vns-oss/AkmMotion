"use client";

import { useUserStore } from "@/lib/stores/userStore";
import { User } from "lucide-react";

export default function Navbar() {
  const user = useUserStore((state) => state.user);

  return (
    <header className="h-16 border-b border-gray-800/80 bg-[#090D16]/80 backdrop-blur sticky top-0 z-40 px-6 flex items-center justify-end">
      {/* Right Controls */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-semibold text-xs">
            {user?.full_name ? user.full_name[0].toUpperCase() : <User className="w-4 h-4" />}
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-white">{user?.full_name || "Creator"}</div>
            <div className="text-[10px] text-gray-400">{user?.email || "Studio Account"}</div>
          </div>
        </div>
      </div>
    </header>
  );
}
