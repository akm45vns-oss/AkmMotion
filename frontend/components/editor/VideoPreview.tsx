"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useEditorStore } from "@/lib/stores/editorStore";
import { Play, Pause, Sparkles, Film, Mic2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { API_BASE_URL } from "@/lib/api/client";

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
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return null;
    const voices = window.speechSynthesis.getVoices();
    const langCode = lang === "hi" ? "hi-IN" : "en-IN";

    const exactMatch = voices.find((v) => v.lang === langCode);
    if (exactMatch) return exactMatch;

    const broadMatch = voices.find((v) =>
      v.lang.startsWith(lang === "hi" ? "hi" : "en") &&
      (v.name.includes("India") || v.name.includes("Rishi") || v.name.includes("Heera") ||
       v.name.includes("Veena") || v.name.includes("Moira") || v.lang.includes("IN"))
    );
    return broadMatch ?? null;
  }, []);

  const playSceneAudio = useCallback(
    (scene: any, onEnd?: () => void) => {
      const audioAsset = scene?.assets?.find((a: any) => a.asset_type === "audio");
      const audioUrl = audioAsset?.url;

      if (audioUrl) {
        if (audioRef.current) {
          audioRef.current.pause();
          audioRef.current = null;
        }
        const audio = new Audio(audioUrl);
        audioRef.current = audio;

        const duration = scene.duration || 5;
        const text = scene.subtitle || scene.narration || "";
        const words = text.trim().split(/\s+/).filter(Boolean);
        const perWordMs = (duration * 1000) / Math.max(words.length, 1);

        let wordIdx = 0;
        const wordTimer = setInterval(() => {
          if (wordIdx < words.length) {
            setCurrentWordIndex(wordIdx);
            wordIdx++;
          } else {
            clearInterval(wordTimer);
          }
        }, perWordMs);

        audio.onended = () => {
          clearInterval(wordTimer);
          resetKaraoke();
          onEnd?.();
        };

        audio.onerror = () => {
          clearInterval(wordTimer);
          playSpeechFallback(scene, onEnd);
        };

        audio.play().catch(() => playSpeechFallback(scene, onEnd));
        return;
      }

      playSpeechFallback(scene, onEnd);
    },
    [setCurrentWordIndex, resetKaraoke]
  );

  const playSpeechFallback = (scene: any, onEnd?: () => void) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      onEnd?.();
      return;
    }
    window.speechSynthesis.cancel();

    const text = scene?.subtitle || scene?.narration || "";
    if (!text.trim()) {
      setTimeout(() => onEnd?.(), (scene?.duration || 4) * 1000);
      return;
    }

    const words = text.trim().split(/\s+/).filter(Boolean);
    const duration = scene?.duration || 4;
    const perWordMs = (duration * 1000) / Math.max(words.length, 1);

    let wordIdx = 0;
    const wordTimer = setInterval(() => {
      if (wordIdx < words.length) {
        setCurrentWordIndex(wordIdx);
        wordIdx++;
      } else {
        clearInterval(wordTimer);
      }
    }, perWordMs);

    const utt = new SpeechSynthesisUtterance(text);
    const voice = pickVoice(voiceLang, voiceGender);
    if (voice) utt.voice = voice;
    utt.rate = 1.0;
    utt.pitch = voiceGender === "female" ? 1.1 : 0.95;

    utt.onend = () => {
      clearInterval(wordTimer);
      resetKaraoke();
      onEnd?.();
    };

    utt.onerror = () => {
      clearInterval(wordTimer);
      resetKaraoke();
      onEnd?.();
    };

    utteranceRef.current = utt;
    window.speechSynthesis.speak(utt);
  };

  const playSequenceFrom = useCallback(
    (startIndex: number) => {
      if (startIndex >= scenes.length) {
        setIsPlaying(false);
        setActiveSceneIndex(0);
        return;
      }
      setActiveSceneIndex(startIndex);
      const scene = scenes[startIndex];
      if (scene) setActiveSceneId(scene.id);

      playSceneAudio(scene, () => {
        playSequenceFrom(startIndex + 1);
      });
    },
    [scenes, setActiveSceneIndex, setActiveSceneId, setIsPlaying, playSceneAudio]
  );

  const togglePlay = () => {
    if (isPlaying) {
      if (audioRef.current) audioRef.current.pause();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setIsPlaying(false);
      resetKaraoke();
    } else {
      setIsPlaying(true);
      playSequenceFrom(activeSceneIndex);
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

    // Default: karaoke word highlighting
    const words = rawSub.toUpperCase().split(" ");
    return (
      <motion.div
        key={rawSub}
        initial={{ y: 8, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="px-3 pb-3 text-center"
      >
        <div className="inline-block px-3.5 py-2 rounded-xl bg-black/85 backdrop-blur-md border border-white/15 shadow-xl">
          <p className="font-extrabold text-xs leading-snug tracking-wide uppercase flex flex-wrap justify-center gap-x-1.5 gap-y-0.5">
            {words.map((word: string, i: number) => (
              <span
                key={i}
                className={
                  i === currentWordIndex
                    ? "text-[#FDE047] scale-105 inline-block transition-transform"
                    : i % 2 === 0
                    ? "text-white"
                    : "text-neutral-300"
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

  const cameraLabel = activeScene?.camera_motion
    ? activeScene.camera_motion.replace(/_/g, " ").toUpperCase()
    : activeScene?.animation_style?.replace(/_/g, " ").toUpperCase() || "KEN BURNS";

  return (
    <div className="w-full flex flex-col items-center justify-center p-2 sm:p-4 relative">
      {/* ── Video Player Smartphone Container ───────────────────────────────── */}
      <div className="relative w-full max-w-[280px] xs:max-w-[300px] sm:max-w-[320px] aspect-[9/16] rounded-2xl overflow-hidden border border-[#24272E] bg-black shadow-2xl flex flex-col justify-between group">
        {/* Background visual image */}
        <div className="absolute inset-0 z-0 overflow-hidden bg-neutral-950">
          {isImageLoading && !isSceneImageFailed && (
            <div className="absolute inset-0 flex flex-col items-center justify-center bg-neutral-950/80 z-10 pointer-events-none">
              <div className="w-8 h-8 rounded-lg bg-[#1B1D21] border border-[#24272E] flex items-center justify-center animate-pulse mb-1.5">
                <Film className="w-4 h-4 text-[#E0693B]" />
              </div>
              <span className="text-[10px] text-neutral-400">Loading scene...</span>
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
                  if (!currentImageUrl.includes("/ai/image-proxy") && currentImageUrl.startsWith("http")) {
                    const proxyUrl = `${API_BASE_URL}/ai/image-proxy?url=${encodeURIComponent(currentImageUrl)}`;
                    setImgSrcOverrides((prev) => ({ ...prev, [sceneKey]: proxyUrl }));
                  } else {
                    setFailedScenes((prev) => ({ ...prev, [sceneKey]: true }));
                  }
                }}
                alt="Scene Visual"
                initial={{ scale: 1.0, opacity: 0.8 }}
                animate={{ scale: isPlaying ? 1.15 : 1.04, opacity: 1 }}
                transition={{
                  scale: { duration: isPlaying ? 8 : 0.4, ease: "linear" },
                  opacity: { duration: 0.3 },
                }}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center p-6 bg-gradient-to-b from-neutral-900 to-black text-center relative">
                <div className="w-12 h-12 rounded-xl bg-[#1B1D21] border border-[#24272E] flex items-center justify-center mb-2">
                  <Film className="w-5 h-5 text-neutral-400" />
                </div>
                <span className="text-[11px] font-semibold text-neutral-300 uppercase tracking-wider mb-1">
                  Scene #{activeScene?.scene_number ?? 1}
                </span>
                <p className="text-[11px] text-neutral-400 line-clamp-3 italic px-2">
                  &ldquo;{activeScene?.narration || activeScene?.subtitle || "Narrative scene"}&rdquo;
                </p>
              </div>
            )}
          </AnimatePresence>

          {/* Vignette Overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/85 pointer-events-none" />
        </div>

        {/* Top Badges */}
        <div className="relative z-10 p-2.5 flex items-center justify-between">
          <span className="px-2 py-0.5 rounded bg-black/75 backdrop-blur text-[10px] font-bold text-white border border-white/10 flex items-center gap-1">
            <Film className="w-3 h-3 text-[#E0693B]" />
            #{activeScene?.scene_number ?? 1}
          </span>
          <span className="camera-badge">
            {cameraLabel}
          </span>
        </div>

        {/* CME badge (if character injected) */}
        {activeScene?.assets?.some((a: any) => a.metadata_json?.cme_injected) && (
          <div className="relative z-10 flex justify-center -mt-1">
            <span className="cme-badge text-[9px]">
              <Sparkles className="w-2.5 h-2.5" />
              CME Locked
            </span>
          </div>
        )}

        {/* Center Hover Play Button */}
        <div className="relative z-10 flex-1 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <button
            onClick={togglePlay}
            className="w-12 h-12 rounded-full bg-[#E0693B] hover:bg-[#EB794D] text-white flex items-center justify-center shadow-xl hover:scale-105 active:scale-95 transition-transform"
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? (
              <Pause className="w-5 h-5" />
            ) : (
              <Play className="w-5 h-5 ml-0.5 fill-white" />
            )}
          </button>
        </div>

        {/* Bottom: Subtitles & Voice Indicator */}
        <div className="relative z-10 space-y-1">
          {renderSubtitle()}

          <div className="px-3 pb-2 flex items-center justify-between text-[10px] text-neutral-400">
            <div className="flex items-center gap-1.5">
              <Mic2
                className={`w-3 h-3 ${isPlaying ? "text-[#E0693B] voice-active-pulse" : "text-neutral-500"}`}
              />
              <span className={isPlaying ? "text-white font-medium" : "text-neutral-400"}>
                {voiceLang === "hi" ? "Hindi" : "Indian English"} · {voiceGender}
              </span>
            </div>
            <div className="flex items-center gap-0.5">
              {[30, 65, 95, 50, 80, 40, 60].map((h, i) => (
                <div
                  key={i}
                  className="w-0.5 rounded-full bg-[#E0693B] transition-all duration-150"
                  style={{
                    height: isPlaying ? `${((h * (i + 1)) % 12) + 4}px` : "3px",
                    opacity: isPlaying ? 0.9 : 0.25,
                  }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Playback Control Below Player */}
      <div className="mt-3 flex items-center gap-3 select-none">
        <button
          onClick={togglePlay}
          className="btn-secondary text-xs px-3.5 py-1.5 min-h-[36px] flex items-center gap-2"
        >
          {isPlaying ? (
            <>
              <Pause className="w-3.5 h-3.5 text-[#E0693B]" />
              <span>Pause</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 text-[#E0693B] fill-[#E0693B]" />
              <span>Play Video</span>
            </>
          )}
        </button>

        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[#141517] border border-[#24272E] text-[10px] text-neutral-300 font-medium">
          <span className="text-[#E0693B] font-semibold">📱 9:16</span>
          <span className="text-neutral-400">Vertical Shorts</span>
        </div>
      </div>
    </div>
  );
}