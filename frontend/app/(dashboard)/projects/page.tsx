"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Film, Trash2, Play } from "lucide-react";
import { projectsApi, Project } from "@/lib/api/projects";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchProjects = () => {
    setLoading(true);
    projectsApi
      .list(1, 50)
      .then((res) => setProjects(res.items))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (!confirm("Are you sure you want to delete this project?")) return;
    try {
      await projectsApi.delete(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Your Video Projects</h1>
          <p className="text-sm text-gray-400 mt-1">Manage and edit your AI video creation projects</p>
        </div>

        <Link
          href="/projects/new"
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-md shadow-indigo-600/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </Link>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-500 text-sm">Loading projects...</div>
      ) : projects.length === 0 ? (
        <div className="p-12 rounded-2xl border border-dashed border-gray-800 bg-[#0D1322]/50 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-gray-800/50 flex items-center justify-center mx-auto text-gray-500">
            <Film className="w-7 h-7" />
          </div>
          <h3 className="text-base font-semibold text-white">No projects created yet</h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto">
            Create your first AI video project to turn scripts into YouTube Shorts.
          </p>
          <Link
            href="/projects/new"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold text-xs shadow-md shadow-indigo-600/20"
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
              className="p-5 rounded-2xl bg-[#0D1322] border border-gray-800 hover:border-indigo-500/50 transition-all group flex flex-col justify-between h-48 relative"
            >
              <div>
                <div className="flex items-center justify-between text-xs text-gray-400 mb-2">
                  <span className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 font-semibold border border-indigo-500/20">
                    {p.style}
                  </span>
                  <button
                    onClick={(e) => handleDelete(p.id, e)}
                    className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <h3 className="font-bold text-white group-hover:text-indigo-400 transition-colors line-clamp-2">
                  {p.title}
                </h3>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-gray-800/80 text-xs text-gray-400">
                <span>{new Date(p.created_at).toLocaleDateString()}</span>
                <div className="flex items-center gap-1.5 text-indigo-400 font-medium group-hover:translate-x-0.5 transition-transform">
                  <span>Open Studio</span>
                  <Play className="w-3 h-3 fill-indigo-400" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
