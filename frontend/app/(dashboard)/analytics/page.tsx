"use client";

import { useState, useEffect } from "react";
import { BarChart3, Film, Clock, HardDrive, Coins, TrendingUp } from "lucide-react";
import { apiClient } from "@/lib/api/client";

export default function AnalyticsPage() {
  const [data, setData] = useState({
    projects_count: 0,
    videos_count: 0,
    total_render_seconds: 0,
    storage_used_mb: 0,
    credits_remaining: 100,
  });

  useEffect(() => {
    apiClient
      .get("/analytics")
      .then((res) => setData(res.data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-indigo-400" />
          Studio Analytics & Insights
        </h1>
        <p className="text-sm text-gray-400 mt-1">Track video production metrics, storage usage, and rendering time</p>
      </div>

      {/* Grid Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Total Projects</span>
            <Film className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{data.projects_count}</div>
          <div className="text-[11px] text-emerald-400 flex items-center gap-1">
            <TrendingUp className="w-3 h-3" />
            <span>Active Creation Mode</span>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Rendered Videos</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{data.videos_count}</div>
          <div className="text-[11px] text-gray-400">{data.total_render_seconds}s total render time</div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Storage Used</span>
            <HardDrive className="w-4 h-4 text-pink-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{data.storage_used_mb} MB</div>
          <div className="text-[11px] text-gray-400">Cloud Storage (Neon + R2)</div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-3">
          <div className="flex items-center justify-between text-xs text-gray-400">
            <span>Credits Remaining</span>
            <Coins className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-extrabold text-white">{data.credits_remaining}</div>
          <div className="text-[11px] text-amber-400 font-semibold">100 Bonus Credits Active</div>
        </div>
      </div>

      {/* Production Activity Chart Placeholder */}
      <div className="p-6 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-4">
        <h2 className="text-sm font-bold text-white uppercase tracking-wider">Weekly Video Production</h2>
        <div className="h-48 border border-dashed border-gray-800 rounded-xl flex items-end justify-between p-6 gap-3 bg-[#090D16]/40">
          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, idx) => (
            <div key={day} className="flex-1 flex flex-col items-center gap-2">
              <div
                className="w-full bg-gradient-to-t from-indigo-600 to-purple-500 rounded-t-lg transition-all"
                style={{ height: `${(idx + 1) * 15 + 20}%` }}
              />
              <span className="text-[11px] text-gray-400">{day}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
