"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Film, CheckCircle2, Clock, ArrowRight, Video } from "lucide-react";
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
    <div className="max-w-6xl mx-auto space-y-8">
      {/* ─── Creative Hero Workspace Banner ────────────────────────────────── */}
      <section className="p-6 sm:p-8 rounded-2xl bg-[#141517] border border-[#24272E] flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
        <div className="space-y-2 max-w-xl">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#E0693B]/10 border border-[#E0693B]/25 text-[#E0693B] text-[11px] font-semibold tracking-wide uppercase">
            <span>Video Creation Studio</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-[#F2F2F3] tracking-tight">
            Transform Scripts into Vertical Videos
          </h1>
          <p className="text-xs sm:text-sm text-neutral-400 leading-relaxed">
            Automated scene splitting, Character Memory Engine (CME) visual consistency, native Indian voiceover narration, and server-side 1080×1920 MP4 rendering.
          </p>
        </div>

        <Link
          href="/projects/new"
          className="btn-primary w-full sm:w-auto text-sm px-6 py-3 shadow-sm flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Video</span>
        </Link>
      </section>

      {/* ─── Functional Project Counts ──────────────────────────────────────── */}
      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-4 sm:p-5 rounded-xl bg-[#141517] border border-[#24272E] flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-[#1B1D21] border border-[#24272E] flex items-center justify-center text-neutral-300">
            <Film className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-[#F2F2F3]">{projects.length}</div>
            <div className="text-xs text-neutral-400">Total Projects</div>
          </div>
        </div>

        <div className="p-4 sm:p-5 rounded-xl bg-[#141517] border border-[#24272E] flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-[#2EB88A]/10 border border-[#2EB88A]/25 flex items-center justify-center text-[#2EB88A]">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-[#F2F2F3]">{completedCount}</div>
            <div className="text-xs text-neutral-400">Completed Videos</div>
          </div>
        </div>

        <div className="p-4 sm:p-5 rounded-xl bg-[#141517] border border-[#24272E] flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-lg bg-[#E5A43B]/10 border border-[#E5A43B]/25 flex items-center justify-center text-[#E5A43B]">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xl font-bold text-[#F2F2F3]">{draftCount}</div>
            <div className="text-xs text-neutral-400">Drafts / In Progress</div>
          </div>
        </div>
      </section>

      {/* ─── Recent Projects Workspace ─────────────────────────────────────── */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-[#F2F2F3]">Recent Projects</h2>
            <p className="text-xs text-neutral-400">Continue editing your recent video timelines</p>
          </div>
          <Link
            href="/projects"
            className="text-xs font-medium text-[#E0693B] hover:text-[#EB794D] flex items-center gap-1 transition-colors"
          >
            <span>View All</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-44 rounded-xl bg-[#141517] border border-[#24272E] animate-pulse" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="p-10 rounded-xl border border-dashed border-[#24272E] bg-[#141517]/40 text-center space-y-3">
            <div className="w-12 h-12 rounded-xl bg-[#1B1D21] border border-[#24272E] flex items-center justify-center mx-auto text-neutral-400">
              <Video className="w-5 h-5" />
            </div>
            <div className="text-sm font-semibold text-[#F2F2F3]">No video projects yet</div>
            <p className="text-xs text-neutral-400 max-w-sm mx-auto">
              Start by pasting your script or creating a new vertical video project.
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
                className="group p-5 rounded-xl bg-[#141517] border border-[#24272E] hover:border-[#333742] hover:bg-[#1B1D21]/50 transition-all flex flex-col justify-between h-48"
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="px-2 py-0.5 rounded bg-[#1B1D21] border border-[#24272E] text-neutral-300 text-[11px] font-medium">
                      {p.style}
                    </span>
                    <span className="text-[10px] text-neutral-500 font-mono">
                      {new Date(p.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="font-semibold text-sm text-[#F2F2F3] group-hover:text-[#E0693B] transition-colors line-clamp-2">
                    {p.title}
                  </h3>
                </div>

                <div className="pt-3 border-t border-[#24272E] flex items-center justify-between text-xs">
                  <span className="text-[11px] text-neutral-400">
                    {p.status === "completed" ? "✅ Completed" : "✏️ In Studio"}
                  </span>
                  <span className="text-[11px] font-medium text-[#E0693B] group-hover:translate-x-0.5 transition-transform flex items-center gap-1">
                    <span>Open Editor</span>
                    <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
