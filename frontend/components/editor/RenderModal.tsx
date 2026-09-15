"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { useEditorStore } from "@/lib/stores/editorStore";
import { Download, CheckCircle2, AlertCircle, X, Film, Loader2 } from "lucide-react";
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
          setErrorMsg("Rendering is taking longer than expected. Please check your project dashboard.");
          setPhase("error");
          return;
        }

        try {
          const job = await renderApi.getStatus(jobId);
          setCurrentJob(job);

          if (job.status === "processing" || job.status === "pending") {
            setProgress(job.progress || 10);
            if (job.progress < 20) {
              setStatusText("Preparing visual scenes & audio narration...");
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

  const firstSceneImg = scenes?.[0]?.assets?.find((a: any) => a.asset_type === "image")?.url;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="w-full max-w-md max-h-[92vh] overflow-y-auto p-5 sm:p-6 rounded-xl bg-[#151616] border border-[#292A29] shadow-2xl relative flex flex-col items-center">
        {/* Close Button */}
        <button
          onClick={() => {
            isCancelledRef.current = true;
            cleanupPolling();
            onClose();
          }}
          className="absolute top-3.5 right-3.5 z-10 p-2 rounded-lg text-[#A9A49B] hover:text-[#F5F1E8] hover:bg-[#1B1C1C] transition-colors"
          aria-label="Close modal"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="text-center mb-3">
          <h2 className="text-base font-bold text-[#F5F1E8] flex items-center justify-center gap-1.5 font-display">
            <span>Video Export Studio</span>
          </h2>
          <p className="text-[11px] text-[#A9A49B] mt-0.5">
            1080×1920 MP4 H.264 vertical video with burned-in subtitles
          </p>
        </div>

        {/* Smartphone Vertical Preview Frame */}
        <div className="relative w-[200px] h-[355px] rounded-lg overflow-hidden border border-[#292A29] bg-black shadow-xl flex items-center justify-center my-2">
          {phase === "done" && downloadUrl ? (
            <video
              src={downloadUrl}
              controls
              autoPlay
              loop
              playsInline
              className="w-full h-full object-cover rounded-lg"
            />
          ) : phase === "rendering" ? (
            <div className="relative w-full h-full flex flex-col items-center justify-center bg-black p-4 text-center">
              {firstSceneImg ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={firstSceneImg}
                  alt="Scene preview"
                  className="absolute inset-0 w-full h-full object-cover opacity-20 filter blur-[1px]"
                />
              ) : null}
              <div className="relative z-10 flex flex-col items-center gap-2.5">
                <div className="p-3 rounded-lg bg-[#E76536]/10 border border-[#E76536]/25">
                  <Loader2 className="w-6 h-6 text-[#E76536] animate-spin" />
                </div>
                <div className="space-y-0.5">
                  <span className="text-xs font-semibold text-[#F5F1E8]">Encoding MP4</span>
                  <p className="text-[10px] text-[#A9A49B] font-mono">
                    {scenes.length} Scenes · 30 FPS
                  </p>
                </div>
              </div>
            </div>
          ) : (
            <div className="absolute inset-0 bg-black/90 flex flex-col items-center justify-center gap-2 p-4 text-center">
              <AlertCircle className="w-8 h-8 text-[#C95C5C]" />
              <p className="text-[#F5F1E8] font-bold text-xs">Render Failed</p>
              <p className="text-[#C95C5C] text-[10px] line-clamp-3">{errorMsg}</p>
            </div>
          )}
        </div>

        {/* Phase Status & Progress */}
        <div className="w-full space-y-3 mt-3 text-center">
          {phase === "rendering" && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-[11px]">
                <span className="text-[#A9A49B]">{statusText}</span>
                <span className="text-[#E76536] font-mono font-semibold">{progress}%</span>
              </div>
              <div className="w-full h-1.5 rounded-full bg-[#1B1C1C] border border-[#292A29] overflow-hidden">
                <div
                  className="h-full bg-[#E76536] transition-all duration-300"
                  style={{ width: `${Math.max(progress, 5)}%` }}
                />
              </div>
            </div>
          )}

          {phase === "done" && (
            <div className="space-y-2">
              <div className="flex items-center justify-center gap-1.5 text-[#4FAE7B] text-xs font-semibold">
                <CheckCircle2 className="w-4 h-4" />
                <span>Ready for Download</span>
              </div>
              {downloadUrl && (
                <a
                  href={downloadUrl}
                  download={`akmmotion_${projectId}.mp4`}
                  className="btn-primary w-full py-2.5 text-xs flex items-center justify-center gap-2 shadow-sm touch-target"
                >
                  <Download className="w-4 h-4" />
                  <span>Download 1080×1920 MP4</span>
                </a>
              )}
            </div>
          )}

          {phase === "error" && (
            <div className="space-y-2">
              <button
                onClick={startRender}
                className="btn-primary w-full py-2.5 text-xs flex items-center justify-center gap-2 shadow-sm"
              >
                <span>Retry Render</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}