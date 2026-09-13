"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useEditorStore } from "@/lib/stores/editorStore";
import { Download, CheckCircle2, AlertCircle, X, Film, Sparkles, Loader2 } from "lucide-react";
import { renderApi, RenderJob } from "@/lib/api/render";

interface RenderModalProps {
  projectId: string;
  onClose: () => void;
}

export default function RenderModal({ projectId, onClose }: RenderModalProps) {
  const { scenes } = useEditorStore();
  const [phase, setPhase] = useState<"rendering" | "done" | "error">("rendering");
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("Initializing Server Render Engine...");
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [currentJob, setCurrentJob] = useState<RenderJob | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const isCancelledRef = useRef(false);

  const cleanupPolling = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
  }, []);

  const pollJobStatus = useCallback(
    (jobId: string) => {
      cleanupPolling();
      let attempts = 0;
      const MAX_ATTEMPTS = 180; // 4.5 minutes maximum polling timeout

      pollIntervalRef.current = setInterval(async () => {
        if (isCancelledRef.current) {
          cleanupPolling();
          return;
        }

        attempts += 1;
        if (attempts > MAX_ATTEMPTS) {
          cleanupPolling();
          setErrorMsg("Rendering is taking longer than usual. Please check your project dashboard.");
          setPhase("error");
          return;
        }

        try {
          const job = await renderApi.getStatus(jobId);
          setCurrentJob(job);

          if (job.status === "processing" || job.status === "pending") {
            setProgress(job.progress || 10);
            if (job.progress < 20) {
              setStatusText("Preparing visual scenes & audio tracks...");
            } else if (job.progress < 70) {
              setStatusText(`Rendering 9:16 vertical MP4 video (${job.progress}%)...`);
            } else {
              setStatusText("Stitching scenes & finalizing H.264 MP4 encode...");
            }
          } else if (job.status === "completed") {
            cleanupPolling();
            setProgress(100);
            setStatusText("Video successfully rendered!");
            const finalUrl = job.video_url || renderApi.getVideoUrl(job.id);
            setDownloadUrl(finalUrl);
            setPhase("done");
          } else if (job.status === "failed") {
            cleanupPolling();
            setPhase("error");
            setErrorMsg(job.error_message || "Video rendering failed. Please try again.");
          }
        } catch (err: any) {
          console.error("Failed to poll render status:", err);
          // Only fail after 5 consecutive errors to tolerate transient network hiccups
          if (attempts > 5 && !currentJob) {
            cleanupPolling();
            setPhase("error");
            setErrorMsg("Network error checking render status. Please retry.");
          }
        }
      }, 1500);
    },
    [cleanupPolling, currentJob]
  );

  const startRender = useCallback(async () => {
    isCancelledRef.current = false;
    cleanupPolling();
    setPhase("rendering");
    setProgress(5);
    setStatusText("Submitting render job to server...");
    setDownloadUrl(null);
    setErrorMsg("");

    try {
      const job = await renderApi.start(projectId);
      setCurrentJob(job);

      if (job.status === "completed") {
        setProgress(100);
        setStatusText("Video ready!");
        const finalUrl = job.video_url || renderApi.getVideoUrl(job.id);
        setDownloadUrl(finalUrl);
        setPhase("done");
        return;
      }

      setProgress(job.progress || 10);
      setStatusText("Render job queued on server...");
      pollJobStatus(job.id);
    } catch (err: any) {
      console.error("Failed to start render:", err);
      setPhase("error");
      const errorDetail =
        err?.response?.data?.detail ||
        err?.message ||
        "Could not initiate video render. Please verify project scenes.";
      setErrorMsg(typeof errorDetail === "string" ? errorDetail : "Failed to initiate render.");
    }
  }, [projectId, cleanupPolling, pollJobStatus]);

  useEffect(() => {
    startRender();
    return () => {
      isCancelledRef.current = true;
      cleanupPolling();
    };
  }, [startRender, cleanupPolling]);

  // First scene preview image if available
  const firstSceneImg = scenes?.[0]?.assets?.find((a: any) => a.asset_type === "image")?.url;

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-md p-6 rounded-3xl bg-[#0D1322] border border-gray-800 shadow-2xl relative flex flex-col items-center">
        {/* Close Button */}
        <button
          onClick={() => {
            isCancelledRef.current = true;
            cleanupPolling();
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
            <span>Server Video Rendering Studio</span>
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">
            Real 1080x1920 MP4 H.264 encode with narration & subtitles
          </p>
        </div>

        {/* Compact Smartphone Vertical Preview Frame */}
        <div className="relative w-[214px] h-[380px] rounded-2xl overflow-hidden border-2 border-gray-800 bg-black shadow-2xl flex items-center justify-center my-2">
          {phase === "done" && downloadUrl ? (
            <video
              src={downloadUrl}
              controls
              autoPlay
              loop
              playsInline
              className="w-full h-full object-cover rounded-2xl"
            />
          ) : phase === "rendering" ? (
            <div className="relative w-full h-full flex flex-col items-center justify-center bg-gray-950 p-4 text-center">
              {firstSceneImg ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={firstSceneImg}
                  alt="Scene preview"
                  className="absolute inset-0 w-full h-full object-cover opacity-25 filter blur-[1px]"
                />
              ) : null}
              <div className="relative z-10 flex flex-col items-center gap-3">
                <div className="p-3.5 rounded-full bg-indigo-500/20 border border-indigo-500/30">
                  <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
                </div>
                <div className="space-y-1">
                  <span className="text-xs font-semibold text-white">Encoding MP4</span>
                  <p className="text-[10px] text-gray-400">
                    {scenes.length} Scene{scenes.length === 1 ? "" : "s"}
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="absolute inset-0 bg-black/85 backdrop-blur-sm flex flex-col items-center justify-center gap-2 p-4 text-center">
              <AlertCircle className="w-10 h-10 text-red-400" />
              <p className="text-white font-bold text-sm">Render Failed</p>
              <p className="text-red-300 text-[11px] line-clamp-3">{errorMsg}</p>
            </div>
          )}
        </div>

        {/* Bottom Progress & Download Controls */}
        <div className="w-full mt-4 space-y-3">
          {phase === "rendering" && (
            <>
              <div className="flex items-center justify-between text-xs font-medium">
                <span className="text-indigo-400 flex items-center gap-1.5 truncate max-w-[260px]">
                  <Film className="w-3.5 h-3.5 animate-pulse text-emerald-400 flex-shrink-0" />
                  <span className="truncate">{statusText}</span>
                </span>
                <span className="text-white font-bold">{progress}%</span>
              </div>
              <div className="w-full h-2 bg-gray-900 rounded-full overflow-hidden border border-gray-800">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-emerald-400 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-[11px] text-gray-400 text-center">
                Processing {scenes.length} Scenes on Server Engine
              </p>
            </>
          )}

          {phase === "done" && downloadUrl && (
            <div className="space-y-2">
              <a
                href={downloadUrl}
                download={`akmmotion_${projectId.slice(0, 8)}.mp4`}
                className="block w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 text-white font-bold text-sm text-center shadow-xl transition-all"
              >
                <div className="flex items-center justify-center gap-2">
                  <Download className="w-4 h-4" />
                  <span>Download MP4 Video</span>
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
              className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition-colors"
            >
              Try Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}