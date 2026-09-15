export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-[#0D0E0E] text-[#F5F1E8] flex items-center justify-center p-4 selection:bg-[#E76536]/30 selection:text-[#F5F1E8]">
      {children}
    </div>
  );
}
