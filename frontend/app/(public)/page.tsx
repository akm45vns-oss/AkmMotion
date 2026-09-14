"use client";

import Link from "next/link";
import { Sparkles, Play, ShieldCheck, Wand2, ArrowRight, UserCheck, Volume2, Film, Layers, Zap } from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#090D16] text-white selection:bg-indigo-500 selection:text-white">
      {/* Top Glass Header */}
      <header className="border-b border-gray-800/80 bg-[#090D16]/80 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-pink-500 flex items-center justify-center font-extrabold text-white text-lg shadow-lg shadow-indigo-500/25">
            A
          </div>
          <div>
            <span className="text-xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-white via-indigo-200 to-gray-400">
              AkmMotion
            </span>
            <span className="hidden sm:inline-block ml-2 text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-bold uppercase tracking-wider">
              AI Video SaaS
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Link
            href="/characters"
            className="hidden md:flex items-center gap-1.5 text-xs font-semibold text-gray-300 hover:text-indigo-400 transition-colors"
          >
            <UserCheck className="w-4 h-4 text-indigo-400" />
            <span>Character Studio</span>
          </Link>

          <Link
            href="/login"
            className="text-xs font-semibold text-gray-300 hover:text-white transition-colors"
          >
            Sign In
          </Link>
          <Link
            href="/projects/new"
            className="text-xs font-bold px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white shadow-lg shadow-indigo-600/25 transition-all transform hover:scale-105"
          >
            Create Video Free
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center text-center px-6 pt-16 pb-24 relative overflow-hidden">
        {/* Background Ambient Glowing Orbs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-indigo-600/20 via-purple-600/15 to-pink-600/10 blur-[120px] rounded-full pointer-events-none" />

        {/* Feature Pill */}
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-8 shadow-inner">
          <Sparkles className="w-4 h-4 text-amber-400 animate-spin" />
          <span>Character Memory Engine (CME) v7.3 Active</span>
        </div>

        {/* Hero Title */}
        <h1 className="text-4xl sm:text-6xl md:text-7xl font-black max-w-5xl tracking-tight leading-[1.1] mb-6">
          Turn Simple Scripts Into <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-300 to-pink-400">
            Viral YouTube Shorts & Reels
          </span>
        </h1>

        {/* Subtitle */}
        <p className="text-base sm:text-xl text-gray-400 max-w-2xl mb-10 leading-relaxed font-normal">
          Automated scene splitting, <strong className="text-white font-semibold">100% Visual Character Memory Consistency</strong>, Indian voiceover narration, and 1080×1920 vertical video rendering in under 2 minutes.
        </p>

        {/* CTA Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-4 z-10">
          <Link
            href="/projects/new"
            className="w-full sm:w-auto px-8 py-4 rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 hover:opacity-95 text-white font-extrabold text-base shadow-2xl shadow-indigo-600/30 transition-all transform hover:-translate-y-0.5 flex items-center justify-center gap-3"
          >
            <Wand2 className="w-5 h-5" />
            <span>Generate Video Project →</span>
          </Link>

          <Link
            href="/characters"
            className="w-full sm:w-auto px-8 py-4 rounded-2xl border border-gray-800 hover:border-indigo-500/50 bg-[#0D1322] text-gray-200 font-bold text-base transition-all flex items-center justify-center gap-2"
          >
            <UserCheck className="w-5 h-5 text-indigo-400" />
            <span>Character Studio</span>
          </Link>
        </div>

        {/* Live Smartphone Interactive Showcase */}
        <div className="mt-16 relative z-10 w-full max-w-4xl flex items-center justify-center">
          <div className="p-4 rounded-3xl bg-[#0D1322] border border-gray-800/90 shadow-2xl shadow-indigo-950/60 relative flex flex-col md:flex-row items-center gap-8">
            {/* 9:16 Video Frame */}
            <div className="relative w-[240px] h-[426px] rounded-2xl overflow-hidden border-2 border-indigo-500/30 bg-black shadow-2xl flex-shrink-0 flex flex-col justify-between p-4 group">
              <img
                src="https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=600&h=1066&q=80"
                alt="AI Scene"
                className="absolute inset-0 w-full h-full object-cover opacity-85 group-hover:scale-110 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/90" />

              <div className="relative z-10 flex items-center justify-between">
                <span className="px-2.5 py-0.5 rounded-full bg-black/70 backdrop-blur text-[10px] font-bold text-white border border-white/10">
                  #SCENE 1
                </span>
                <span className="px-2.5 py-0.5 rounded-full bg-indigo-600/90 text-[10px] font-bold text-white">
                  9:16 HD
                </span>
              </div>

              <div className="relative z-10 text-center">
                <div className="inline-block px-3 py-1.5 rounded-xl bg-black/85 backdrop-blur border border-white/20">
                  <p className="text-yellow-300 font-black text-xs uppercase tracking-wider">
                    RAHUL EXPLORES THE SACRED TEMPLES
                  </p>
                </div>
              </div>
            </div>

            {/* Feature Description Card */}
            <div className="text-left space-y-4 max-w-md p-2">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold">
                <ShieldCheck className="w-4 h-4" /> 100% CME Character Visual Locking
              </div>
              <h3 className="text-2xl font-extrabold text-white">
                Guaranteed Visual Consistency Across Every Scene
              </h3>
              <p className="text-xs text-gray-400 leading-relaxed">
                Character Memory Engine (CME) locks your character's facial features, hairstyle, skin tone, and outfit description across all generated scenes. No random face changes. No costume shifts.
              </p>
              <div className="grid grid-cols-2 gap-3 pt-2 text-xs font-semibold">
                <div className="p-3 rounded-xl bg-[#090D16] border border-gray-800 flex items-center gap-2 text-indigo-300">
                  <UserCheck className="w-4 h-4 text-indigo-400" />
                  <span>Persistent Character DNA</span>
                </div>
                <div className="p-3 rounded-xl bg-[#090D16] border border-gray-800 flex items-center gap-2 text-purple-300">
                  <Volume2 className="w-4 h-4 text-purple-400" />
                  <span>Native Indian Voiceover</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="mt-24 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl w-full text-left">
          <div className="p-6 rounded-3xl bg-[#0D1322] border border-gray-800 hover:border-indigo-500/40 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold">
              <UserCheck className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Character Memory Engine (CME)</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Stores character DNA in PostgreSQL with fast &lt;100ms lookups. Injects locked character identity into every visual prompt.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-[#0D1322] border border-gray-800 hover:border-purple-500/40 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-purple-600/10 border border-purple-500/20 text-purple-400 flex items-center justify-center font-bold">
              <Zap className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">AI Scene Director</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Deconstructs English &amp; Hindi scripts into cinematic visual scenes, camera motions, and synced Indian voiceover narration.
            </p>
          </div>

          <div className="p-6 rounded-3xl bg-[#0D1322] border border-gray-800 hover:border-pink-500/40 transition-all space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-pink-600/10 border border-pink-500/20 text-pink-400 flex items-center justify-center font-bold">
              <Film className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Server-Side FFmpeg Renderer</h3>
            <p className="text-xs text-gray-400 leading-relaxed">
              Produces true production-grade 1080×1920 vertical MP4 videos with H.264 video, AAC audio, synced subtitles, and Ken Burns camera movements.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800 py-8 text-center text-xs text-gray-500 bg-[#090D16]">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-indigo-600 font-bold text-white flex items-center justify-center text-xs">A</div>
            <span className="font-bold text-gray-300">AkmMotion AI SaaS</span>
          </div>
          <div>© 2026 AkmMotion AI Video Engine. All rights reserved.</div>
        </div>
      </footer>
    </div>
  );
}