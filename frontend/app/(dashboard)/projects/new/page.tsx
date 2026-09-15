"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Video, Volume2, Type, Sparkles } from "lucide-react";
import StyleSelector from "@/components/project/StyleSelector";
import VoiceSelector from "@/components/project/VoiceSelector";
import { projectsApi } from "@/lib/api/projects";
import { aiApi } from "@/lib/api/ai";

export default function NewProjectPage() {
  const router = useRouter();

  const [title, setTitle] = useState("");
  const [scriptContent, setScriptContent] = useState("");
  const [style, setStyle] = useState("Explainer");
  const [voice, setVoice] = useState("voice_indian_en");
  const [language, setLanguage] = useState("en");
  const [loading, setLoading] = useState(false);
  const [loadingMessage, setLoadingMessage] = useState("Creating Project...");
  const [error, setError] = useState<string | null>(null);

  const words = scriptContent.trim() ? scriptContent.trim().split(/\s+/).filter(Boolean) : [];
  const wordCount = words.length;

  // Harmonized with backend ScriptAnalyzerService pacing engine (2.2 words/sec, 3.0s-10.0s per scene)
  const estimatedSeconds = (() => {
    if (wordCount === 0) return 0;
    let targetScenes = 1;
    if (wordCount > 300) {
      targetScenes = Math.min(10, Math.max(6, Math.ceil(wordCount / 50)));
    } else if (wordCount > 180) {
      targetScenes = 4;
    } else if (wordCount > 100) {
      targetScenes = 3;
    } else if (wordCount > 50) {
      targetScenes = 2;
    } else if (wordCount > 20) {
      targetScenes = 2;
    } else {
      targetScenes = 1;
    }
    const wordsPerScene = wordCount / targetScenes;
    const sceneDuration = Math.min(Math.max(wordsPerScene / 2.2, 3.0), 10.0);
    return Math.round(sceneDuration * targetScenes);
  })();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError("Please provide a project title.");
      return;
    }
    if (!scriptContent.trim()) {
      setError("Please paste or write your script.");
      return;
    }

    setLoading(true);
    setLoadingMessage("Creating project...");
    setError(null);

    try {
      const project = await projectsApi.create({
        title: title.trim(),
        style,
        language,
        script_content: scriptContent.trim(),
      });

      setLoadingMessage("AI Director generating 9:16 vertical scenes...");
      try {
        await aiApi.generatePipeline(project.id);
      } catch (pipeErr) {
        console.warn("Pipeline generation notice:", pipeErr);
      }

      if (typeof window !== "undefined") {
        window.location.href = `/projects/${project.id}/editor`;
      } else {
        router.push(`/projects/${project.id}/editor`);
      }
    } catch (err: any) {
      console.error("Project creation error:", err);
      setError(err.response?.data?.detail || "Failed to create project. Please try again.");
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-7 pb-16">
      {/* Header */}
      <div className="border-b border-[#292A29] pb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-[#F5F1E8] tracking-tight">
          CREATE NEW VIDEO
        </h1>
        <p className="text-xs sm:text-sm text-[#77746E] mt-1">
          Turn your script into a vertical video with scene splitting, visual prompts, and voice narration.
        </p>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-[#C95C5C]/10 border border-[#C95C5C]/25 text-[#C95C5C] text-xs font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-7">
        {/* Project Section */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-[#A9A49B] uppercase tracking-wider">
            Project
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Project title (e.g. 5 Mind-Blowing Historical Mysteries)"
            className="input-base text-sm py-2.5"
          />
        </div>

        <div className="border-t border-[#292A29]" />

        {/* Script Section */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold text-[#A9A49B] uppercase tracking-wider">
              Script
            </label>
            <div className="text-[11px] text-[#77746E] font-mono">
              <span className="font-semibold text-[#F5F1E8]">{wordCount}</span> {wordCount === 1 ? "word" : "words"} · ~
              <span className="font-semibold text-[#F5F1E8]">{estimatedSeconds}s</span>
            </div>
          </div>

          <div className="relative rounded-lg border border-[#292A29] bg-[#151616] p-3 focus-within:border-[#E76536] focus-within:ring-1 focus-within:ring-[#E76536] transition-colors">
            <textarea
              rows={9}
              required
              value={scriptContent}
              onChange={(e) => setScriptContent(e.target.value)}
              placeholder="Paste or write your video script here. Every sentence and word of your script will be preserved exactly as narration and burned-in subtitles across the generated scenes..."
              className="w-full bg-transparent border-0 p-0 text-sm text-[#F5F1E8] placeholder-[#77746E] leading-relaxed resize-none focus:outline-none focus:ring-0 font-normal"
            />
          </div>
        </div>

        <div className="border-t border-[#292A29]" />

        {/* Visual Style Section */}
        <div className="space-y-2.5">
          <label className="block text-xs font-semibold text-[#A9A49B] uppercase tracking-wider">
            Visual Style
          </label>
          <StyleSelector selected={style} onSelect={setStyle} />
        </div>

        {/* Narration Voice Section */}
        <div className="space-y-2.5">
          <label className="block text-xs font-semibold text-[#A9A49B] uppercase tracking-wider">
            Narration Voice
          </label>
          <VoiceSelector selected={voice} onSelect={setVoice} />
        </div>

        {/* Create Video Action */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full sm:w-auto min-h-[44px] px-8 text-xs font-semibold flex items-center justify-center gap-2 shadow-sm"
          >
            {loading ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>{loadingMessage}</span>
              </>
            ) : (
              <>
                <span>CREATE VIDEO</span>
                <ArrowRight className="w-3.5 h-3.5 ml-0.5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}