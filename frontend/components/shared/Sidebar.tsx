"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  FolderPlus, 
  Film, 
  UserCheck,
  Settings, 
  BarChart3, 
  Sparkles,
  LogOut 
} from "lucide-react";
import { useUserStore } from "@/lib/stores/userStore";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "New Video", href: "/projects/new", icon: FolderPlus, highlight: true },
  { name: "Projects", href: "/projects", icon: Film },
  { name: "Character Studio", href: "/characters", icon: UserCheck },
  { name: "Analytics", href: "/analytics", icon: BarChart3 },
  { name: "Settings", href: "/settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const logout = useUserStore((state) => state.logout);

  return (
    <aside className="w-64 border-r border-gray-800/80 bg-[#090D16] flex flex-col justify-between hidden md:flex min-h-screen sticky top-0">
      <div>
        {/* Brand Header */}
        <div className="h-16 px-6 border-b border-gray-800/80 flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-500 flex items-center justify-center font-bold text-white shadow-md shadow-indigo-500/20">
            A
          </div>
          <span className="text-lg font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
            AkmMotion
          </span>
        </div>

        {/* Navigation Links */}
        <nav className="p-4 space-y-1.5">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;

            if (item.highlight) {
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center gap-3 px-4 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold text-sm shadow-lg shadow-indigo-600/20 hover:from-indigo-500 hover:to-purple-500 transition-all mb-4"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            }

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-2.5 rounded-xl font-medium text-sm transition-all ${
                  isActive
                    ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20 font-semibold"
                    : "text-gray-400 hover:text-white hover:bg-gray-800/50"
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User / Credits Footer */}
      <div className="p-4 border-t border-gray-800/80">
        <div className="p-3 rounded-xl bg-[#0D1322] border border-gray-800 mb-3">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1.5">
            <span>Free Credits</span>
            <span className="font-semibold text-indigo-400">100 / 100</span>
          </div>
          <div className="w-full h-1.5 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 w-full" />
          </div>
        </div>

        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/10 text-sm font-medium transition-all"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}