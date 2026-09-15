"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Plus, 
  Home, 
  Film, 
  UserCheck, 
  Settings, 
  LogOut 
} from "lucide-react";
import { useUserStore } from "@/lib/stores/userStore";
import Logo from "@/components/shared/Logo";

const primaryNav = [
  { name: "Home", href: "/dashboard", icon: Home },
  { name: "Projects", href: "/projects", icon: Film },
  { name: "Characters", href: "/characters", icon: UserCheck },
];

export default function Sidebar() {
  const pathname = usePathname();
  const logout = useUserStore((state) => state.logout);

  return (
    <aside className="w-56 border-r border-[#292A29] bg-[#151616] flex flex-col justify-between hidden md:flex min-h-screen sticky top-0 select-none z-20">
      <div>
        {/* Brand Header */}
        <div className="h-14 px-4 border-b border-[#292A29] flex items-center justify-between">
          <Logo href="/dashboard" size="md" />
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-[#1B1C1C] border border-[#292A29] text-[#77746E]">
            v7.3
          </span>
        </div>

        {/* Primary Action: New Video */}
        <div className="p-3 pb-2">
          <Link
            href="/projects/new"
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-md bg-[#E76536] hover:bg-[#F07847] text-white font-semibold text-xs transition-colors shadow-sm"
          >
            <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
            <span>New Video</span>
          </Link>
        </div>

        {/* Main Navigation Links */}
        <nav className="px-3 py-1 space-y-0.5">
          {primaryNav.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-[#1B1C1C] text-[#F5F1E8] border border-[#383938] font-semibold"
                    : "text-[#A9A49B] hover:text-[#F5F1E8] hover:bg-[#1B1C1C]/60"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#E76536]" : "text-[#77746E]"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}

          <div className="pt-3 pb-1">
            <div className="border-t border-[#292A29]" />
          </div>

          <Link
            href="/settings"
            className={`flex items-center gap-2.5 px-3 py-2 rounded-md text-xs font-medium transition-colors ${
              pathname === "/settings"
                ? "bg-[#1B1C1C] text-[#F5F1E8] border border-[#383938] font-semibold"
                : "text-[#A9A49B] hover:text-[#F5F1E8] hover:bg-[#1B1C1C]/60"
            }`}
          >
            <Settings className={`w-4 h-4 ${pathname === "/settings" ? "text-[#E76536]" : "text-[#77746E]"}`} />
            <span>Settings</span>
          </Link>
        </nav>
      </div>

      {/* User / Sign Out Footer */}
      <div className="p-3 border-t border-[#292A29]">
        <button
          onClick={logout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-[#77746E] hover:text-[#C95C5C] hover:bg-[#C95C5C]/10 text-xs font-medium transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}