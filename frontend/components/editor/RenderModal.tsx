"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useEditorStore } from "@/lib/stores/editorStore";
import { Download, CheckCircle2, AlertCircle, X, Film, Volume2, Sparkles } from "lucide-react";

// ─── Word timing helper (mirrors backend logic) ───────────────────────────────
function computeWordTimings(text: string, duration: number) {
  const words = text.split(/\s+/).filter(Boolean);
  if (!words.length || duration <= 0) return [];
  const wOf = (w: string): number => { const n = w.replace(/[.,!?\u0964]/g, "").length; return n <= 2 ? 0.5 : n <= 5 ? 1.0 : n <= 8 ? 1.4 : 1.8; };
  const weights = words.map(wOf);
  const totalW = weights.reduce((a: number, b: number) => a + b, 0) || 1;
  const onset = 0.25;
  const avail = Math.max(duration - onset, 1);
  let t = onset;
  return words.map((word: string, i: number) => { const d = (weights[i] / totalW) * avail; const e = { word, start: t, end: t + d }; t += d; return e; });
}

interface RenderModalProps {
  projectId: string;
  onClose: () => void;
}

const FALLBACK_IMGS = [
  "https://picsum.photos/seed/fallback1/600/960",
  "https://picsum.photos/seed/fallback2/600/960",
  "https://picsum.photos/seed/fallback3/600/960",
  "https://picsum.photos/seed/fallback4/600/960",
  "https://picsum.photos/seed/fallback5/600/960",
  "https://picsum.photos/seed/fallback6/600/960",
  "https://picsum.photos/seed/fallback7/600/960",
  "https://picsum.photos/seed/fallback8/600/960",
];

const W = 540, H = 960;

