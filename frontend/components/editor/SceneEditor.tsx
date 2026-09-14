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
    <div className="w-full h-full flex flex-col justify-between overflow-y-auto bg-[#141517] border-l border-[#24272E]">
      <div className="p-4 sm:p-5 space-y-5">
        {/* ── Section Header ─────────────────────────────────────────────── */}
        <div className="flex items-center justify-between border-b border-[#24272E] pb-3">
          <h2 className="text-xs font-bold text-[#F2F2F3] uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-[#E0693B]" />
            Scene #{activeScene.scene_number} Inspector
          </h2>
          <div className="flex items-center gap-1.5">
            {activeScene.camera_motion && (
              <span className="camera-badge">
                {activeScene.camera_motion.replace(/_/g, " ").toUpperCase()}
              </span>
            )}
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#1B1D21] border border-[#24272E] text-neutral-300 font-mono">
              {duration}s
            </span>
          </div>
        </div>

        {/* ─────────────── STYLE PRESET ──────────────────────────────────── */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5 text-[11px] font-semibold text-neutral-300 uppercase tracking-wider">
            <Film className="w-3 h-3 text-[#E0693B]" />
            <span>Style Preset</span>
          </label>
          <div className="grid grid-cols-3 gap-1.5">
            {STYLE_PRESETS.map(({ id, label, emoji }) => (
              <button
                key={id}
                type="button"
                onClick={() => setStylePreset(id)}
                className={`px-2 py-1.5 rounded-lg text-[11px] font-medium border transition-colors flex items-center justify-center gap-1 min-h-[36px] ${
                  stylePreset === id
                    ? "bg-[#E0693B]/10 border-[#E0693B] text-[#E0693B] font-semibold"
                    : "bg-[#1B1D21] border-[#24272E] text-neutral-400 hover:text-white"
                }`}
              >
                <span>{emoji}</span>
                <span className="truncate">{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ─────────────── VOICE PICKER ─────────────────────────────────── */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5 text-[11px] font-semibold text-neutral-300 uppercase tracking-wider">
            <Mic2 className="w-3 h-3 text-[#E0693B]" />
            <span>Voice Options</span>
          </label>
          <div className="p-3 rounded-xl bg-[#1B1D21] border border-[#24272E] space-y-2 text-xs">
            {/* Language */}
            <div className="flex items-center justify-between">
              <span className="text-neutral-400">Language</span>
              <div className="flex gap-1">
                {(["en", "hi"] as const).map((l) => (
                  <button
                    key={l}
                    type="button"
                    onClick={() => setVoiceLang(l)}
                    className={`px-2.5 py-1 rounded-md text-[11px] border font-medium transition-colors ${
                      voiceLang === l
                        ? "bg-[#E0693B] border-[#E0693B] text-white"
                        : "bg-[#141517] border-[#24272E] text-neutral-400 hover:text-white"
                    }`}
                  >
                    {l === "en" ? "🇬🇧 English" : "🇮🇳 Hindi"}
                  </button>
                ))}
              </div>
            </div>
            {/* Gender */}
            <div className="flex items-center justify-between">
              <span className="text-neutral-400">Gender</span>
              <div className="flex gap-1">
                {(["male", "female"] as const).map((g) => (
                  <button
                    key={g}
                    type="button"
                    onClick={() => setVoiceGender(g)}
                    className={`px-2.5 py-1 rounded-md text-[11px] border font-medium transition-colors ${
                      voiceGender === g
                        ? "bg-[#E0693B] border-[#E0693B] text-white"
                        : "bg-[#141517] border-[#24272E] text-neutral-400 hover:text-white"
                    }`}
                  >
                    {g === "male" ? "👨 Male" : "👩 Female"}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* ─────────────── ASPECT RATIO ─────────────────────────────────── */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5 text-[11px] font-semibold text-neutral-300 uppercase tracking-wider">
            <Crop className="w-3 h-3 text-[#E0693B]" />
            <span>Format</span>
          </label>
          <div className="px-3 py-2 rounded-xl bg-[#1B1D21] border border-[#24272E] flex items-center justify-between text-xs">
            <span className="font-semibold text-[#F2F2F3] flex items-center gap-2">
              <span>📱</span> 9:16 Vertical (Shorts / Reels)
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#141517] border border-[#24272E] text-neutral-400 font-mono">
              1080×1920
            </span>
          </div>
        </div>

        {/* ─────────────── SUBTITLE STYLE ───────────────────────────────── */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5 text-[11px] font-semibold text-neutral-300 uppercase tracking-wider">
            <Subtitles className="w-3 h-3 text-[#E0693B]" />
            <span>Subtitle Layout</span>
          </label>
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
                className={`py-1.5 px-2 rounded-lg text-[11px] font-medium border text-center transition-colors min-h-[36px] ${
                  subtitleStyle === id
                    ? "bg-[#E0693B]/10 border-[#E0693B] text-[#E0693B] font-semibold"
                    : "bg-[#1B1D21] border-[#24272E] text-neutral-400 hover:text-white"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* ─────────────── NARRATION TEXT ───────────────────────────────── */}
        <div className="space-y-1.5">
          <label className="flex items-center gap-1.5 text-[11px] font-semibold text-neutral-300 uppercase tracking-wider">
            <Type className="w-3 h-3 text-[#E0693B]" />
            <span>Narration Text</span>
          </label>
          <textarea
            rows={3}
            value={narration}
            onChange={(e) => setNarration(e.target.value)}
            className="input-base text-xs leading-relaxed resize-none"
          />
        </div>

        {/* ─────────────── SUBTITLE CAPTION ─────────────────────────────── */}
        <div className="space-y-1.5">
          <label className="text-[11px] font-semibold text-neutral-300 uppercase tracking-wider block">
            Burned-In Subtitle
          </label>
          <input
            type="text"
            value={subtitle}
            onChange={(e) => setSubtitle(e.target.value)}
            className="input-base text-xs"
          />
        </div>

        {/* ─────────────── IMAGE PROMPT + REGEN ────────────────────────── */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-1.5 text-[11px] font-semibold text-neutral-300 uppercase tracking-wider">
              <ImageIcon className="w-3 h-3 text-[#E0693B]" />
              <span>Visual Prompt</span>
            </label>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleEnhancePrompt}
                disabled={enhanceLoading || regenLoading}
                className="btn-ghost text-[10px] py-1 px-2 border border-[#24272E] disabled:opacity-40"
                title="Optimize prompt with AI Director"
              >
                <Sparkles className={`w-2.5 h-2.5 text-[#E0693B] ${enhanceLoading ? "animate-spin" : ""}`} />
                <span>{enhanceLoading ? "Writing..." : "AI Prompt"}</span>
              </button>
              <button
                type="button"
                onClick={handleRegenerateImage}
                disabled={regenLoading || enhanceLoading}
                className={`text-[10px] py-1 px-2.5 rounded-md font-medium border transition-colors flex items-center gap-1 ${
                  regenSuccess
                    ? "border-[#2EB88A] text-[#2EB88A] bg-[#2EB88A]/10"
                    : "border-[#E0693B]/40 text-[#E0693B] hover:bg-[#E0693B]/10"
                } disabled:opacity-40 disabled:cursor-not-allowed`}
              >
                <RefreshCw className={`w-2.5 h-2.5 ${regenLoading ? "animate-spin" : ""}`} />
                <span>{regenSuccess ? "Done!" : regenLoading ? "Generating..." : "Regen Visual"}</span>
              </button>
            </div>
          </div>
          <textarea
            rows={3}
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            className="input-base text-xs leading-relaxed resize-none"
          />
        </div>

        {/* ─────────────── ANIMATION + DURATION ────────────────────────── */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[11px] font-semibold text-neutral-400 uppercase mb-1">Animation</label>
            <select
              value={animationStyle}
              onChange={(e) => setAnimationStyle(e.target.value)}
              className="input-base text-xs py-1.5"
            >
              {ANIMATION_STYLES.map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-[11px] font-semibold text-neutral-400 uppercase mb-1">Duration (s)</label>
            <input
              type="number"
              step="0.5"
              min="3"
              max="15"
              value={duration}
              onChange={(e) => setDuration(parseFloat(e.target.value))}
              className="input-base text-xs py-1.5"
            />
          </div>
        </div>
      </div>

      {/* ── Save button ──────────────────────────────────────────────────────── */}
      <div className="p-4 border-t border-[#24272E] bg-[#141517]">
        <button
          onClick={handleSave}
          disabled={saving}
          className="btn-primary w-full py-2.5 text-xs flex items-center justify-center gap-2 shadow-sm"
        >
          {saving ? (
            <><RefreshCw className="w-3.5 h-3.5 animate-spin" /> Saving Changes...</>
          ) : (
            <><Wand2 className="w-3.5 h-3.5" /> Apply Scene Changes</>
          )}
        </button>
      </div>
    </div>
  );
}