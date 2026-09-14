import Sidebar from "@/components/shared/Sidebar";
import Navbar from "@/components/shared/Navbar";
import MobileNav from "@/components/shared/MobileNav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0C0D0E] text-[#F2F2F3]">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        {/* pb-20 on mobile ensures bottom navigation never obscures content */}
        <main className="p-4 sm:p-6 md:p-8 flex-1 overflow-y-auto pb-24 md:pb-8">
          {children}
        </main>
        <MobileNav />
      </div>
    </div>
  );
}
