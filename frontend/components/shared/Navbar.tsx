"use client";

import { useUserStore } from "@/lib/stores/userStore";
import { User } from "lucide-react";
import Link from "next/link";

export default function Navbar() {
  const user = useUserStore((state) => state.user);

  return (
    <header className="h-14 border-b border-[#24272E] bg-[#141517]/90 backdrop-blur-md sticky top-0 z-40 px-4 md:px-6 flex items-center justify-between">
      {/* Mobile Brand Mark */}
      <div className="flex md:hidden items-center gap-2">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-[#E0693B] flex items-center justify-center font-bold text-white text-xs">
            A
          </div>
          <span className="text-xs font-bold text-[#F2F2F3] tracking-tight">AkmMotion</span>
        </Link>
      </div>

      {/* Desktop Workspace Label */}
      <div className="hidden md:flex items-center gap-2 text-xs text-neutral-400">
        <span className="w-2 h-2 rounded-full bg-[#2EB88A]" />
        <span>Video Studio Active</span>
      </div>

      {/* User Profile */}
      <div className="flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-[#1B1D21] border border-[#24272E] flex items-center justify-center text-[#E0693B] font-semibold text-xs">
          {user?.full_name ? user.full_name[0].toUpperCase() : <User className="w-3.5 h-3.5 text-neutral-400" />}
        </div>
        <div className="text-left">
          <div className="text-xs font-medium text-[#F2F2F3] leading-tight">
            {user?.full_name || "Creator"}
          </div>
          <div className="text-[10px] text-neutral-400 hidden sm:block">
            {user?.email || "Personal Workspace"}
          </div>
        </div>
      </div>
    </header>
  );
}
