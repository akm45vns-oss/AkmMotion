"use client";

import { useState, useEffect } from "react";
import { useEditorStore } from "@/lib/stores/editorStore";
import { scenesApi } from "@/lib/api/scenes";
import {
  Type, ImageIcon, Sliders, Mic2, RefreshCw, Sparkles,
  Film, Subtitles, Crop, Wand2
} from "lucide-react";
import { API_BASE_URL } from "@/lib/api/client";

type SubtitleStyle = "yellow-cyan" | "karaoke" | "minimal";
type StylePreset   = "Explainer" | "Cinematic" | "Vlog" | "Anime" | "Story" | "Finance";

const STYLE_PRESETS: { id: StylePreset; label: string; emoji: string }[] = [
  { id: "Explainer", label: "Explainer", emoji: "📘" },
  { id: "Cinematic", label: "Cinematic", emoji: "🎬" },
  { id: "Vlog",      label: "Vlog",      emoji: "📱" },
  { id: "Anime",     label: "Anime",     emoji: "✨" },
  { id: "Story",     label: "Story",     emoji: "📖" },
  { id: "Finance",   label: "Finance",   emoji: "💹" },
];

const ANIMATION_STYLES = [
  "ken_burns", "zoom", "pan", "fade", "camera_push", "camera_pull", "motion_blur"
];

