"use client";

import { useState, useEffect } from "react";
import { X, Sparkles, Check, RotateCcw, ArrowRight, ShieldCheck } from "lucide-react";

interface AutoImproveModalProps {
  originalScript: string;
  onAccept: (improvedScript: string) => void;
  onClose: () => void;
}

export default function AutoImproveModal({ originalScript, onAccept, onClose }: AutoImproveModalProps) {
  const [improvedScript, setImprovedScript] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchImprovement = async () => {
      setLoading(true);
      try {
        const res = await fetch("http://localhost:8000/api/v1/ai/improve-script", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ script: originalScript }),
        });

        if (res.ok) {
          const data = await res.json();
          setImprovedScript(data.improved_script || originalScript);
        } else {
          setImprovedScript(originalScript);
        }
      } catch (err) {
        console.error("Failed to fetch script improvement:", err);
        setImprovedScript(originalScript);
      } finally {
        setLoading(false);
      }
    };

    fetchImprovement();
  }, [originalScript]);

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-3xl rounded-3xl bg-[#0D1322] border border-gray-800 shadow-2xl relative p-6 space-y-6">
        {/* Close Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
            <Sparkles className="w-6 h-6 text-yellow-300 animate-pulse" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">✨ AI Script Intelligence — Side-by-Side Optimization</h2>
            <p className="text-xs text-gray-400">
              Enhanced readability, grammar, hook power, and subtitle timing while preserving 100% original meaning.
            </p>
          </div>
        </div>

        {loading ? (
          <div className="h-64 flex flex-col items-center justify-center gap-3">
            <Sparkles className="w-8 h-8 text-indigo-400 animate-spin" />
            <p className="text-xs text-gray-400">Analyzing & Optimizing Script Structure...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Original Script */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-gray-400 px-1">
                <span>Original Script</span>
                <span className="text-[10px] text-gray-500">{originalScript.split(" ").length} words</span>
              </div>
              <div className="h-60 p-4 rounded-2xl bg-[#090D16] border border-gray-800 text-xs text-gray-300 overflow-y-auto leading-relaxed scrollbar-thin">
                {originalScript}
              </div>
            </div>

            {/* Improved AI Script */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-bold text-indigo-400 px-1">
                <span className="flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5" /> AI Improved Script
                </span>
                <span className="text-[10px] text-emerald-400 font-bold">Optimized</span>
              </div>
              <div className="h-60 p-4 rounded-2xl bg-[#090D16] border border-indigo-500/40 text-xs text-white overflow-y-auto leading-relaxed scrollbar-thin shadow-inner">
                {improvedScript}
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-2 border-t border-gray-800">
          <button
            type="button"
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reject / Keep Original</span>
          </button>

          <button
            type="button"
            onClick={() => onAccept(improvedScript)}
            disabled={loading}
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-xs shadow-xl shadow-emerald-600/20 flex items-center gap-2 transition-all disabled:opacity-50"
          >
            <Check className="w-4 h-4" />
            <span>Accept AI Improved Script</span>
          </button>
        </div>
      </div>
    </div>
  );
}