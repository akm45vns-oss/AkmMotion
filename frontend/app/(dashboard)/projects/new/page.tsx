"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, ArrowRight, Video, Volume2, Type } from "lucide-react";
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

  const wordCount = scriptContent.trim() ? scriptContent.trim().split(/\s+/).length : 0;
  const estimatedSeconds = Math.round(wordCount / 2.5);

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

      // Redirect cleanly to studio editor
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
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <Sparkles className="w-6 h-6 text-indigo-400" />
          Create New AI Video Project
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Paste your script, select style and voiceover, and let AI generate your 9:16 vertical video scenes.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm font-medium">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Project Name */}
        <div className="p-6 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-4">
          <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider">
            1. Project Title
          </label>
          <input
            type="text"
            required
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. 5 Mind-Blowing Facts About AI"
            className="w-full px-4 py-3 rounded-xl bg-[#090D16] border border-gray-800 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm"
          />
        </div>

        {/* Script Input */}
        <div className="p-6 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-4">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
              <Type className="w-4 h-4 text-indigo-400" />
              2. Paste or Write Script
            </label>
            <div className="text-xs text-gray-400">
              <span className="font-semibold text-indigo-400">{wordCount}</span> words • ~
              <span className="font-semibold text-indigo-400">{estimatedSeconds}s</span> video duration
            </div>
          </div>

          <textarea
            rows={8}
            required
            value={scriptContent}
            onChange={(e) => setScriptContent(e.target.value)}
            placeholder="Paste your video script here in English or Hindi... AI will segment scenes, synthesize natural voiceover, and prepare for 1080x1920 MP4 rendering."
            className="w-full px-4 py-3 rounded-xl bg-[#090D16] border border-gray-800 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-sm leading-relaxed"
          />
        </div>

        {/* Visual Style Selection */}
        <div className="p-6 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-4">
          <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
            <Video className="w-4 h-4 text-purple-400" />
            3. Choose Visual Style
          </label>
          <StyleSelector selected={style} onSelect={setStyle} />
        </div>

        {/* Voiceover Selection */}
        <div className="p-6 rounded-2xl bg-[#0D1322] border border-gray-800 space-y-4">
          <label className="block text-xs font-semibold text-gray-300 uppercase tracking-wider flex items-center gap-2">
            <Volume2 className="w-4 h-4 text-pink-400" />
            4. Choose AI Narration Voice
          </label>
          <VoiceSelector selected={voice} onSelect={setVoice} />
        </div>

        {/* Generate CTA Button */}
        <div className="flex justify-end pt-4">
          <button
            type="submit"
            disabled={loading}
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:from-indigo-500 hover:to-pink-500 text-white font-bold text-base shadow-xl shadow-indigo-600/30 transition-all flex items-center gap-3 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>{loadingMessage}</span>
              </>
            ) : (
              <>
                <span>Generate Video Studio</span>
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>
        </div>
      </form>

    </div>
  );
}