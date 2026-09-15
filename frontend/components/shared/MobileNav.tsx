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
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-[#151616]/98 backdrop-blur-md border-t border-[#292A29] px-2 py-1 safe-bottom shadow-2xl"
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
                className="flex flex-col items-center justify-center -mt-3.5 touch-target group"
                aria-label="Create New Video Project"
              >
                <div className="w-11 h-11 rounded-xl bg-[#E76536] hover:bg-[#F07847] text-white flex items-center justify-center shadow-md shadow-[#E76536]/25 transition-transform active:scale-95">
                  <Icon className="w-5 h-5 stroke-[2.5]" />
                </div>
                <span className="text-[10px] font-semibold text-[#A9A49B] mt-1">Create</span>
              </Link>
            );
          }

          return (
            <Link
              key={item.label}
              href={item.href}
              className={`flex flex-col items-center justify-center py-1.5 px-3 min-h-[48px] rounded-lg transition-colors ${
                isActive
                  ? "text-[#E76536] font-semibold"
                  : "text-[#77746E] hover:text-[#F5F1E8]"
              }`}
            >
              <Icon className="w-4 h-4 mb-0.5" />
              <span className="text-[10px]">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