export default function SceneEditor() {
  const {
    scenes,
    activeSceneIndex,
    updateSceneInStore,
    subtitleStyle,
    setSubtitleStyle,
    voiceLang,
    setVoiceLang,
    voiceGender,
    setVoiceGender,
    stylePreset,
    setStylePreset,
  } = useEditorStore();

  const activeScene = scenes[activeSceneIndex];
  const fullProjectScript = scenes.map((s) => s.narration).join(" ");

  const [narration,      setNarration]      = useState("");
  const [subtitle,       setSubtitle]       = useState("");
  const [imagePrompt,    setImagePrompt]    = useState("");
  const [animationStyle, setAnimationStyle] = useState("ken_burns");
  const [duration,       setDuration]       = useState(7.0);
  const [saving,         setSaving]         = useState(false);
  const [regenLoading,   setRegenLoading]   = useState(false);
  const [regenSuccess,   setRegenSuccess]   = useState(false);
  const [enhanceLoading, setEnhanceLoading] = useState(false);

  useEffect(() => {
    if (activeScene) {
      setNarration(activeScene.narration || "");
      setSubtitle(activeScene.subtitle || "");
      setImagePrompt(activeScene.image_prompt || "");
      setAnimationStyle(activeScene.animation_style || "ken_burns");
      setDuration(activeScene.duration || 7.0);
      setRegenSuccess(false);
    }
  }, [activeSceneIndex, activeScene]);

  if (!activeScene) {
    return (
      <div className="w-full h-full p-6 flex flex-col items-center justify-center text-center text-xs text-neutral-400">
        <Sliders className="w-6 h-6 text-neutral-500 mb-2" />
        <p>Select a scene from the timeline below to edit its properties</p>
      </div>
    );
  }

  // ── Save scene changes ────────────────────────────────────────────────────
  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await scenesApi.update(activeScene.id, {
        narration,
        subtitle,
        image_prompt: imagePrompt,
        animation_style: animationStyle as any,
        duration,
      });
      updateSceneInStore(activeScene.id, updated);
    } catch (err) {
      console.error("Save scene error:", err);
    } finally {
      setSaving(false);
    }
  };

  // ── Regenerate scene image ────────────────────────────────────────────────
  const handleRegenerateImage = async () => {
    setRegenLoading(true);
    setRegenSuccess(false);
    try {
      const res = await fetch(`${API_BASE_URL}/ai/regenerate-scene-image`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
        },
        body: JSON.stringify({
          scene_id: activeScene.id,
          prompt:   imagePrompt || undefined,
          style:    stylePreset,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        const updatedAssets = (activeScene.assets || []).map((a: any) =>
          a.asset_type === "image" ? { ...a, url: data.image_url } : a
        );
        updateSceneInStore(activeScene.id, { assets: updatedAssets } as any);
        setRegenSuccess(true);
        setTimeout(() => setRegenSuccess(false), 3000);
      }
    } catch (err) {
      console.error("Regen error:", err);
    } finally {
      setRegenLoading(false);
    }
  };

  // ── AI Prompt enhancer ────────────────────────────────────────────────────
  const handleEnhancePrompt = async () => {
    if (!activeScene) return;
    setEnhanceLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/ai/generate-scene-prompt`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
        },
        body: JSON.stringify({
          narration: narration || activeScene.narration,
          style: stylePreset,
          story_context: fullProjectScript,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        if (data.prompt) {
          setImagePrompt(data.prompt);
        }
      }
    } catch (err) {
      console.error("Enhance prompt error:", err);
    } finally {
      setEnhanceLoading(false);
    }
  };

  return (
    <div className="w-full h-full flex flex-col justify-between overflow-y-auto bg-[#151616] border-l border-[#292A29]">
      <div className="p-4 sm:p-5 space-y-6">
        {/* ── Section Header ─────────────────────────────────────────────── */}
        <div className="flex items-center justify-between border-b border-[#292A29] pb-3">
          <div>
            <h2 className="text-xs font-bold text-[#F5F1E8] uppercase tracking-wider flex items-center gap-1.5">
              <Sliders className="w-3.5 h-3.5 text-[#E76536]" />
              Scene #{activeScene.scene_number} Inspector
            </h2>
            <p className="text-[10px] text-[#77746E] mt-0.5 font-mono">
              Scene timing: {duration}s · Vertical 9:16
            </p>
          </div>
          <div className="flex items-center gap-1.5">
            {activeScene.camera_motion && (
              <span className="camera-badge">
                {activeScene.camera_motion.replace(/_/g, " ").toUpperCase()}
              </span>
            )}
          </div>
        </div>

        {/* ─────────────── 1. SCENE SCRIPT (USER-AUTHORITATIVE) ──────────── */}
        <div className="space-y-1.5 rounded-lg p-3 bg-[#1B1C1C] border border-[#292A29]">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-[#F5F1E8] uppercase tracking-wider">
              <Type className="w-3.5 h-3.5 text-[#4FAE7B]" />
              <span>SCENE SCRIPT</span>
            </label>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#4FAE7B]/10 border border-[#4FAE7B]/25 text-[#4FAE7B] font-semibold">
              AUTHORITATIVE
            </span>
          </div>
          <p className="text-[10px] text-[#77746E]">
            Exact spoken narration — preserved verbatim for voiceover synthesis.
          </p>
          <textarea
            rows={3}
            value={narration}
            onChange={(e) => setNarration(e.target.value)}
            className="input-base text-xs leading-relaxed resize-none mt-1 font-normal"
            placeholder="Scene narration text..."
          />
        </div>

        {/* ─────────────── 2. BURNED-IN SUBTITLE ─────────────────────────── */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-[#A9A49B] uppercase tracking-wider flex items-center gap-1.5">
              <Subtitles className="w-3.5 h-3.5 text-[#E76536]" />
              <span>BURNED-IN SUBTITLE</span>
            </label>
          </div>
          <input
            type="text"
            value={subtitle}
            onChange={(e) => setSubtitle(e.target.value)}
            className="input-base text-xs"
            placeholder="Subtitle text to display on screen..."
          />

          {/* Subtitle Style Switcher */}
          <div className="pt-1">
            <span className="text-[10px] text-[#77746E] uppercase tracking-wider block mb-1">Layout Mode</span>
            <div className="grid grid-cols-3 gap-1.5">
              {([
                { id: "yellow-cyan" as const, label: "Word Sync" },
                { id: "karaoke"    as const, label: "Karaoke" },
                { id: "minimal"    as const, label: "Minimal" },
              ]).map(({ id, label }) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => setSubtitleStyle(id)}
                  className={`py-1.5 px-2 rounded-md text-[11px] font-medium border text-center transition-colors min-h-[32px] ${
                    subtitleStyle === id
                      ? "bg-[#1B1C1C] border-[#E76536] text-[#E76536] font-semibold ring-1 ring-[#E76536]"
                      : "bg-[#151616] border-[#292A29] text-[#77746E] hover:text-[#F5F1E8]"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* ─────────────── 3. VISUAL PROMPT (AI GENERATED) ────────────────── */}
        <div className="space-y-2 rounded-lg p-3 bg-[#1B1C1C] border border-[#292A29]">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-[#F5F1E8] uppercase tracking-wider">
              <ImageIcon className="w-3.5 h-3.5 text-[#E76536]" />
              <span>VISUAL PROMPT</span>
            </label>
            <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#E76536]/10 border border-[#E76536]/25 text-[#E76536] font-semibold">
              AI INSTRUCTION
            </span>
          </div>
          <p className="text-[10px] text-[#77746E]">
            Cinematic visual prompt guiding image synthesis in 9:16 vertical framing.
          </p>
          <textarea
            rows={3}
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            className="input-base text-xs leading-relaxed resize-none font-normal"
            placeholder="Cinematic description of visual shot, setting, characters..."
          />

          {/* Secondary Actions for Visuals */}
          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={handleEnhancePrompt}
              disabled={enhanceLoading || regenLoading}
              className="btn-secondary text-[11px] py-1 px-2.5 min-h-[32px] border border-[#292A29] disabled:opacity-40"
              title="Enhance prompt with AI Director"
            >
              <Sparkles className={`w-3 h-3 text-[#E76536] ${enhanceLoading ? "animate-spin" : ""}`} />
              <span>{enhanceLoading ? "Writing..." : "AI Prompt"}</span>
            </button>
            <button
              type="button"
              onClick={handleRegenerateImage}
              disabled={regenLoading || enhanceLoading}
              className={`text-[11px] py-1 px-3 rounded-md font-medium border transition-colors flex items-center gap-1.5 min-h-[32px] ${
                regenSuccess
                  ? "border-[#4FAE7B] text-[#4FAE7B] bg-[#4FAE7B]/10"
                  : "border-[#292A29] bg-[#151616] text-[#A9A49B] hover:text-[#F5F1E8] hover:border-[#383938]"
              } disabled:opacity-40 disabled:cursor-not-allowed`}
            >
              <RefreshCw className={`w-3 h-3 ${regenLoading ? "animate-spin" : ""}`} />
              <span>{regenSuccess ? "Generated!" : regenLoading ? "Generating..." : "Regenerate Visual"}</span>
            </button>
          </div>
        </div>

        {/* ─────────────── 4. ANIMATION & DURATION ───────────────────────── */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <div>
            <label className="block text-xs font-semibold text-[#A9A49B] uppercase tracking-wider mb-1">
              ANIMATION
            </label>
            <select
              value={animationStyle}
              onChange={(e) => setAnimationStyle(e.target.value)}
              className="input-base text-xs py-2"
            >
              {ANIMATION_STYLES.map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-[#A9A49B] uppercase tracking-wider mb-1">
              DURATION (S)
            </label>
            <input
              type="number"
              step="0.5"
              min="3"
              max="15"
              value={duration}
              onChange={(e) => setDuration(parseFloat(e.target.value))}
              className="input-base text-xs py-2 font-mono"
            />
          </div>
        </div>
      </div>

      {/* ── 5. ACTIONS (PRIMARY CTA) ─────────────────────────────────────────── */}
      <div className="p-4 border-t border-[#292A29] bg-[#151616]">
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary w-full py-2.5 text-xs font-semibold flex items-center justify-center gap-2 shadow-sm"
        >
          {saving ? (
            <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Saving Changes...</>
          ) : (
            <><Wand2 className="w-3.5 h-3.5" /> APPLY CHANGES</>
          )}
        </button>
      </div>
    </div>
  );
}