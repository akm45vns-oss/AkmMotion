"use client";

import { useEditorStore } from "@/lib/stores/editorStore";
import { Layers, Clock } from "lucide-react";
import { API_BASE_URL } from "@/lib/api/client";

export default function Timeline() {
  const { scenes, activeSceneIndex, activeSceneId, setActiveSceneId, setActiveSceneIndex } = useEditorStore();

  const totalDuration = scenes.reduce((sum, s) => sum + (s.duration || 5), 0);

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
    <div className="h-40 border-t border-[#24272E] bg-[#141517] flex flex-col justify-between p-3 sm:p-4 select-none">
      {/* Track Header */}
      <div className="flex items-center justify-between text-xs text-neutral-400 mb-1.5">
        <div className="flex items-center gap-2 font-semibold text-[#F2F2F3]">
          <Layers className="w-3.5 h-3.5 text-[#E0693B]" />
          <span>Timeline Tracks ({scenes.length} Scenes)</span>
        </div>
        <div className="flex items-center gap-1.5 text-[11px] font-mono text-neutral-400">
          <Clock className="w-3 h-3 text-[#E0693B]" />
          <span>Total: {totalDuration.toFixed(1)}s</span>
        </div>
      </div>

      {/* Horizontal Scenes Track */}
      <div className="flex-1 flex items-center gap-2.5 overflow-x-auto py-1 scrollbar-thin">
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
              className={`flex-shrink-0 w-32 sm:w-36 h-24 rounded-lg border cursor-pointer relative overflow-hidden transition-all group ${
                isActive
                  ? "border-[#E0693B] ring-1 ring-[#E0693B] shadow-md shadow-[#E0693B]/20 scale-[1.02]"
                  : "border-[#24272E] hover:border-[#333742] bg-[#0C0D0E]"
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
                className="w-full h-full object-cover opacity-75 group-hover:opacity-90 transition-opacity"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-black/60" />

              {/* Scene Number Badge */}
              <div className="absolute top-1.5 left-1.5 px-1.5 py-0.5 rounded bg-black/80 text-[10px] font-bold text-white border border-white/10 font-mono">
                #{scene.scene_number}
              </div>

              {/* Duration Badge */}
              <div className="absolute top-1.5 right-1.5 px-1.5 py-0.5 rounded bg-[#141517]/90 text-[10px] font-medium text-neutral-300 border border-[#24272E] font-mono">
                {scene.duration || 5}s
              </div>

              {/* Narration Preview */}
              <div className="absolute bottom-1.5 left-1.5 right-1.5 text-[10px] text-neutral-200 line-clamp-1 font-medium">
                {(scene.narration || "").replace(/\*\*/g, "")}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}