export default function RenderModal({ projectId, onClose }: RenderModalProps) {
  const { scenes, subtitleStyle, voiceLang, voiceGender, stylePreset } = useEditorStore();
  const [phase, setPhase] = useState<"rendering" | "done" | "error">("rendering");
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("Initializing Video Engine...");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [blobSize, setBlobSize] = useState(0);
  const [errorMsg, setErrorMsg] = useState("");
  const [currentSceneIdx, setCurrentSceneIdx] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const cancelRef = useRef(false);

  const fetchIndianTTSAudio = async (text: string, audioCtx: AudioContext): Promise<AudioBuffer | null> => {
    try {
      const response = await fetch("http://localhost:8000/api/v1/ai/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: voiceLang, gender: voiceGender }),
      });
      if (!response.ok) return null;
      const arrayBuffer = await response.arrayBuffer();
      return await audioCtx.decodeAudioData(arrayBuffer);
    } catch (err) {
      console.error("Local TTS fetch error:", err);
      return null;
    }
  };

  const drawFrame = useCallback((
    ctx: CanvasRenderingContext2D,
    img: HTMLImageElement | null,
    scene: any,
    t: number,           // 0..1 progress through this scene
    wordTimings: { word: string; start: number; end: number }[],
    elapsedTime: number  // seconds elapsed within this scene
  ) => {
    const scale = 1.0 + t * 0.09;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#090D16";
    ctx.fillRect(0, 0, W, H);

    if (img && img.complete && img.naturalWidth > 0) {
      const dw = W * scale, dh = H * scale;
      ctx.drawImage(img, (W - dw) / 2, (H - dh) / 2, dw, dh);
    }

    // Cinematic letterbox bars for Cinematic style
    if (stylePreset === "Cinematic") {
      const barH = Math.round(H * 0.06);
      ctx.fillStyle = "rgba(0,0,0,0.92)";
      ctx.fillRect(0, 0, W, barH);
      ctx.fillRect(0, H - barH, W, barH);
    }

    // Gradient overlay
    const g = ctx.createLinearGradient(0, 0, 0, H);
    g.addColorStop(0, "rgba(0,0,0,0.5)");
    g.addColorStop(0.4, "rgba(0,0,0,0.05)");
    g.addColorStop(1, "rgba(0,0,0,0.92)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);

    // Scene number badge
    ctx.save();
    ctx.fillStyle = "rgba(0,0,0,0.75)";
    ctx.beginPath();
    ctx.roundRect(16, 18, 118, 30, 8);
    ctx.fill();
    ctx.font = "bold 13px Arial";
    ctx.fillStyle = "#FFFFFF";
    ctx.textAlign = "left";
    ctx.fillText(`SCENE #${scene.scene_number}`, 26, 37);
    ctx.restore();

    // ── Subtitle rendering (style-aware) ───────────────────────────────────
    const rawSub = (scene.subtitle || "").replace(/\*\*/g, "").trim();
    if (rawSub) {
      if (subtitleStyle === "minimal") {
        // Minimal: small white text, no background box
        ctx.save();
        ctx.textAlign = "center";
        ctx.font = "500 15px Arial";
        ctx.fillStyle = "rgba(255,255,255,0.88)";
        ctx.shadowColor = "rgba(0,0,0,0.9)";
        ctx.shadowBlur = 6;
        ctx.fillText(rawSub.slice(0, 60), W / 2, H - 56);
        ctx.restore();

      } else if (subtitleStyle === "karaoke") {
        // Karaoke: per-word highlight based on elapsed time
        const words = rawSub.split(" ");
        const activeIdx = wordTimings.findIndex(
          (wt) => elapsedTime >= wt.start && elapsedTime < wt.end
        );
        const spokenIdx = wordTimings.findLastIndex((wt) => elapsedTime >= wt.end);

        // Box background
        const boxH = 62;
        ctx.save();
        ctx.fillStyle = "rgba(0,0,0,0.84)";
        ctx.beginPath();
        ctx.roundRect(16, H - 76 - boxH, W - 32, boxH, 12);
        ctx.fill();

        // Measure each word to position inline
        ctx.font = "bold 18px Arial";
        const wordWidths = words.map((w: string) => ctx.measureText(w + " ").width);
        const totalWidth = wordWidths.reduce((a: number, b: number) => a + b, 0);
        let x = (W - totalWidth) / 2;
        const y = H - 76 - boxH + 36;

        words.forEach((word: string, i: number) => {
          if (i === activeIdx) {
            ctx.fillStyle = "#FFD700";
            ctx.shadowColor = "rgba(255,215,0,0.7)";
            ctx.shadowBlur = 10;
          } else if (i <= spokenIdx) {
            ctx.fillStyle = "rgba(255,255,255,0.38)";
            ctx.shadowBlur = 0;
          } else {
            ctx.fillStyle = "rgba(255,255,255,0.8)";
            ctx.shadowBlur = 0;
          }
          ctx.fillText(word, x, y);
          x += wordWidths[i];
        });
        ctx.restore();

      } else {
        // Default yellow-cyan: alternate word colors
        const words = rawSub.toUpperCase().split(" ");
        const line1 = words.slice(0, 5).join(" ");
        const line2 = words.slice(5, 10).join(" ");
        const boxH = line2 ? 88 : 54;
        ctx.save();
        ctx.fillStyle = "rgba(0,0,0,0.86)";
        ctx.beginPath();
        ctx.roundRect(16, H - 62 - boxH, W - 32, boxH, 12);
        ctx.fill();
        ctx.textAlign = "center";
        ctx.font = "bold 21px Arial";
        ctx.fillStyle = "#FFD700";
        ctx.fillText(line1, W / 2, H - 62 - boxH + 34);
        if (line2) {
          ctx.fillStyle = "#00E5FF";
          ctx.fillText(line2, W / 2, H - 62 - boxH + 66);
        }
        ctx.restore();
      }
    }

    // Aurora shimmer progress bar
    ctx.save();
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.fillRect(0, H - 12, W, 12);
    const grad = ctx.createLinearGradient(0, 0, W, 0);
    grad.addColorStop(0,   "#6C63FF");
    grad.addColorStop(0.5, "#A855F7");
    grad.addColorStop(1,   "#06B6D4");
    ctx.fillStyle = grad;
    ctx.fillRect(0, H - 12, W * t, 12);
    ctx.restore();
  }, [subtitleStyle, stylePreset]);

  const startRender = useCallback(async () => {
    cancelRef.current = false;
    setPhase("rendering");
    setProgress(0);
    setDownloadUrl(null);
    setBlobSize(0);
    setCurrentSceneIdx(0);

    if (!scenes || scenes.length === 0) {
      setErrorMsg("No scenes found to render.");
      setPhase("error");
      return;
    }

    await new Promise((r) => requestAnimationFrame(r));

    const canvas = canvasRef.current;
    if (!canvas) {
      setErrorMsg("Canvas surface missing.");
      setPhase("error");
      return;
    }

    const ctx = canvas.getContext("2d");
    if (!ctx) {
      setErrorMsg("Canvas 2D context error.");
      setPhase("error");
      return;
    }

    // Audio Context & Destination
    let audioCtx: AudioContext | null = null;
    let audioDest: MediaStreamAudioDestinationNode | null = null;
    try {
      audioCtx = new AudioContext({ sampleRate: 44100 });
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }
      audioDest = audioCtx.createMediaStreamDestination();
    } catch (e) {
      console.error("AudioContext setup error:", e);
    }

    const videoStream = canvas.captureStream(24);
    const tracks: MediaStreamTrack[] = [...videoStream.getVideoTracks()];
    if (audioDest) {
      tracks.push(...audioDest.stream.getAudioTracks());
    }

    const recorderStream = new MediaStream(tracks);
    const codec = [
      "video/webm;codecs=vp9,opus",
      "video/webm;codecs=vp8,opus",
      "video/webm",
    ].find((c) => MediaRecorder.isTypeSupported(c)) || "video/webm";

    const recorder = new MediaRecorder(recorderStream, {
      mimeType: codec,
      videoBitsPerSecond: 3_500_000,
    });

    const chunks: Blob[] = [];
    recorder.ondataavailable = (e) => {
      if (e.data?.size > 0) chunks.push(e.data);
    };

    const donePromise = new Promise<void>((res) => {
      recorder.onstop = () => res();
    });

    recorder.start(200);
    const N = scenes.length;

    // ── Helper: load image via fetch → blob URL (prevents canvas CORS taint) ─
    const loadImageSafe = async (url: string): Promise<HTMLImageElement> => {
      const img = new Image();
      // Try fetching as blob first (avoids taint entirely)
      try {
        const resp = await fetch(url, { mode: "cors" });
        if (resp.ok) {
          const blob = await resp.blob();
          img.src = URL.createObjectURL(blob);
          await new Promise<void>((res, rej) => {
            img.onload = () => res();
            img.onerror = rej;
          });
          return img;
        }
      } catch (_) {/* fall through */}
      // Fallback: draw a solid gradient onto a temp canvas and use that
      const fc = document.createElement("canvas");
      fc.width = 540; fc.height = 960;
      const fctx = fc.getContext("2d")!;
      const g = fctx.createLinearGradient(0, 0, 0, 960);
      g.addColorStop(0, "#1a1a2e"); g.addColorStop(1, "#16213e");
      fctx.fillStyle = g;
      fctx.fillRect(0, 0, 540, 960);
      img.src = fc.toDataURL();
      await new Promise<void>((res) => { img.onload = () => res(); });
      return img;
    };

    // Phase 1: Synthesize & Load Indian Accent Audio + CME Scene Images
    const audioBuffers: (AudioBuffer | null)[] = [];
    const images: HTMLImageElement[] = [];

    for (let i = 0; i < N; i++) {
      if (cancelRef.current) break;
      const scene = scenes[i];
      const stepPct = Math.floor((i / N) * 25);
      setProgress(stepPct);
      setStatusText(`Voice & Image Scene #${scene.scene_number} (${i + 1}/${N})...`);

      // Synthesize Speech Audio
      const narrationText = (scene.narration || "").replace(/\*\*/g, "").trim();
      let buf: AudioBuffer | null = null;
      if (narrationText && audioCtx) {
        buf = await fetchIndianTTSAudio(narrationText, audioCtx);
      }
      audioBuffers.push(buf);

      // Load Image — use fetch+blob to avoid canvas CORS taint
      const imgAsset = scene?.assets?.find((a: any) => a.asset_type === "image");
      const storedUrl = imgAsset?.url || "";
      const isBadUrl =
        !storedUrl ||
        storedUrl.includes("unsplash.com") ||
        storedUrl.includes("picsum.photos") ||
        storedUrl.includes("placeholder");

      const rawPrompt = (scene.image_prompt || narrationText || "").replace(/\*\*/g, "").trim();
      const promptText = rawPrompt || `9:16 vertical 8k render scene ${scene.scene_number || 1}`;
      const seed = ((scene.scene_number || 1) * 73 + 1234) % 99999;
      const pollinationsUrl = `https://image.pollinations.ai/prompt/${encodeURIComponent(promptText)}?width=540&height=960&nologo=true&seed=${seed}`;
      const imageUrl = isBadUrl ? pollinationsUrl : storedUrl;

      const img = await loadImageSafe(imageUrl);
      images.push(img);
    }

    // Phase 2: Render Frames & Synchronize Voice Audio
    for (let i = 0; i < N; i++) {
      if (cancelRef.current) break;
      const scene = scenes[i];
      const img = images[i];
      const buf = audioBuffers[i];

      let sceneDuration = Math.max(scene.duration || 7, 5);
      if (buf) {
        sceneDuration = Math.max(sceneDuration, buf.duration + 0.3);
      }

      // Compute per-word timings for karaoke subtitle burning
      const narTextForTimings = (scene.narration || scene.subtitle || "").replace(/\*\*/g, "").trim();
      const sceneWordTimings = computeWordTimings(narTextForTimings, sceneDuration);

      setCurrentSceneIdx(i);
      setStatusText(`Rendering Scene #${scene.scene_number} (${i + 1}/${N})...`);

      // Play audio stream into MediaRecorder destination
      if (buf && audioCtx && audioDest && audioCtx.state === "running") {
        const source = audioCtx.createBufferSource();
        source.buffer = buf;
        source.connect(audioDest);
        source.start();
      }

      const fps = 24;
      const totalFrames = Math.ceil(sceneDuration * fps);

      for (let f = 0; f < totalFrames; f++) {
        if (cancelRef.current) break;
        const t = f / totalFrames;
        const elapsedTime = t * sceneDuration;
        drawFrame(ctx, img, scene, t, sceneWordTimings, elapsedTime);
        const pct = Math.floor(25 + ((i * totalFrames + f) / (N * totalFrames)) * 73);
        setProgress(pct);
        await new Promise((r) => setTimeout(r, 1000 / fps));
      }
    }

    if (cancelRef.current) {
      recorder.stop();
      if (audioCtx) await audioCtx.close();
      return;
    }

    setStatusText("Finalizing Video File...");
    setProgress(99);
    await new Promise((r) => setTimeout(r, 600));
    recorder.stop();
    await donePromise;

    if (audioCtx) await audioCtx.close();

    const blob = new Blob(chunks, { type: codec });
    if (blob.size === 0) {
      setErrorMsg("Video output was 0 bytes. Please try re-rendering.");
      setPhase("error");
      return;
    }

    const url = URL.createObjectURL(blob);
    setDownloadUrl(url);
    setBlobSize(blob.size);
    setProgress(100);
    setPhase("done");
  }, [scenes, drawFrame]);

  useEffect(() => {
    const t = setTimeout(startRender, 300);
    return () => {
      clearTimeout(t);
      cancelRef.current = true;
    };
  }, []);

  const fmt = (b: number) =>
    b < 1024
      ? `${b} B`
      : b < 1024 ** 2
      ? `${(b / 1024).toFixed(1)} KB`
      : `${(b / 1024 ** 2).toFixed(1)} MB`;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-md p-6 rounded-3xl bg-[#0D1322] border border-gray-800 shadow-2xl relative flex flex-col items-center">
        {/* Close Button */}
        <button
          onClick={() => {
            cancelRef.current = true;
            onClose();
          }}
          className="absolute top-4 right-4 z-10 p-2 rounded-full text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center mb-4">
          <h2 className="text-lg font-bold text-white flex items-center justify-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>Rendering Studio Shorts Video</span>
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Generating 9:16 vertical video with Indian voiceover narration
          </p>
        </div>

        {/* Compact Smartphone Vertical Preview Frame */}
        <div className="relative w-[214px] h-[380px] rounded-2xl overflow-hidden border-2 border-gray-800 bg-black shadow-2xl flex items-center justify-center my-2">
          <canvas
            ref={canvasRef}
            width={W}
            height={H}
            className="w-full h-full object-cover block"
          />

          {phase === "done" && (
            <div className="absolute inset-0 bg-black/80 backdrop-blur-sm flex flex-col items-center justify-center gap-2 p-4 text-center">
              <CheckCircle2 className="w-12 h-12 text-emerald-400" />
              <div>
                <h3 className="text-white font-bold text-base">Video Ready!</h3>
                <p className="text-gray-300 text-[11px] mt-1">
                  {scenes.length} Scenes · <span className="text-emerald-400 font-bold">{fmt(blobSize)}</span>
                </p>
              </div>
            </div>
          )}

          {phase === "error" && (
            <div className="absolute inset-0 bg-black/85 backdrop-blur-sm flex flex-col items-center justify-center gap-2 p-4 text-center">
              <AlertCircle className="w-10 h-10 text-red-400" />
              <p className="text-white font-bold text-sm">Render Failed</p>
              <p className="text-red-300 text-[11px]">{errorMsg}</p>
            </div>
          )}
        </div>

        {/* Bottom Progress & Download Controls */}
        <div className="w-full mt-4 space-y-3">
          {phase === "rendering" && (
            <>
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-indigo-400 flex items-center gap-1.5 truncate max-w-[260px]">
                  <Volume2 className="w-3.5 h-3.5 animate-pulse text-emerald-400 flex-shrink-0" />
                  <span className="truncate">{statusText}</span>
                </span>
                <span className="text-white font-bold">{progress}%</span>
              </div>
              <div className="w-full h-2 bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-[11px] text-gray-400 text-center">
                Processing Scene {currentSceneIdx + 1}/{scenes.length}
              </p>
            </>
          )}

          {phase === "done" && (
            <div className="space-y-2">
              <a
                href={downloadUrl!}
                download={`akmmotion_${projectId.slice(0, 8)}.webm`}
                className="block w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-sm text-center shadow-xl transition-all"
              >
                <div className="flex items-center justify-center gap-2">
                  <Download className="w-4 h-4" />
                  <span>Download Video ({fmt(blobSize)})</span>
                </div>
              </a>
              <button
                onClick={startRender}
                className="w-full py-2 rounded-xl bg-gray-800 text-xs text-gray-300 hover:text-white transition-colors"
              >
                Re-render Video
              </button>
            </div>
          )}

          {phase === "error" && (
            <button
              onClick={startRender}
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}