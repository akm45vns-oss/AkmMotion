"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useEditorStore } from "@/lib/stores/editorStore";
import { projectsApi } from "@/lib/api/projects";
import { scenesApi } from "@/lib/api/scenes";
import ToolBar from "@/components/editor/ToolBar";
import VideoPreview from "@/components/editor/VideoPreview";
import SceneEditor from "@/components/editor/SceneEditor";
import Timeline from "@/components/editor/Timeline";
import RenderModal from "@/components/editor/RenderModal";
import { Loader2 } from "lucide-react";

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
  } = useEditorStore();

  const [isRenderModalOpen, setIsRenderModalOpen] = useState(false);

  useEffect(() => {
    if (!projectId) return;

    setIsLoading(true);
    Promise.all([
      projectsApi.getById(projectId),
      scenesApi.getByProjectId(projectId),
    ])
      .then(([projectData, scenesData]) => {
        setProject(projectData);
        setScenes(scenesData);
        if (scenesData.length > 0) {
          setActiveSceneId(scenesData[0].id);
        }
      })
      .catch((err) => {
        console.error("Failed to load project editor data:", err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, [projectId, setProject, setScenes, setActiveSceneId, setIsLoading]);

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
      <ToolBar onRenderClick={() => setIsRenderModalOpen(true)} />

      {/* Main Studio Viewport (Preview Player + Inspector) */}
      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 border-r border-gray-800 p-4">
          <VideoPreview activeScene={activeScene} />
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