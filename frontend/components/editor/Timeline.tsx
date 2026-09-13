"use client";

import { useEditorStore } from "@/lib/stores/editorStore";
import { Layers } from "lucide-react";

import { API_BASE_URL } from "@/lib/api/client";

export default function Timeline() {
  const { scenes, activeSceneIndex, activeSceneId, setActiveSceneId, setActiveSceneIndex } = useEditorStore();

  const getSceneImageUrl = (scene: any) => {
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

    const rawPrompt = (scene?.image_prompt || scene?.narration || scene?.subtitle || "").replace(/\*\*/g, "").trim();
    const promptText = rawPrompt || `Indian story scene ${scene?.scene_number || 1}`;
    
    const encodedPrompt = encodeURIComponent(`photorealistic 8k render, ${promptText}, 9:16 vertical aspect ratio, cinematic lighting, ultra detailed`);
    const seed = ((scene?.scene_number || 1) * 73 + 1234) % 99999;
    return `https://image.pollinations.ai/prompt/${encodedPrompt}?width=768&height=1344&model=flux-realism&nologo=true&seed=${seed}`;
  };

  return (
    <div className="h-44 border-t border-gray-800 bg-[#0D1322] flex flex-col justify-between p-4">
      {/* Track Header */}
      <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
        <div className="flex items-center gap-2 font-semibold text-white">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span>Scene Timeline Tracks ({scenes.length})</span>
        </div>
        <div className="text-[11px]">Click scene card to select and inspect</div>
      </div>

      {/* Horizontal Scenes Track */}
      <div className="flex-1 flex items-center gap-3 overflow-x-auto py-1 scrollbar-thin scrollbar-thumb-gray-800">
        {scenes.map((scene, index) => {
          const isActive = index === activeSceneIndex || scene.id === activeSceneId;
          const imageUrl = getSceneImageUrl(scene);

          const handleSelect = () => {
            setActiveSceneIndex(index);
            setActiveSceneId(scene.id);
          };

          return (
            <div
              key={scene.id || index}
              onClick={handleSelect}
              className={`flex-shrink-0 w-36 h-28 rounded-xl border cursor-pointer relative overflow-hidden transition-all group ${
                isActive
                  ? "border-indigo-500 ring-2 ring-indigo-500/50 scale-[1.02]"
                  : "border-gray-800 hover:border-gray-700 bg-black/40"
              }`}
            >
              {/* Background Scene Image */}
              <img
                src={imageUrl}
                alt=""
                onError={(e) => {
                  if (!e.currentTarget.src.includes("/ai/image-proxy") && imageUrl.startsWith("http")) {
                    e.currentTarget.src = `${API_BASE_URL}/ai/image-proxy?url=${encodeURIComponent(imageUrl)}`;
                  }
                }}
                className="w-full h-full object-cover opacity-70 group-hover:opacity-90 transition-opacity"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/40" />

              {/* Scene Number Badge */}
              <div className="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-black/70 text-[10px] font-bold text-white border border-white/10">
                #{scene.scene_number}
              </div>

              {/* Duration Badge */}
              <div className="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-indigo-600/80 text-[10px] font-bold text-white">
                {scene.duration || 5}s
              </div>

              {/* Narration Teaser */}
              <div className="absolute bottom-2 left-2 right-2 text-[10px] text-gray-200 line-clamp-1 font-medium">
                {(scene.narration || "").replace(/\*\*/g, "")}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}