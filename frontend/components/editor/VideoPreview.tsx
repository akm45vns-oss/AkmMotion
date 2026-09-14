"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useEditorStore } from "@/lib/stores/editorStore";
import { Play, Pause, Volume2, Sparkles, Film, Mic2, Monitor, Square } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE_URL } from "@/lib/api/client";

// ─── Aspect ratio frame dimensions ───────────────────────────────────────────
const FRAME_DIMS: Record<string, { w: number; h: number }> = {
  "9:16": { w: 310, h: 551 },
  "1:1":  { w: 380, h: 380 },
  "16:9": { w: 540, h: 304 },
};

interface VideoPreviewProps {
  activeScene?: any;
}

export default function VideoPreview({ activeScene: propScene }: VideoPreviewProps) {
  const {
    scenes,
    activeSceneIndex,
    activeSceneId,
    isPlaying,
    setIsPlaying,
    setActiveSceneIndex,
    setActiveSceneId,
    subtitleStyle,
    aspectRatio,
    voiceLang,
    voiceGender,
    currentWordIndex,
    setCurrentWordIndex,
    wordTimings,
    setWordTimings,
    resetKaraoke,
  } = useEditorStore();

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [imgSrcOverrides, setImgSrcOverrides] = useState<Record<string, string>>({});
  const [failedScenes, setFailedScenes] = useState<Record<string, boolean>>({});
  const [isImageLoading, setIsImageLoading] = useState(true);

  const activeScene =
    propScene ||
    scenes.find((s) => s.id === activeSceneId) ||
    scenes[activeSceneIndex] ||
    scenes[0];

  // ── Image URL resolution ──────────────────────────────────────────────────
  const getSceneImageUrl = (scene: any): string => {
    const imageAsset = scene?.assets?.find((a: any) => a.asset_type === "image");
    let storedUrl = imageAsset?.url || "";
    if (storedUrl) {
      // Optimize any legacy Pollinations URLs from flux 1080x1920 to fast flux-realism 768x1344
      if (storedUrl.includes("pollinations.ai")) {
        storedUrl = storedUrl
          .replace(/model=flux(&|$)/, "model=flux-realism$1")
          .replace("width=1080", "width=768")
          .replace("height=1920", "height=1344");
      }
      return storedUrl;
    }
    const rawPrompt = (scene?.image_prompt || scene?.narration || "").replace(/\*\*/g, "").trim();
    const promptText = rawPrompt || `cinematic Indian story scene ${scene?.scene_number || 1}`;
    const encoded = encodeURIComponent(
      `photorealistic 8k render, ${promptText}, 9:16 vertical aspect ratio, cinematic lighting, ultra detailed`
    );
    const seed = ((scene?.scene_number || 1) * 73 + 1234) % 99999;
    return `https://image.pollinations.ai/prompt/${encoded}?width=768&height=1344&model=flux-realism&nologo=true&seed=${seed}`;
  };

  const sceneKey = activeScene?.id || String(activeScene?.scene_number || 1);
  const baseImageUrl = activeScene ? getSceneImageUrl(activeScene) : "";
  const currentImageUrl = imgSrcOverrides[sceneKey] || baseImageUrl;
  const isSceneImageFailed = Boolean(failedScenes[sceneKey]);

  useEffect(() => {
    setIsImageLoading(true);
  }, [currentImageUrl]);

  // ── Voice & Karaoke engine ────────────────────────────────────────────────
  const pickVoice = useCallback((lang: string, gender: string): SpeechSynthesisVoice | null => {
    const voices = window.speechSynthesis.getVoices();
    const langCode = lang === "hi" ? "hi-IN" : "en-IN";

    // Try exact lang match first
    const exactMatch = voices.find((v) => v.lang === langCode);
    if (exactMatch) return exactMatch;

    // Broader search for Indian voices
    const broadMatch = voices.find((v) =>
      v.lang.startsWith(lang === "hi" ? "hi" : "en") &&
      (v.name.includes("India") || v.name.includes("Rishi") || v.name.includes("Heera") ||
       v.name.includes("Veena") || v.name.includes("Moira") || v.lang.includes("IN"))
    );
    return broadMatch ?? null;
  }, []);

  const buildWordTimings = useCallback((text: string, estimatedDuration: number) => {
    // Build word timing array from character-weight model (mirrors backend logic)
    const words = text.split(/\s+/).filter(Boolean);
    if (!words.length) return [];

    const weightOf = (w: string) => {
      const n = w.replace(/[.,!?।]/g, "").length;
      if (n <= 2) return 0.5;
      if (n <= 5) return 1.0;
      if (n <= 8) return 1.4;
      return 1.8;
    };

    const weights = words.map(weightOf);
    const totalW = weights.reduce((a, b) => a + b, 0) || 1;
    const onset = 0.25;
    const available = Math.max(estimatedDuration - onset, 1);

    let t = onset;
    return words.map((word, i) => {
      const dur = (weights[i] / totalW) * available;
      const entry = { word, start: t, end: t + dur, index: i };
      t += dur;
      return entry;
    });
  }, []);

  const playSceneVoice = useCallback(
    (sceneIdx: number) => {
      // 1. Cancel previous audio & browser speech
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      resetKaraoke();

      const scene = scenes[sceneIdx];
      if (!scene) return;

      const cleanText = (scene.narration || scene.subtitle || "")
        .replace(/\*\*/g, "")
        .replace(/[^\w\s.,?!''\u0900-\u097F-]/g, "")
        .trim();

      if (!cleanText) {
        if (sceneIdx + 1 < scenes.length) {
          setActiveSceneIndex(sceneIdx + 1);
          setActiveSceneId(scenes[sceneIdx + 1].id);
          playSceneVoice(sceneIdx + 1);
        } else {
          setIsPlaying(false);
        }
        return;
      }

      // Initial word timings estimate
      const estimatedDuration = scene.duration || cleanText.split(" ").length / 2.1;
      let timings = buildWordTimings(cleanText, estimatedDuration);
      setWordTimings(timings);

      // 2. Play exact Edge Neural TTS audio from backend
      const ttsUrl = `${API_BASE_URL}/ai/tts?text=${encodeURIComponent(cleanText)}&language=${voiceLang}&gender=${voiceGender}`;
      const audio = new Audio(ttsUrl);
      audioRef.current = audio;

      let timingsUpdated = false;

      audio.onloadedmetadata = () => {
        if (audio.duration && audio.duration > 0) {
          timings = buildWordTimings(cleanText, audio.duration);
          setWordTimings(timings);
          timingsUpdated = true;
        }
      };

      audio.ontimeupdate = () => {
        const cur = audio.currentTime;
        if (!timingsUpdated && audio.duration && audio.duration > 0) {
          timings = buildWordTimings(cleanText, audio.duration);
          setWordTimings(timings);
          timingsUpdated = true;
        }
        const activeIdx = timings.findIndex((t) => cur >= t.start && cur <= t.end);
        if (activeIdx >= 0) {
          setCurrentWordIndex(activeIdx);
        }
      };

      audio.onended = () => {
        resetKaraoke();
        if (sceneIdx + 1 < scenes.length) {
          setActiveSceneIndex(sceneIdx + 1);
          setActiveSceneId(scenes[sceneIdx + 1]?.id);
          playSceneVoice(sceneIdx + 1);
        } else {
          setIsPlaying(false);
        }
      };

      audio.onerror = () => {
        // Fallback to local SpeechSynthesis if backend is temporarily unreachable
        if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = voiceLang === "hi" ? "hi-IN" : "en-IN";
        utterance.rate = voiceLang === "hi" ? 0.9 : 0.95;
        const voice = pickVoice(voiceLang, voiceGender);
        if (voice) utterance.voice = voice;
        utterance.onend = () => {
          resetKaraoke();
          if (sceneIdx + 1 < scenes.length) {
            setActiveSceneIndex(sceneIdx + 1);
            setActiveSceneId(scenes[sceneIdx + 1]?.id);
            playSceneVoice(sceneIdx + 1);
          } else {
            setIsPlaying(false);
          }
        };
        utteranceRef.current = utterance;
        window.speechSynthesis.speak(utterance);
      };

      audio.play().catch((err) => {
        console.warn("Audio playback interrupted or blocked:", err);
      });
    },
    [scenes, voiceLang, voiceGender, buildWordTimings, pickVoice, setWordTimings, setCurrentWordIndex, resetKaraoke, setIsPlaying, setActiveSceneIndex, setActiveSceneId]
  );

  const togglePlay = () => {
    const next = !isPlaying;
    setIsPlaying(next);
    if (next) {
      playSceneVoice(activeSceneIndex);
    } else {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      resetKaraoke();
    }
  };

  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // ── Subtitle rendering ────────────────────────────────────────────────────
  const renderSubtitle = () => {
    if (!activeScene?.subtitle) return null;
    const rawSub = (activeScene.subtitle || "").replace(/\*\*/g, "").trim();

    if (subtitleStyle === "minimal") {
      return (
        <motion.div
          key={rawSub}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center px-4 pb-2"
        >
          <p className="subtitle-minimal">{rawSub}</p>
        </motion.div>
      );
    }

    if (subtitleStyle === "karaoke") {
      const words = rawSub.split(" ");
      return (
        <motion.div
          key={rawSub}
          initial={{ y: 8, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="px-4 pb-4 text-center"
        >
          <div className="inline-block px-3 py-2 rounded-xl bg-black/80 backdrop-blur-md border border-white/10">
            <p className="font-extrabold text-sm leading-snug tracking-wide flex flex-wrap justify-center gap-x-1.5 gap-y-0.5">
              {words.map((word: string, i: number) => (
                <span
                  key={i}
                  className={`karaoke-word ${
                    i === currentWordIndex
                      ? "active"
                      : i < currentWordIndex
                      ? "spoken"
                      : ""
                  }`}
                >
                  {word}
                </span>
              ))}
            </p>
          </div>
        </motion.div>
      );
    }

    // Default: yellow-cyan
    const words = rawSub.toUpperCase().split(" ");
    return (
      <motion.div
        key={rawSub}
        initial={{ y: 10, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="px-4 pb-4 text-center"
      >
        <div className="inline-block px-4 py-2.5 rounded-2xl bg-black/85 backdrop-blur-md border border-white/15 shadow-2xl">
          <p className="font-extrabold text-sm leading-snug tracking-wide uppercase flex flex-wrap justify-center gap-x-1.5 gap-y-0.5">
            {words.map((word: string, i: number) => (
              <span
                key={i}
                className={
                  i === currentWordIndex
                    ? "text-yellow-300 drop-shadow-[0_0_10px_rgba(250,204,21,0.8)] scale-110 inline-block"
                    : i % 3 === 0
                    ? "text-yellow-400"
                    : i % 3 === 1
                    ? "text-cyan-300"
                    : "text-white"
                }
              >
                {word}
              </span>
            ))}
          </p>
        </div>
      </motion.div>
    );
  };

  // ── Aspect ratio frame dimensions ─────────────────────────────────────────
  const frameDim = FRAME_DIMS[aspectRatio] || FRAME_DIMS["9:16"];
  const isPortrait = aspectRatio === "9:16";

  // ── Camera motion label ───────────────────────────────────────────────────
  const cameraLabel = activeScene?.camera_motion
    ? activeScene.camera_motion.replace(/_/g, " ").toUpperCase()
    : activeScene?.animation_style?.replace(/_/g, " ").toUpperCase() || "KEN BURNS";

  return (
    <div className="flex-1 h-full flex flex-col items-center justify-center p-4 bg-[#090D16] relative overflow-hidden">
      {/* Ambient background glow */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-indigo-900/20 rounded-full blur-3xl" />
      </div>

      {/* ── Video Frame ───────────────────────────────────────────────────── */}
      <AnimatePresence mode="wait">
        <motion.div
          key={aspectRatio}
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.35, ease: "easeOut" }}
          style={{ width: frameDim.w, height: frameDim.h }}
          className="relative rounded-3xl overflow-hidden border-2 border-gray-800/80 bg-black shadow-2xl shadow-indigo-950/60 flex flex-col justify-between group"
        >
          {/* Background scene image with Ken Burns */}
          <div className="absolute inset-0 z-0 overflow-hidden bg-gray-950">
            {isImageLoading && !isSceneImageFailed && (
              <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-950/85 z-10 pointer-events-none transition-opacity">
                <div className="w-10 h-10 rounded-2xl bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center animate-pulse mb-2">
                  <Film className="w-5 h-5 text-indigo-400" />
                </div>
                <span className="text-[11px] font-medium text-gray-400">Loading scene visual...</span>
              </div>
            )}
            <AnimatePresence mode="wait">
              {!isSceneImageFailed && currentImageUrl ? (
                <motion.img
                  key={currentImageUrl}
                  src={currentImageUrl}
                  onLoad={() => setIsImageLoading(false)}
                  onError={() => {
                    setIsImageLoading(false);
                    // Try backend proxy first if direct image fetch failed
                    if (!currentImageUrl.includes("/ai/image-proxy") && currentImageUrl.startsWith("http")) {
                      const proxyUrl = `${API_BASE_URL}/ai/image-proxy?url=${encodeURIComponent(currentImageUrl)}`;
                      setImgSrcOverrides((prev) => ({ ...prev, [sceneKey]: proxyUrl }));
                    } else {
                      setFailedScenes((prev) => ({ ...prev, [sceneKey]: true }));
                    }
                  }}
                  alt="Scene Visual"
                  initial={{ scale: 1.0, opacity: 0.7 }}
                  animate={{ scale: isPlaying ? 1.2 : 1.06, opacity: 1 }}
                  transition={{
                    scale:   { duration: isPlaying ? 9 : 0.5, ease: "linear" },
                    opacity: { duration: 0.4 },
                  }}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-b from-indigo-950/80 via-slate-900 to-black text-center relative">
                  <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-3">
                    <Film className="w-7 h-7 text-indigo-400" />
                  </div>
                  <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-1">
                    Scene #{activeScene?.scene_number ?? 1}
                  </span>
                  <p className="text-xs text-gray-300 line-clamp-3 italic px-2">
                    &ldquo;{activeScene?.narration || activeScene?.subtitle || "Narrative scene"}&rdquo;
                  </p>
                </div>
              )}
            </AnimatePresence>

            {/* Cinematic gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/55 via-transparent to-black/92 pointer-events-none" />
          </div>

          {/* ── Top header badges ──────────────────────────────────────────── */}
          <div className="relative z-10 p-3 flex items-center justify-between">
            <span className="px-2.5 py-1 rounded-full bg-black/65 backdrop-blur text-[10px] font-bold text-white uppercase tracking-wider border border-white/10 flex items-center gap-1.5">
              <Film className="w-3 h-3 text-indigo-400" />
              Scene #{activeScene?.scene_number ?? 1}
            </span>
            <span className="camera-badge">
              {cameraLabel}
            </span>
          </div>

          {/* ── CME badge (if character detected) ─────────────────────────── */}
          {activeScene?.assets?.some((a: any) => a.metadata_json?.cme_injected) && (
            <div className="relative z-10 flex justify-center -mt-1">
              <span className="cme-badge text-[9px]">
                <Sparkles className="w-2.5 h-2.5" />
                CME Locked
              </span>
            </div>
          )}

          {/* ── Play/Pause hover overlay ───────────────────────────────────── */}
          <div className="relative z-10 flex-1 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <button
              onClick={togglePlay}
              className="w-14 h-14 rounded-full bg-indigo-600/90 hover:bg-indigo-500 text-white flex items-center justify-center shadow-2xl backdrop-blur border border-indigo-400/40 hover:scale-110 transition-transform"
            >
              {isPlaying ? (
                <Pause className="w-6 h-6" />
              ) : (
                <Play className="w-6 h-6 ml-0.5 fill-white" />
              )}
            </button>
          </div>

          {/* ── Subtitle rendering area ────────────────────────────────────── */}
          <div className="relative z-10">
            {renderSubtitle()}
          </div>

          {/* ── Voice activity waveform ────────────────────────────────────── */}
          <div className="relative z-10 px-3 pb-2 flex items-center justify-between text-[10px] text-gray-400">
            <div className="flex items-center gap-1.5">
              <Mic2
                className={`w-3 h-3 ${isPlaying ? "text-amber-400 voice-active-pulse" : "text-gray-600"}`}
              />
              <span className={isPlaying ? "text-white font-medium" : "text-gray-600"}>
                {voiceLang === "hi" ? "Hindi Voice" : "Indian English"} · {voiceGender}
              </span>
            </div>
            <div className="flex items-center gap-0.5">
              {[35, 70, 100, 55, 85, 40, 65].map((h, i) => (
                <div
                  key={i}
                  className="w-0.5 rounded-full bg-amber-400 transition-all duration-150"
                  style={{
                    height: isPlaying ? `${((h * (i + 1)) % 14) + 4}px` : "3px",
                    opacity: isPlaying ? 0.9 : 0.3,
                  }}
                />
              ))}
            </div>
          </div>
        </motion.div>
      </AnimatePresence>

      {/* ── Playback control bar ─────────────────────────────────────────────── */}
      <div className="mt-4 flex items-center gap-3">
        <button
          onClick={togglePlay}
          className="px-4 py-2 rounded-xl bg-[#0D1322] border border-gray-800 hover:border-indigo-700 text-white font-semibold text-xs flex items-center gap-2 transition-all shadow-md hover:shadow-indigo-900/30"
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5 text-amber-400" />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
              <span>Play Video</span>
            </>
          )}
        </button>

        {/* Canonical Aspect Ratio Badge */}
        <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl bg-[#0D1322] border border-gray-800 text-[10px] text-gray-300 font-medium">
          <span className="text-indigo-400 font-semibold">📱 9:16</span>
          <span className="text-gray-400">Vertical Shorts</span>
        </div>
      </div>

      {/* Scene count */}
      <p className="mt-2 text-[10px] text-gray-600">
        {scenes.length} scenes · {scenes.reduce((s, sc) => s + (sc.duration || 7), 0).toFixed(0)}s total
      </p>
    </div>
  );
}