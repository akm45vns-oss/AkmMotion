"use client";

import { useState } from "react";
import { Settings, Video, ShieldCheck, Check } from "lucide-react";
import { useUserStore } from "@/lib/stores/userStore";

export default function SettingsPage() {
  const user = useUserStore((state) => state.user);

  const [quality, setQuality] = useState("1080p");
  const [saved, setSaved] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      <div className="border-b border-[#292A29] pb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-[#F5F1E8] tracking-tight font-display">
          Account & Studio Settings
        </h1>
        <p className="text-xs sm:text-sm text-[#A9A49B] mt-1">
          Manage your account profile and default export quality settings
        </p>
      </div>

      {saved && (
        <div className="p-3.5 rounded-lg bg-[#4FAE7B]/10 border border-[#4FAE7B]/25 text-[#4FAE7B] text-xs flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>Settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-5">
        {/* User Profile */}
        <div className="p-5 rounded-lg bg-[#151616] border border-[#292A29] space-y-3.5">
          <h2 className="text-xs font-bold text-[#F5F1E8] uppercase tracking-wider flex items-center gap-2 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-[#E76536]" />
            <span>Profile Information</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Full Name</label>
              <input
                type="text"
                disabled
                value={user?.full_name || "Creator"}
                className="input-base text-xs opacity-75 cursor-not-allowed bg-[#0D0E0E]"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Email Address</label>
              <input
                type="email"
                disabled
                value={user?.email || "user@example.com"}
                className="input-base text-xs opacity-75 cursor-not-allowed bg-[#0D0E0E]"
              />
            </div>
          </div>
        </div>

        {/* Studio Export Defaults */}
        <div className="p-5 rounded-lg bg-[#151616] border border-[#292A29] space-y-3.5">
          <h2 className="text-xs font-bold text-[#F5F1E8] uppercase tracking-wider flex items-center gap-2 font-mono">
            <Video className="w-3.5 h-3.5 text-[#E76536]" />
            <span>Default Video Resolution</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {["720p", "1080p"].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuality(q)}
                className={`p-3.5 rounded-lg border text-left transition-all touch-target ${
                  quality === q
                    ? "border-[#E76536] bg-[#E76536]/10 text-white font-semibold shadow-sm"
                    : "border-[#292A29] bg-[#1B1C1C] text-[#A9A49B] hover:border-[#383938]"
                }`}
              >
                <div className="text-xs font-semibold uppercase text-[#F5F1E8]">{q} Resolution</div>
                <div className="text-[11px] text-[#A9A49B] mt-0.5">
                  {q === "1080p" ? "Full HD vertical (Recommended for Shorts & Reels)" : "Standard HD (Faster render)"}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            className="btn-primary text-xs px-6 py-2.5 shadow-sm touch-target"
          >
            Save Settings
          </button>
        </div>
      </form>
    </div>
  );
}
