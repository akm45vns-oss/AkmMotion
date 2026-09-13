"use client";

import { useUserStore } from "@/lib/stores/userStore";
import { User, Bell, Search } from "lucide-react";

export default function Navbar() {
  const user = useUserStore((state) => state.user);

  return (
    <header className="h-16 border-b border-gray-800/80 bg-[#090D16]/80 backdrop-blur sticky top-0 z-40 px-6 flex items-center justify-between">
      {/* Search Input */}
      <div className="relative w-72">
        <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-500" />
        <input
          type="text"
          placeholder="Search projects, scripts..."
          className="w-full pl-10 pr-4 py-2 rounded-xl bg-[#0D1322] border border-gray-800 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition-all"
        />
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-4">
        <button className="p-2 rounded-xl border border-gray-800 bg-[#0D1322] text-gray-400 hover:text-white transition-colors relative">
          <Bell className="w-4 h-4" />
          <span className="w-2 h-2 rounded-full bg-indigo-500 absolute top-2 right-2" />
        </button>

        <div className="flex items-center gap-3 pl-2 border-l border-gray-800">
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
