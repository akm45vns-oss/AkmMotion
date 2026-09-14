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
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="border-b border-[#24272E] pb-4">
        <h1 className="text-xl sm:text-2xl font-bold text-[#F2F2F3] tracking-tight">
          Create New Video Project
        </h1>
        <p className="text-xs sm:text-sm text-neutral-400 mt-1">
          Paste your narrative script to generate 9:16 vertical scenes with character consistency and synchronized Indian voiceovers.
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-[#E55353]/10 border border-[#E55353]/25 text-[#E55353] text-xs font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Step 1: Project Title */}
        <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-3">
          <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider">
            1. Project Title
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. 5 Mind-Blowing Historical Mysteries"
            className="input-base text-sm"
          />
        </div>

        {/* Step 2: Script Input */}
        <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider flex items-center gap-1.5">
              <Type className="w-3.5 h-3.5 text-[#E0693B]" />
              <span>2. Script Text</span>
            </label>
            <div className="text-[11px] text-neutral-400 font-mono">
              <span className="font-semibold text-[#F2F2F3]">{wordCount}</span> {wordCount === 1 ? "word" : "words"} · ~
              <span className="font-semibold text-[#F2F2F3]">{estimatedSeconds}s</span> duration
            </div>
          </div>

          <textarea
            rows={7}
            required
            value={scriptContent}
            onChange={(e) => setScriptContent(e.target.value)}
            placeholder="Paste your video script in English or Hindi here. The AI Director will segment it into vertical scenes, preserve your exact spoken words, and craft cinematic visual prompts..."
            className="input-base text-xs sm:text-sm leading-relaxed resize-none"
          />
        </div>

        {/* Step 3: Style Selection */}
        <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-3">
          <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider flex items-center gap-1.5">
            <Video className="w-3.5 h-3.5 text-[#E0693B]" />
            <span>3. Visual Style</span>
          </label>
          <StyleSelector selected={style} onSelect={setStyle} />
        </div>

        {/* Step 4: Voiceover Selection */}
        <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-3">
          <label className="block text-xs font-semibold text-neutral-300 uppercase tracking-wider flex items-center gap-1.5">
            <Volume2 className="w-3.5 h-3.5 text-[#E0693B]" />
            <span>4. Narration Voice</span>
          </label>
          <VoiceSelector selected={voice} onSelect={setVoice} />
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full sm:w-auto px-7 py-3 text-sm flex items-center justify-center gap-2 touch-target shadow-md"
          >
            {loading ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>{loadingMessage}</span>
              </>
            ) : (
              <>
                <span>Generate Video Studio</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}