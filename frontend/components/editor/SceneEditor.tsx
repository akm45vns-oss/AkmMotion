"use client";

import { useState, useEffect } from "react";
import { useEditorStore } from "@/lib/stores/editorStore";
import { scenesApi } from "@/lib/api/scenes";
import {
  Type, ImageIcon, Sliders, Mic2, RefreshCw, Sparkles,
  Film, Subtitles, Crop, Wand2, ChevronDown
} from "lucide-react";
import HealthScoreCard from "@/components/editor/HealthScoreCard";
import AutoImproveModal from "@/components/editor/AutoImproveModal";

// ─── Types ────────────────────────────────────────────────────────────────────
type SubtitleStyle = "yellow-cyan" | "karaoke" | "minimal";
type AspectRatio   = "9:16" | "1:1" | "16:9";
type VoiceLang     = "en" | "hi";
type VoiceGender   = "male" | "female";
type StylePreset   = "Explainer" | "Cinematic" | "Vlog" | "Anime" | "Story" | "Finance";

const STYLE_PRESETS: { id: StylePreset; label: string; emoji: string }[] = [
  { id: "Explainer", label: "Explainer",    emoji: "📘" },
  { id: "Cinematic",  label: "Cinematic",    emoji: "🎬" },
  { id: "Vlog",       label: "Vlog",         emoji: "📱" },
  { id: "Anime",      label: "Anime",        emoji: "✨" },
  { id: "Story",      label: "Story",        emoji: "📖" },
  { id: "Finance",    label: "Finance",      emoji: "💹" },
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
    aspectRatio,
    setAspectRatio,
    voiceLang,
    setVoiceLang,
    voiceGender,
    setVoiceGender,
    stylePreset,
    setStylePreset,
  } = useEditorStore();

  const activeScene = scenes[activeSceneIndex];
  const fullProjectScript = scenes.map((s) => s.narration).join(" ");

  // ── Local scene field state ───────────────────────────────────────────────
  const [narration,      setNarration]      = useState("");
  const [subtitle,       setSubtitle]       = useState("");
  const [imagePrompt,    setImagePrompt]    = useState("");
  const [animationStyle, setAnimationStyle] = useState("ken_burns");
  const [duration,       setDuration]       = useState(7.0);
  const [saving,         setSaving]         = useState(false);
  const [regenLoading,   setRegenLoading]   = useState(false);
  const [regenSuccess,   setRegenSuccess]   = useState(false);
  const [enhanceLoading, setEnhanceLoading] = useState(false);
  const [isAutoImproveOpen, setIsAutoImproveOpen] = useState(false);

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
      <div className="w-80 border-l border-gray-800 bg-[#0D1322] p-6 flex items-center justify-center text-center text-xs text-gray-500">
        <div>
          <Sliders className="w-5 h-5 text-gray-700 mx-auto mb-2" />
          Select a scene to edit
        </div>
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
      console.error(err);
    } finally {
      setSaving(false);
    }
  };

  // ── Regenerate scene image ────────────────────────────────────────────────
  const handleRegenerateImage = async () => {
    setRegenLoading(true);
    setRegenSuccess(false);
    try {
      const res = await fetch("http://localhost:8000/api/v1/ai/regenerate-scene-image", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}` },
        body: JSON.stringify({
          scene_id: activeScene.id,
          prompt:   imagePrompt || undefined,
          style:    stylePreset,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        // Update the scene's image asset URL in the store
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
        const res = await fetch("http://localhost:8000/api/v1/ai/generate-scene-prompt", {
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

    const handleAcceptImprovedScript = (improvedText: string) => {
    setNarration(improvedText);
    setIsAutoImproveOpen(false);
  };

  return (
    <div className="w-96 border-l border-gray-800/60 bg-[#0D1322] flex flex-col justify-between overflow-y-auto">
      <div className="p-4 space-y-5">

        {/* ── Section header ─────────────────────────────────────────────── */}
        <div className="flex items-center justify-between border-b border-gray-800/60 pb-3">
          <h2 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-indigo-400" />
            Scene #{activeScene.scene_number} Inspector
          </h2>
          <div className="flex items-center gap-1.5">
            {activeScene.camera_motion && (
              <span className="camera-badge">
                {activeScene.camera_motion.replace(/_/g, " ").toUpperCase()}
              </span>
            )}
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 font-semibold border border-indigo-500/20">
              {duration}s
            </span>
          </div>
        </div>

        {/* ── Script Health Score ────────────────────────────────────────── */}
        <HealthScoreCard
          scriptText={fullProjectScript || narration}
          language="Auto Detect"
          onAutoImproveClick={() => setIsAutoImproveOpen(true)}
        />

        {/* ─────────────── STYLE PRESET ──────────────────────────────────── */}
        <div className="space-y-2">
          <label className="section-label flex items-center gap-1.5">
            <Film className="w-3 h-3 text-indigo-400" />
            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wider">Style Preset</span>
          </label>
          <div className="flex flex-wrap gap-1.5">
            {STYLE_PRESETS.map(({ id, label, emoji }) => (
              <button
                key={id}
                onClick={() => setStylePreset(id)}
                className={`px-2.5 py-1.5 rounded-lg text-[10px] font-semibold border transition-all flex items-center gap-1 ${
                  stylePreset === id
                    ? "bg-indigo-600/20 border-indigo-500/60 text-indigo-300"
                    : "bg-transparent border-gray-800 text-gray-500 hover:border-gray-700 hover:text-gray-300"
                }`}
              >
                <span>{emoji}</span>
                <span>{label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ─────────────── VOICE PICKER ─────────────────────────────────── */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5">
            <Mic2 className="w-3 h-3 text-purple-400" />
            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wider">Voice</span>
          </label>
          <div className="voice-picker space-y-2">
            {/* Language */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-gray-400">Language</span>
              <div className="flex gap-1">
                {(["en", "hi"] as const).map((l) => (
                  <button
                    key={l}
                    onClick={() => setVoiceLang(l)}
                    className={`voice-option-pill ${voiceLang === l ? "active" : ""}`}
                  >
                    {l === "en" ? "🇬🇧 English" : "🇮🇳 Hindi"}
                  </button>
                ))}
              </div>
            </div>
            {/* Gender */}
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-gray-400">Voice</span>
              <div className="flex gap-1">
                {(["male", "female"] as const).map((g) => (
                  <button
                    key={g}
                    onClick={() => setVoiceGender(g)}
                    className={`voice-option-pill ${voiceGender === g ? "active" : ""}`}
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
          <label className="flex items-center gap-1.5">
            <Crop className="w-3 h-3 text-cyan-400" />
            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wider">Aspect Ratio</span>
          </label>
          <div className="aspect-toggle w-full">
            {(["9:16", "1:1", "16:9"] as const).map((r) => (
              <button
                key={r}
                onClick={() => setAspectRatio(r)}
                className={`aspect-toggle-btn flex-1 ${aspectRatio === r ? "active" : ""}`}
              >
                {r === "9:16" ? "📱 9:16" : r === "1:1" ? "⬛ 1:1" : "🖥 16:9"}
              </button>
            ))}
          </div>
        </div>

        {/* ─────────────── SUBTITLE STYLE ───────────────────────────────── */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5">
            <Subtitles className="w-3 h-3 text-cyan-400" />
            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wider">Subtitle Style</span>
          </label>
          <div className="flex gap-1.5">
            {([
              { id: "yellow-cyan" as const, label: "Yellow-Cyan" },
              { id: "karaoke"    as const, label: "Karaoke" },
              { id: "minimal"    as const, label: "Minimal" },
            ]).map(({ id, label }) => (
              <button
                key={id}
                onClick={() => setSubtitleStyle(id)}
                className={`subtitle-style-btn flex-1 ${subtitleStyle === id ? "active" : ""}`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* ─────────────── NARRATION TEXT ───────────────────────────────── */}
        <div className="space-y-2">
          <label className="flex items-center gap-1.5">
            <Type className="w-3 h-3 text-indigo-400" />
            <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wider">Narration Script</span>
          </label>
          <textarea
            rows={3}
            value={narration}
            onChange={(e) => setNarration(e.target.value)}
            className="w-full p-3 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 leading-relaxed resize-none"
          />
        </div>

        {/* ─────────────── SUBTITLE CAPTION ─────────────────────────────── */}
        <div className="space-y-2">
          <label className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider block">
            Subtitle Caption
          </label>
          <input
            type="text"
            value={subtitle}
            onChange={(e) => setSubtitle(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
          />
        </div>

        {/* ─────────────── IMAGE PROMPT + REGEN ────────────────────────── */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-1.5">
              <ImageIcon className="w-3 h-3 text-purple-400" />
              <span className="text-[10px] font-bold text-gray-300 uppercase tracking-wider">Visual Prompt</span>
            </label>
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={handleEnhancePrompt}
                disabled={enhanceLoading || regenLoading}
                className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-semibold border border-indigo-500/40 text-indigo-400 hover:bg-indigo-500/10 bg-transparent transition-all disabled:opacity-40"
                title="Use AI to craft a vivid, story-aligned English visual prompt for this scene"
              >
                <Sparkles className={`w-2.5 h-2.5 ${enhanceLoading ? "animate-spin" : ""}`} />
                {enhanceLoading ? "Writing..." : "AI Prompt"}
              </button>
              <button
                type="button"
                onClick={handleRegenerateImage}
                disabled={regenLoading || enhanceLoading}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-all ${
                  regenSuccess
                    ? "border-emerald-500/60 text-emerald-400 bg-emerald-500/10"
                    : "border-purple-500/40 text-purple-400 hover:bg-purple-500/10 bg-transparent"
                } disabled:opacity-40 disabled:cursor-not-allowed`}
                title="Regenerate scene image with Flux"
              >
                <RefreshCw className={`w-2.5 h-2.5 ${regenLoading ? "animate-spin" : ""}`} />
                {regenSuccess ? "Done!" : regenLoading ? "Generating..." : "Regen Image"}
              </button>
            </div>
          </div>
          <textarea
            rows={3}
            value={imagePrompt}
            onChange={(e) => setImagePrompt(e.target.value)}
            className="w-full p-3 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 leading-relaxed resize-none"
          />
        </div>

        {/* ─────────────── ANIMATION + DURATION ────────────────────────── */}
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-[10px] font-semibold text-gray-500 uppercase mb-1">Animation</label>
            <select
              value={animationStyle}
              onChange={(e) => setAnimationStyle(e.target.value)}
              className="w-full px-2.5 py-2 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              {ANIMATION_STYLES.map((s) => (
                <option key={s} value={s}>
                  {s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-[10px] font-semibold text-gray-500 uppercase mb-1">Duration (s)</label>
            <input
              type="number"
              step="0.5"
              min="3"
              max="15"
              value={duration}
              onChange={(e) => setDuration(parseFloat(e.target.value))}
              className="w-full px-2.5 py-2 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>
      </div>

      {/* ── Save button ──────────────────────────────────────────────────────── */}
      <div className="p-4 border-t border-gray-800/60 space-y-2">
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {saving ? (
            <><RefreshCw className="w-3 h-3 animate-spin" /> Saving...</>
          ) : (
            <><Wand2 className="w-3 h-3" /> Apply Changes</>
          )}
        </button>
      </div>

      {/* ── Auto-improve modal ────────────────────────────────────────────────── */}
      {isAutoImproveOpen && (
        <AutoImproveModal
          originalScript={narration}
          onAccept={handleAcceptImprovedScript}
          onClose={() => setIsAutoImproveOpen(false)}
        />
      )}
    </div>
  );
}