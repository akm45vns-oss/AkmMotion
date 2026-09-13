"use client";

import { useEditorStore } from "@/lib/stores/editorStore";
import { ArrowLeft, Play, Download, Sparkles, Wand2 } from "lucide-react";
import Link from "next/link";

interface ToolBarProps {
  onRenderClick: () => void;
}

export default function ToolBar({ onRenderClick }: ToolBarProps) {
  const { project, isPlaying, setIsPlaying } = useEditorStore();

  return (
    <header className="h-16 border-b border-gray-800 bg-[#0D1322] px-6 flex items-center justify-between">
      <div className="flex items-center gap-4">
        <Link
          href="/dashboard"
          className="p-2 rounded-xl bg-gray-800/50 hover:bg-gray-800 text-gray-300 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-base font-bold text-white flex items-center gap-2">
            {project?.title || "Untitled Video"}
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-medium">
              1080 x 1920
            </span>
          </h1>
          <p className="text-xs text-gray-400">AI Vertical Short Studio</p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          className="px-4 py-2 rounded-xl bg-gray-800 hover:bg-gray-700 text-white text-xs font-semibold flex items-center gap-2 transition-all"
        >
          <Play className={`w-3.5 h-3.5 ${isPlaying ? "fill-white" : ""}`} />
          {isPlaying ? "Pause Preview" : "Play Timeline"}
        </button>

        <button
          onClick={onRenderClick}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-90 text-white text-xs font-bold shadow-lg shadow-indigo-500/25 flex items-center gap-2 transition-all"
        >
          <Wand2 className="w-4 h-4" />
          Render Final Video
        </button>
      </div>
    </header>
  );
}