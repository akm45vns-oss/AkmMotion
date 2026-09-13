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
import { Loader2, Sparkles, Wand2 } from "lucide-react";

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
        // Auto-generate if project has script but zero scenes
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
      <div className="h-screen w-full flex items-center justify-center bg-[#090D16]">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-8 h-8 text-indigo-500 animate-spin" />
          <p className="text-sm font-medium text-gray-400">Loading Video Studio...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full flex flex-col bg-[#090D16] text-white overflow-hidden">
      {/* Top Studio Toolbar */}
      <ToolBar
        onRenderClick={() => setIsRenderModalOpen(true)}
        onGenerateClick={handleGenerateScenes}
        isGenerating={isGenerating}
      />

      {/* Main Studio Viewport (Preview Player + Inspector) */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 border-r border-gray-800 p-4 flex flex-col justify-center items-center">
          {isGenerating ? (
            <div className="w-full max-w-md p-8 rounded-2xl bg-[#0D1322] border border-indigo-500/20 text-center space-y-4 shadow-2xl">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                <Sparkles className="w-7 h-7 text-indigo-400 animate-spin" />
              </div>
              <div className="space-y-1">
                <h3 className="text-base font-bold text-white">AI Director at Work</h3>
                <p className="text-xs text-gray-400">
                  Splitting script into 5-7 vertical scenes, generating cinematic visual prompts & audio tracks...
                </p>
              </div>
            </div>
          ) : scenes.length === 0 ? (
            <div className="w-full max-w-md p-8 rounded-2xl bg-[#0D1322] border border-gray-800 text-center space-y-5 shadow-2xl">
              <div className="w-14 h-14 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                <Sparkles className="w-7 h-7" />
              </div>
              <div className="space-y-1.5">
                <h3 className="text-lg font-bold text-white">No Scenes Generated Yet</h3>
                <p className="text-xs text-gray-400 leading-relaxed">
                  Your script is saved. Click below to automatically generate all 9:16 vertical scenes, captions, and visual assets.
                </p>
              </div>
              <button
                onClick={handleGenerateScenes}
                className="w-full py-3 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-90 text-white text-xs font-bold shadow-lg shadow-indigo-500/25 flex items-center justify-center gap-2 transition-all"
              >
                <Sparkles className="w-4 h-4" />
                Generate AI Scenes
              </button>
            </div>
          ) : (
            <VideoPreview activeScene={activeScene} />
          )}
        </div>
        <div className="w-96 p-4">
          <SceneEditor />
        </div>
      </div>

      {/* Bottom Timeline Bar */}
      <div className="h-44 border-t border-gray-800 bg-[#0D1322]">
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