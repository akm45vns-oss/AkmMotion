"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useEditorStore } from "@/lib/stores/editorStore";
import { projectsApi } from "@/lib/api/projects";
import { scenesApi } from "@/lib/api/scenes";
import { aiApi } from "@/lib/api/ai";
import ToolBar from "@/components/editor/ToolBar";
import VideoPreview from "@/components/editor/VideoPreview";
import SceneEditor from "@/components/editor/SceneEditor";
import Timeline from "@/components/editor/Timeline";
import RenderModal from "@/components/editor/RenderModal";
import { Loader2, Sparkles, Sliders, Film, Layers } from "lucide-react";

export default function EditorPage() {
  const params = useParams();
  const projectId = params.id as string;

  const {
    setProject,
    setScenes,
    activeSceneId,
    setActiveSceneId,
    scenes,
    isLoading,
    setIsLoading,
    project,
  } = useEditorStore();

  const [isRenderModalOpen, setIsRenderModalOpen] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [mobileTab, setMobileTab] = useState<"preview" | "inspector" | "timeline">("preview");

  const fetchProjectAndScenes = useCallback(async () => {
    if (!projectId) return null;
    try {
      const [projectData, scenesData] = await Promise.all([
        projectsApi.getById(projectId),
        scenesApi.getByProjectId(projectId),
      ]);
      setProject(projectData);
      setScenes(scenesData);
      if (scenesData.length > 0) {
        setActiveSceneId(scenesData[0].id);
      }
      return { projectData, scenesData };
    } catch (err) {
      console.error("Failed to load project editor data:", err);
      return null;
    }
  }, [projectId, setProject, setScenes, setActiveSceneId]);

  const handleGenerateScenes = async () => {
    if (!projectId || isGenerating) return;
    setIsGenerating(true);
    try {
      await aiApi.generatePipeline(projectId);
      const freshScenes = await scenesApi.getByProjectId(projectId);
      setScenes(freshScenes);
      if (freshScenes.length > 0) {
        setActiveSceneId(freshScenes[0].id);
      }
    } catch (err: any) {
      console.error("Pipeline generation error:", err);
      alert(err.response?.data?.detail || "Failed to generate scenes. Please verify script content.");
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    if (!projectId) return;

    setIsLoading(true);
    fetchProjectAndScenes()
      .then((res) => {
        if (res && res.scenesData.length === 0 && res.projectData?.script?.content) {
          handleGenerateScenes();
        }
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [projectId, fetchProjectAndScenes]);

  const activeScene = scenes.find((s) => s.id === activeSceneId) || scenes[0];

  if (isLoading) {
    return (
      <div className="h-screen w-full flex items-center justify-center bg-[#0C0D0E]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-7 h-7 text-[#E0693B] animate-spin" />
          <p className="text-xs font-medium text-neutral-400">Loading Video Studio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex flex-col bg-[#0C0D0E] text-[#F2F2F3] overflow-hidden">
      {/* Top Studio Toolbar */}
      <ToolBar
        onRenderClick={() => setIsRenderModalOpen(true)}
        onGenerateClick={handleGenerateScenes}
        isGenerating={isGenerating}
      />

      {/* Mobile Workspace Mode Switcher (Visible only on < lg screens) */}
      <div className="lg:hidden border-b border-[#24272E] bg-[#141517] px-3 py-1.5 flex items-center justify-around text-xs select-none">
        <button
          onClick={() => setMobileTab("preview")}
          className={`flex items-center gap-1.5 py-1 px-3 rounded-lg font-medium transition-colors ${
            mobileTab === "preview"
              ? "bg-[#1B1D21] text-[#E0693B] font-semibold border border-[#333742]"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          <Film className="w-3.5 h-3.5" />
          <span>Player</span>
        </button>

        <button
          onClick={() => setMobileTab("inspector")}
          className={`flex items-center gap-1.5 py-1 px-3 rounded-lg font-medium transition-colors ${
            mobileTab === "inspector"
              ? "bg-[#1B1D21] text-[#E0693B] font-semibold border border-[#333742]"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Inspector</span>
        </button>

        <button
          onClick={() => setMobileTab("timeline")}
          className={`flex items-center gap-1.5 py-1 px-3 rounded-lg font-medium transition-colors ${
            mobileTab === "timeline"
              ? "bg-[#1B1D21] text-[#E0693B] font-semibold border border-[#333742]"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Timeline</span>
        </button>
      </div>

      {/* ── Main Studio Viewport ────────────────────────────────────────────── */}
      <div className="flex-1 flex overflow-hidden">
        {/* Center Video Preview Viewport */}
        <div
          className={`flex-1 border-r border-[#24272E] p-2 sm:p-4 flex flex-col justify-center items-center overflow-y-auto ${
            mobileTab !== "preview" ? "hidden lg:flex" : "flex"
          }`}
        >
          {isGenerating ? (
            <div className="w-full max-w-sm p-6 rounded-xl bg-[#141517] border border-[#24272E] text-center space-y-3 shadow-xl">
              <div className="w-12 h-12 mx-auto rounded-xl bg-[#E0693B]/10 border border-[#E0693B]/25 flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-[#E0693B] animate-spin" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-[#F2F2F3]">AI Director at Work</h3>
                <p className="text-xs text-neutral-400 leading-relaxed">
                  Splitting script into vertical scenes, synthesizing Indian voiceover, and preparing visual assets...
                </p>
              </div>
            </div>
          ) : scenes.length === 0 ? (
            <div className="w-full max-w-sm p-6 rounded-xl bg-[#141517] border border-[#24272E] text-center space-y-4 shadow-xl">
              <div className="w-12 h-12 mx-auto rounded-xl bg-[#1B1D21] border border-[#24272E] flex items-center justify-center text-neutral-400">
                <Film className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-[#F2F2F3]">No Scenes Generated Yet</h3>
                <p className="text-xs text-neutral-400 leading-relaxed">
                  Your script is saved. Click below to generate 9:16 vertical scenes and audio narration.
                </p>
              </div>
              <button
                onClick={handleGenerateScenes}
                className="btn-primary w-full py-2.5 text-xs shadow-sm flex items-center justify-center gap-2"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Generate AI Scenes</span>
              </button>
            </div>
          ) : (
            <VideoPreview activeScene={activeScene} />
          )}
        </div>

        {/* Right Scene Inspector Panel */}
        <div
          className={`w-full lg:w-96 flex-shrink-0 overflow-y-auto ${
            mobileTab !== "inspector" ? "hidden lg:block" : "block"
          }`}
        >
          <SceneEditor />
        </div>
      </div>

      {/* ── Bottom Timeline Bar ─────────────────────────────────────────────── */}
      <div className={`h-40 flex-shrink-0 ${mobileTab !== "timeline" ? "hidden lg:block" : "block"}`}>
        <Timeline />
      </div>

      {/* Render Final Video Modal */}
      {isRenderModalOpen && (
        <RenderModal
          projectId={projectId}
          onClose={() => setIsRenderModalOpen(false)}
        />
      )}
    </div>
  );
}