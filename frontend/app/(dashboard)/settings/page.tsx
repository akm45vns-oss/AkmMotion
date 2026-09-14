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
      <div className="border-b border-[#24272E] pb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-[#F2F2F3] tracking-tight">
          Account & Studio Settings
        </h1>
        <p className="text-xs sm:text-sm text-neutral-400 mt-1">
          Manage your account profile and default export quality settings
        </p>
      </div>

      {saved && (
        <div className="p-3.5 rounded-xl bg-[#2EB88A]/10 border border-[#2EB88A]/25 text-[#2EB88A] text-xs flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>Settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-5">
        {/* User Profile */}
        <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-3.5">
          <h2 className="text-xs font-bold text-neutral-300 uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-3.5 h-3.5 text-[#E0693B]" />
            <span>Profile Information</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <div>
              <label className="block text-[11px] font-semibold text-neutral-400 uppercase mb-1">Full Name</label>
              <input
                type="text"
                disabled
                value={user?.full_name || "Creator"}
                className="input-base text-xs opacity-75 cursor-not-allowed bg-[#0C0D0E]"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-neutral-400 uppercase mb-1">Email Address</label>
              <input
                type="email"
                disabled
                value={user?.email || "user@example.com"}
                className="input-base text-xs opacity-75 cursor-not-allowed bg-[#0C0D0E]"
              />
            </div>
          </div>
        </div>

        {/* Studio Export Defaults */}
        <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-3.5">
          <h2 className="text-xs font-bold text-neutral-300 uppercase tracking-wider flex items-center gap-2">
            <Video className="w-3.5 h-3.5 text-[#E0693B]" />
            <span>Default Video Resolution</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {["720p", "1080p"].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuality(q)}
                className={`p-3.5 rounded-xl border text-left transition-all ${
                  quality === q
                    ? "border-[#E0693B] bg-[#E0693B]/10 text-white font-semibold shadow-sm"
                    : "border-[#24272E] bg-[#1B1D21] text-neutral-400 hover:border-[#333742]"
                }`}
              >
                <div className="text-xs font-semibold uppercase text-[#F2F2F3]">{q} Resolution</div>
                <div className="text-[11px] text-neutral-400 mt-0.5">
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
