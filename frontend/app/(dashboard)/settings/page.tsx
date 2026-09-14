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
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-indigo-400" />
          Account & Studio Settings
        </h1>
        <p className="text-sm text-gray-400 mt-1">Manage your profile and default video export settings</p>
      </div>

      {saved && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>Settings saved successfully!</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* User Profile Card */}
        <div className="p-6 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-indigo-400" />
            Profile Information
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Full Name</label>
              <input
                type="text"
                disabled
                value={user?.full_name || "Creator"}
                className="w-full px-4 py-3 rounded-xl bg-[#090D16] border border-gray-800 text-white text-sm opacity-80 cursor-not-allowed"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-400 uppercase mb-2">Email Address</label>
              <input
                type="email"
                disabled
                value={user?.email || "user@example.com"}
                className="w-full px-4 py-3 rounded-xl bg-[#090D16] border border-gray-800 text-white text-sm opacity-80 cursor-not-allowed"
              />
            </div>
          </div>
        </div>

        {/* Studio Export Defaults */}
        <div className="p-6 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-4">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Video className="w-4 h-4 text-purple-400" />
            Video Export Defaults
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {["720p", "1080p"].map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => setQuality(q)}
                className={`p-4 rounded-xl border text-left transition-all ${
                  quality === q
                    ? "border-indigo-500 bg-indigo-600/10 ring-1 ring-indigo-500 text-white font-bold"
                    : "border-gray-800 bg-[#090D16] text-gray-400 hover:border-gray-700"
                }`}
              >
                <div className="text-sm font-semibold uppercase">{q} Resolution</div>
                <div className="text-xs text-gray-500 mt-1">
                  {q === "1080p" ? "Recommended for Shorts & Reels (Full HD)" : "Faster rendering (Standard HD)"}
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            className="px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/20 transition-all"
          >
            Save Settings
          </button>
        </div>
      </form>
    </div>
  );
}
