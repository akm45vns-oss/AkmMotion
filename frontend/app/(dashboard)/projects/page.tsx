"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Film, Trash2, ArrowRight } from "lucide-react";
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
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this project?")) return;
    try {
      await projectsApi.delete(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#24272E] pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#F2F2F3] tracking-tight">Your Video Projects</h1>
          <p className="text-xs sm:text-sm text-neutral-400 mt-1">Manage and edit your video timelines and exports</p>
        </div>

        <Link
          href="/projects/new"
          className="btn-primary text-xs flex items-center justify-center gap-2 self-start sm:self-auto touch-target"
        >
          <Plus className="w-4 h-4" />
          <span>New Project</span>
        </Link>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="h-44 rounded-xl bg-[#141517] border border-[#24272E] animate-pulse" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <div className="p-12 rounded-xl border border-dashed border-[#24272E] bg-[#141517]/40 text-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-[#1B1D21] border border-[#24272E] flex items-center justify-center mx-auto text-neutral-400">
            <Film className="w-6 h-6" />
          </div>
          <h3 className="text-sm font-semibold text-[#F2F2F3]">No projects created yet</h3>
          <p className="text-xs text-neutral-400 max-w-sm mx-auto">
            Create your first script-to-video project to generate scenes and render 1080×1920 MP4s.
          </p>
          <div className="pt-2">
            <Link href="/projects/new" className="btn-primary text-xs">
              <Plus className="w-3.5 h-3.5" />
              <span>Create First Project</span>
            </Link>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.id}/editor`}
              className="p-5 rounded-xl bg-[#141517] border border-[#24272E] hover:border-[#333742] hover:bg-[#1B1D21]/50 transition-all group flex flex-col justify-between h-48 relative"
            >
              <div>
                <div className="flex items-center justify-between text-xs mb-2">
                  <span className="px-2 py-0.5 rounded bg-[#1B1D21] border border-[#24272E] text-neutral-300 text-[11px] font-medium">
                    {p.style}
                  </span>
                  <button
                    onClick={(e) => handleDelete(p.id, e)}
                    className="p-1.5 rounded-lg text-neutral-400 hover:text-[#E55353] hover:bg-[#E55353]/10 transition-colors"
                    title="Delete project"
                    aria-label="Delete project"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
                <h3 className="font-semibold text-sm text-[#F2F2F3] group-hover:text-[#E0693B] transition-colors line-clamp-2">
                  {p.title}
                </h3>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-[#24272E] text-xs text-neutral-400">
                <span className="text-[11px] font-mono">{new Date(p.created_at).toLocaleDateString()}</span>
                <div className="flex items-center gap-1 text-[#E0693B] font-medium text-[11px] group-hover:translate-x-0.5 transition-transform">
                  <span>Open Studio</span>
                  <ArrowRight className="w-3 h-3" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
