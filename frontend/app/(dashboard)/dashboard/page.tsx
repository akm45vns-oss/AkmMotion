"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sparkles, Film, CheckCircle2, FolderSync, Plus, Play } from "lucide-react";
import { projectsApi, Project } from "@/lib/api/projects";

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsApi
      .list(1, 6)
      .then((res) => setProjects(res.items))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const completedCount = projects.filter((p) => p.status === "completed").length;
  const draftCount = projects.filter((p) => p.status !== "completed").length;

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="p-8 rounded-3xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-[#0D1322] border border-indigo-500/20 relative overflow-hidden">
        <div className="max-w-2xl relative z-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 text-xs font-semibold uppercase tracking-wider mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI Shorts & Reels Generator</span>
          </div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight mb-2">
            Create AI Shorts in Seconds
          </h1>
          <p className="text-sm text-gray-300 leading-relaxed mb-6">
            Paste your script, select an AI style & narrator, and generate vertical 1080×1920 videos ready for YouTube Shorts, Reels, and TikTok.
          </p>

          <Link
            href="/projects/new"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Create New Video</span>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-600/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
            <Film className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{projects.length}</div>
            <div className="text-xs text-gray-400">Total Projects</div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-600/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{completedCount}</div>
            <div className="text-xs text-gray-400">Completed Videos</div>
          </div>
        </div>

        <div className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-amber-600/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
            <FolderSync className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-white">{draftCount}</div>
            <div className="text-xs text-gray-400">In Progress / Drafts</div>
          </div>
        </div>
      </div>

      {/* Recent Projects */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-white">Recent Projects</h2>
          <Link href="/projects" className="text-xs text-indigo-400 hover:text-indigo-300 font-medium">
            View All →
          </Link>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500 text-sm">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="p-8 rounded-2xl border border-dashed border-gray-800 bg-[#0D1322]/50 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-gray-800/50 flex items-center justify-center mx-auto text-gray-500">
              <Film className="w-6 h-6" />
            </div>
            <div className="text-sm font-semibold text-gray-300">No projects yet</div>
            <p className="text-xs text-gray-500 max-w-sm mx-auto">
              Start by creating your first script-to-video project.
            </p>
            <Link
              href="/projects/new"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 text-white font-medium text-xs shadow-md shadow-indigo-600/20"
            >
              <Plus className="w-4 h-4" />
              <span>Create Project</span>
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {projects.map((p) => (
              <Link
                key={p.id}
                href={`/projects/${p.id}/editor`}
                className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 hover:border-indigo-500/50 transition-all group flex flex-col justify-between h-44"
              >
                <div>
                  <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                    <span className="px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 font-semibold border border-indigo-500/20">
                      {p.style}
                    </span>
                    <span className="capitalize">{p.status}</span>
                  </div>
                  <h3 className="font-bold text-white group-hover:text-indigo-400 transition-colors line-clamp-2">
                    {p.title}
                  </h3>
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-gray-800/80 text-xs text-gray-400">
                  <span>{new Date(p.created_at).toLocaleDateString()}</span>
                  <div className="flex items-center gap-1 text-indigo-400 font-medium group-hover:translate-x-0.5 transition-transform">
                    <span>Studio</span>
                    <Play className="w-3 h-3 fill-indigo-400" />
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
