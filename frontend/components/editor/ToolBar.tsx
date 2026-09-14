"use client";

import { useEditorStore } from "@/lib/stores/editorStore";
import { ArrowLeft, Play, Pause, Sparkles, Wand2 } from "lucide-react";
import Link from "next/link";

interface ToolBarProps {
  onRenderClick: () => void;
  onGenerateClick?: () => void;
  isGenerating?: boolean;
}

export default function ToolBar({ onRenderClick, onGenerateClick, isGenerating = false }: ToolBarProps) {
  const { project, scenes, isPlaying, setIsPlaying } = useEditorStore();

  return (
    <header className="h-14 border-b border-[#24272E] bg-[#141517] px-3 sm:px-5 flex items-center justify-between z-30 select-none">
      {/* Left: Project Context & Breadcrumb */}
      <div className="flex items-center gap-2 sm:gap-3 min-w-0">
        <Link
          href="/dashboard"
          className="p-2 rounded-lg text-neutral-400 hover:text-white hover:bg-[#1B1D21] transition-colors touch-target"
          title="Back to Dashboard"
          aria-label="Back to Dashboard"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <h1 className="text-xs sm:text-sm font-bold text-[#F2F2F3] truncate max-w-[150px] sm:max-w-xs md:max-w-md">
              {project?.title || "Untitled Video"}
            </h1>
            <span className="hidden sm:inline-flex px-1.5 py-0.5 rounded bg-[#1B1D21] border border-[#24272E] text-[10px] font-mono text-neutral-300">
              1080×1920
            </span>
          </div>
          <p className="text-[10px] text-neutral-400 hidden sm:block">
            {scenes.length} Scene{scenes.length === 1 ? "" : "s"} · AI Vertical Short
          </p>
        </div>
      </div>

      {/* Right: Studio Playback & Actions */}
      <div className="flex items-center gap-2">
        {onGenerateClick && (
          <button
            onClick={onGenerateClick}
            disabled={isGenerating}
            className="hidden md:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#1B1D21] hover:bg-[#23262C] border border-[#24272E] text-neutral-300 text-xs font-medium transition-colors disabled:opacity-50"
            title="Regenerate all scenes from script"
          >
            <Sparkles className={`w-3.5 h-3.5 text-[#E0693B] ${isGenerating ? "animate-spin" : ""}`} />
            <span>{isGenerating ? "Generating..." : "Regenerate"}</span>
          </button>
        )}

        <button
          onClick={() => setIsPlaying(!isPlaying)}
          disabled={scenes.length === 0}
          className="px-3 sm:px-3.5 py-1.5 rounded-lg bg-[#1B1D21] hover:bg-[#23262C] border border-[#24272E] text-neutral-200 text-xs font-medium flex items-center gap-1.5 transition-colors disabled:opacity-40 min-h-[36px]"
          aria-label={isPlaying ? "Pause Preview" : "Play Timeline"}
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5 text-[#E0693B]" />
              <span className="hidden sm:inline">Pause</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 text-[#E0693B] fill-[#E0693B]" />
              <span className="hidden sm:inline">Play</span>
            </>
          )}
        </button>

        <button
          onClick={onRenderClick}
          disabled={scenes.length === 0}
          className="btn-primary text-xs px-3.5 py-1.5 min-h-[36px] flex items-center gap-1.5 shadow-sm disabled:opacity-40"
        >
          <Wand2 className="w-3.5 h-3.5" />
          <span>Export MP4</span>
        </button>
      </div>
    </header>
  );
}