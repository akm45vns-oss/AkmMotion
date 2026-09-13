"use client";

import { useState, useEffect } from "react";
import { Sparkles, CheckCircle2, AlertCircle, Zap, ShieldCheck, FileText, Globe, Clock, Layers } from "lucide-react";
import { API_BASE_URL } from "@/lib/api/client";

interface HealthScoreCardProps {
  scriptText: string;
  language: string;
  onAutoImproveClick: () => void;
}

export default function HealthScoreCard({ scriptText, language, onAutoImproveClick }: HealthScoreCardProps) {
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    const analyze = async () => {
      if (!scriptText || scriptText.trim().length === 0) {
        setReport(null);
        return;
      }

      setLoading(true);
      try {
        const res = await fetch(`${API_BASE_URL}/ai/analyze-script`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ script: scriptText, language }),
        });

        if (res.ok) {
          const data = await res.json();
          if (isMounted) setReport(data);
        }
      } catch (err) {
        console.error("Failed to analyze script health:", err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    const timer = setTimeout(analyze, 400);
    return () => {
      isMounted = false;
      clearTimeout(timer);
    };
  }, [scriptText, language]);

  if (!scriptText || scriptText.trim().length === 0) {
    return (
      <div className="p-4 rounded-2xl bg-[#0D1322] border border-gray-800 text-center text-xs text-gray-400">
        Enter a script to analyze AI Script Health Score.
      </div>
    );
  }

  const score = report?.overall_score || 85;
  const sub = report?.sub_scores || { grammar: 90, readability: 88, narration: 92, engagement: 85, scene_balance: 90 };
  const metrics = report?.metrics || { word_count: 0, estimated_duration: "0s", estimated_scenes: 0, language: "English", accent: "Indian English Accent", estimated_render_time: "1-2 min" };
  const suggestions = report?.suggestions || [];

  return (
    <div className="rounded-3xl bg-[#0D1322] border border-gray-800 p-5 space-y-5 shadow-xl">
      {/* Header Badge */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">AI Script Health Score</h3>
            <p className="text-[11px] text-gray-400">Quality, Grammar & Video Flow Engine</p>
          </div>
        </div>

        {/* Circular Overall Score */}
        <div className="flex items-center gap-2 bg-[#090D16] px-3 py-1.5 rounded-2xl border border-gray-800">
          <span className="text-xl font-extrabold text-amber-400">{score}</span>
          <span className="text-xs text-gray-500 font-medium">/ 100</span>
        </div>
      </div>

      {/* 5 Sub-Dimension Progress Bars */}
      <div className="space-y-2.5 bg-[#090D16] p-4 rounded-2xl border border-gray-800/80">
        <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider mb-2">Quality Dimensions</div>

        {[
          { label: "Grammar & Spelling", val: sub.grammar, color: "from-emerald-500 to-teal-400" },
          { label: "Readability & Flow", val: sub.readability, color: "from-blue-500 to-indigo-400" },
          { label: "Narration Quality", val: sub.narration, color: "from-purple-500 to-pink-400" },
          { label: "Engagement & Hook", val: sub.engagement, color: "from-amber-500 to-orange-400" },
          { label: "Scene Balance", val: sub.scene_balance, color: "from-cyan-500 to-blue-400" },
        ].map((item, idx) => (
          <div key={idx} className="space-y-1">
            <div className="flex justify-between text-[11px] font-semibold">
              <span className="text-gray-300">{item.label}</span>
              <span className="text-white">{item.val}%</span>
            </div>
            <div className="w-full h-1.5 bg-gray-900 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r ${item.color} transition-all duration-500`}
                style={{ width: `${item.val}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Script Metadata Metrics Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-3 rounded-xl bg-[#090D16] border border-gray-800/60 flex items-center gap-2">
          <Clock className="w-4 h-4 text-indigo-400 flex-shrink-0" />
          <div>
            <div className="text-[10px] text-gray-500 uppercase">Est. Duration</div>
            <div className="font-bold text-white">{metrics.estimated_duration}</div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#090D16] border border-gray-800/60 flex items-center gap-2">
          <Layers className="w-4 h-4 text-purple-400 flex-shrink-0" />
          <div>
            <div className="text-[10px] text-gray-500 uppercase">Est. Scenes</div>
            <div className="font-bold text-white">{metrics.estimated_scenes} Scenes</div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#090D16] border border-gray-800/60 flex items-center gap-2">
          <Globe className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <div>
            <div className="text-[10px] text-gray-500 uppercase">Language</div>
            <div className="font-bold text-white truncate max-w-[100px]">{metrics.language}</div>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-[#090D16] border border-gray-800/60 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <div>
            <div className="text-[10px] text-gray-500 uppercase">Voice Accent</div>
            <div className="font-bold text-white truncate max-w-[100px]">{metrics.accent}</div>
          </div>
        </div>
      </div>

      {/* AI Improvement Suggestions */}
      {suggestions.length > 0 && (
        <div className="space-y-2">
          <div className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">AI Suggestions</div>
          <div className="space-y-1.5">
            {suggestions.map((sug: string, i: number) => (
              <div key={i} className="text-xs text-gray-300 p-2.5 rounded-xl bg-[#090D16] border border-gray-800/50 flex items-start gap-2">
                <span className="leading-tight">{sug}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* One-Click Auto Improve Button */}
      <button
        type="button"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          onAutoImproveClick();
        }}
        className="w-full py-3.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-xs shadow-xl shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 group"
      >
        <Sparkles className="w-4 h-4 text-yellow-300 group-hover:rotate-12 transition-transform" />
        <span>✨ Auto Improve Script (One-Click)</span>
      </button>
    </div>
  );
}