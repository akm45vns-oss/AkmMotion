"use client";

import { useUserStore } from "@/lib/stores/userStore";
import { User } from "lucide-react";
import Link from "next/link";

export default function Navbar() {
  const user = useUserStore((state) => state.user);

  return (
    <header className="h-14 border-b border-[#292A29] bg-[#151616]/95 backdrop-blur-md sticky top-0 z-40 px-4 md:px-6 flex items-center justify-between">
      {/* Mobile Brand Mark */}
      <div className="flex md:hidden items-center gap-2">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#E76536] flex items-center justify-center font-bold text-white text-xs shadow-sm">
            A
          </div>
          <span className="text-xs font-bold text-[#F5F1E8] tracking-tight">AkmMotion</span>
        </Link>
      </div>

      {/* Desktop Workspace Label */}
      <div className="hidden md:flex items-center gap-2 text-xs text-[#A9A49B]">
        <span className="w-1.5 h-1.5 rounded-full bg-[#4FAE7B]" />
        <span className="font-medium text-[#77746E]">Studio Workspace</span>
      </div>

      {/* User Profile */}
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-md bg-[#1B1C1C] border border-[#292A29] flex items-center justify-center text-[#E76536] font-semibold text-xs">
          {user?.full_name ? user.full_name[0].toUpperCase() : <User className="w-3.5 h-3.5 text-[#77746E]" />}
        </div>
        <div className="text-left">
          <div className="text-xs font-medium text-[#F5F1E8] leading-tight">
            {user?.full_name || "Creator"}
          </div>
          <div className="text-[10px] text-[#77746E] hidden sm:block">
            {user?.email || "Personal Workspace"}
          </div>
        </div>
      </div>
    </header>
  );
}
