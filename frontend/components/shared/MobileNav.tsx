"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Film, Plus, UserCheck, Settings } from "lucide-react";

export default function MobileNav() {
  const pathname = usePathname();

  const navItems = [
    { label: "Home", href: "/dashboard", icon: LayoutDashboard },
    { label: "Projects", href: "/projects", icon: Film },
    { label: "Create", href: "/projects/new", icon: Plus, isPrimary: true },
    { label: "Characters", href: "/characters", icon: UserCheck },
    { label: "Settings", href: "/settings", icon: Settings },
  ];

  return (
    <nav
      aria-label="Mobile Bottom Navigation"
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#141517]/95 backdrop-blur-md border-t border-[#24272E] px-2 py-1 safe-bottom shadow-2xl"
    >
      <div className="flex items-center justify-around max-w-lg mx-auto">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;

          if (item.isPrimary) {
            return (
              <Link
                key={item.label}
                href={item.href}
                className="flex flex-col items-center justify-center -mt-4 touch-target group"
                aria-label="Create New Video Project"
              >
                <div className="w-12 h-12 rounded-2xl bg-[#E0693B] hover:bg-[#EB794D] text-white flex items-center justify-center shadow-lg shadow-[#E0693B]/25 transition-transform active:scale-95">
                  <Icon className="w-6 h-6 stroke-[2.5]" />
                </div>
                <span className="text-[10px] font-semibold text-neutral-300 mt-1">Create</span>
              </Link>
            );
          }

          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex flex-col items-center justify-center py-1.5 px-3 min-h-[48px] rounded-xl transition-colors ${
                isActive
                  ? "text-[#E0693B] font-semibold"
                  : "text-neutral-400 hover:text-neutral-200"
              }`}
            >
              <Icon className="w-5 h-5 mb-0.5" />
              <span className="text-[10px]">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
