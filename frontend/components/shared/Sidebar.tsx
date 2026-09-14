"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  FolderPlus, 
  Film, 
  UserCheck,
  Settings, 
  LogOut 
} from "lucide-react";
import { useUserStore } from "@/lib/stores/userStore";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "New Video", href: "/projects/new", icon: FolderPlus, highlight: true },
  { name: "Projects", href: "/projects", icon: Film },
  { name: "Character Studio", href: "/characters", icon: UserCheck },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const logout = useUserStore((state) => state.logout);

  return (
    <aside className="w-60 border-r border-[#24272E] bg-[#141517] flex flex-col justify-between hidden md:flex min-h-screen sticky top-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="h-16 px-5 border-b border-[#24272E] flex items-center gap-3">
          <div className="w-7 h-7 rounded-lg bg-[#E0693B] flex items-center justify-center font-bold text-white text-sm shadow-sm">
            A
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="text-sm font-bold text-[#F2F2F3] tracking-tight">
              AkmMotion
            </span>
            <span className="text-[10px] text-neutral-400 font-medium">Studio</span>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="p-3 space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            if (item.highlight) {
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl bg-[#E0693B] hover:bg-[#EB794D] text-white font-semibold text-xs transition-colors mb-3 shadow-sm"
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            }

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                  isActive
                    ? "bg-[#1B1D21] text-white border border-[#333742] font-semibold"
                    : "text-neutral-400 hover:text-[#F2F2F3] hover:bg-[#1B1D21]/60"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-[#E0693B]" : "text-neutral-400"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User / Sign Out Footer */}
      <div className="p-3 border-t border-[#24272E]">
        <button
          onClick={logout}
          className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-neutral-400 hover:text-[#E55353] hover:bg-[#E55353]/10 text-xs font-medium transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}