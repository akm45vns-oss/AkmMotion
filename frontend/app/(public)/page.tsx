"use client";

import Link from "next/link";
import Logo from "@/components/shared/Logo";
import {
  Wand2,
  ShieldCheck,
  UserCheck,
  Volume2,
  Film,
  ArrowRight,
  Sliders,
  CheckCircle2,
  Video,
  Cpu,
  Layers,
  Sparkles,
} from "lucide-react";

export default function LandingPage() {
  return (
    <div className="flex flex-col min-h-screen bg-[#0D0E0E] text-[#F5F1E8] selection:bg-[#E76536]/30 selection:text-[#F5F1E8]">
      {/* Editorial Header */}
      <header className="border-b border-[#292A29] bg-[#0D0E0E]/90 backdrop-blur-md sticky top-0 z-50 px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Logo href="/" size="md" />
          <span className="hidden sm:inline-block text-[10px] font-mono px-2 py-0.5 rounded border border-[#292A29] bg-[#151616] text-[#A9A49B]">
            STUDIO v7.3
          </span>
        </div>

        <nav className="flex items-center gap-3 sm:gap-6">
          <Link
            href="/characters"
            className="hidden md:flex items-center gap-1.5 text-xs font-medium text-[#A9A49B] hover:text-[#F5F1E8] transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5 text-[#E76536]" />
            <span>Character Studio</span>
          </Link>

          <Link
            href="/projects"
            className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-[#A9A49B] hover:text-[#F5F1E8] transition-colors"
          >
            <span>Projects</span>
          </Link>

          <Link
            href="/login"
            className="text-xs font-medium text-[#A9A49B] hover:text-[#F5F1E8] transition-colors px-2 py-1.5"
          >
            Sign In
          </Link>

          <Link
            href="/projects/new"
            className="btn-primary min-h-[40px] px-4 py-2 text-xs font-medium rounded-md inline-flex items-center gap-1.5 shadow-sm touch-target"
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>Create Video</span>
          </Link>
        </nav>
      </header>

      {/* Main Hero */}
      <main className="flex-1 flex flex-col items-center px-4 sm:px-8 pt-12 sm:pt-20 pb-20 max-w-7xl mx-auto w-full">
        {/* Architecture Highlight Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#151616] border border-[#292A29] text-xs text-[#A9A49B] mb-8">
          <span className="w-2 h-2 rounded-full bg-[#4FAE7B] animate-pulse" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-[#F5F1E8]">Character Memory Engine</span>
          <span className="text-[#383938]">•</span>
          <span className="text-[11px] text-[#A9A49B]">Server-Side 1080×1920 MP4</span>
        </div>

        {/* Editorial Headline */}
        <div className="text-center max-w-4xl space-y-4 mb-8">
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-bold tracking-tight text-[#F5F1E8] leading-[1.15] font-display">
            Script to vertical cinema. <br className="hidden sm:inline" />
            <span className="text-[#E76536]">Locked character consistency.</span>
          </h1>
          <p className="text-sm sm:text-lg text-[#A9A49B] max-w-2xl mx-auto leading-relaxed font-normal">
            Turn raw scripts into production-ready vertical Shorts and Reels. Automated scene director, visual character memory, native Indian voiceovers, and server-side FFmpeg MP4 rendering in under 2 minutes.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3.5 w-full sm:w-auto mb-16 z-10">
          <Link
            href="/projects/new"
            className="btn-primary min-h-[44px] w-full sm:w-auto px-8 py-3 rounded-md text-sm font-medium flex items-center justify-center gap-2 shadow-sm touch-target"
          >
            <Wand2 className="w-4 h-4" />
            <span>Launch Studio Project</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>

          <Link
            href="/characters"
            className="btn-secondary min-h-[44px] w-full sm:w-auto px-6 py-3 rounded-md text-sm font-medium flex items-center justify-center gap-2 touch-target"
          >
            <UserCheck className="w-4 h-4 text-[#E76536]" />
            <span>Character Studio</span>
          </Link>
        </div>

        {/* Studio Workspace Showcase */}
        <div className="w-full rounded-xl bg-[#151616] border border-[#292A29] shadow-2xl shadow-black/60 overflow-hidden mb-24">
          {/* Mock Window Header */}
          <div className="px-5 py-3 border-b border-[#292A29] bg-[#1B1C1C] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#383938]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#383938]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#383938]" />
              </div>
              <span className="text-[#77746E] ml-2 font-mono">/</span>
              <span className="text-[#F5F1E8] font-medium">The Sacred Temples of Varanasi</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-[#0D0E0E] border border-[#292A29] text-[#4FAE7B]">
                1080 × 1920 (9:16)
              </span>
              <span className="hidden sm:inline font-mono text-[11px] text-[#77746E]">
                30 FPS • H.264
              </span>
            </div>
          </div>

          {/* Mock Studio Content */}
          <div className="p-4 sm:p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            {/* 9:16 Video Player Mock */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="relative w-[240px] sm:w-[280px] aspect-[9/16] rounded-xl overflow-hidden border border-[#292A29] bg-black shadow-2xl flex flex-col justify-between p-4 group">
                <img
                  src="https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=600&h=1066&q=80"
                  alt="AkmMotion Scene Preview"
                  className="absolute inset-0 w-full h-full object-cover opacity-85 group-hover:scale-105 transition-transform duration-700"
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/70 via-transparent to-black/90 pointer-events-none" />

                {/* Top Overlay Badges */}
                <div className="relative z-10 flex items-center justify-between text-[10px]">
                  <span className="camera-badge">
                    PAN RIGHT
                  </span>
                  <span className="cme-badge">
                    <CheckCircle2 className="w-2.5 h-2.5" /> CME LOCKED
                  </span>
                </div>

                {/* Bottom Subtitle / Timecode Overlay */}
                <div className="relative z-10 space-y-2">
                  <div className="text-center">
                    <div className="inline-block px-3 py-1.5 rounded-md bg-black/85 backdrop-blur border border-white/10 text-xs font-bold text-[#F5F1E8] leading-snug">
                      <span className="text-[#E76536]">Rahul</span> walks through the sacred ghats at dawn
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-[#A9A49B] pt-1">
                    <span>00:03.200</span>
                    <span>00:15.000</span>
                  </div>
                  <div className="w-full h-1 rounded-full bg-white/20 overflow-hidden">
                    <div className="w-[32%] h-full bg-[#E76536]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Studio Inspector Details */}
            <div className="lg:col-span-7 space-y-4 text-left">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#E76536]/10 border border-[#E76536]/20 text-[#E76536] text-xs font-medium font-mono">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>CME Active: Rahul (Archaeologist)</span>
              </div>

              <h2 className="text-xl sm:text-2xl font-bold text-[#F5F1E8] font-display">
                Zero character drift across every frame
              </h2>

              <p className="text-xs sm:text-sm text-[#A9A49B] leading-relaxed">
                AkmMotion&apos;s Character Memory Engine (CME) stores facial traits, clothing style, and lighting conditions in structured PostgreSQL DNA vectors. Each scene automatically injects locked visual prompts and negative prompts, ensuring your protagonist never changes face or outfit between scenes.
              </p>

              {/* Inspector Metadata Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-lg bg-[#1B1C1C] border border-[#292A29] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-[#F5F1E8]">
                    <UserCheck className="w-3.5 h-3.5 text-[#E76536]" />
                    <span>Character DNA Lock</span>
                  </div>
                  <p className="text-[11px] text-[#77746E]">
                    Rugged jacket, brown leather messenger bag, 28-year-old South Asian male.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-[#1B1C1C] border border-[#292A29] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-[#F5F1E8]">
                    <Volume2 className="w-3.5 h-3.5 text-[#E76536]" />
                    <span>Neural Voiceover</span>
                  </div>
                  <p className="text-[11px] text-[#77746E]">
                    en-IN-PrabhatNeural • 160 WPM • Word-level timestamp alignment.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-[#1B1C1C] border border-[#292A29] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-[#F5F1E8]">
                    <Sliders className="w-3.5 h-3.5 text-[#E76536]" />
                    <span>Ken Burns Motion</span>
                  </div>
                  <p className="text-[11px] text-[#77746E]">
                    Subtle horizontal panning (0.05 speed) with ease-in-out interpolation.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg bg-[#1B1C1C] border border-[#292A29] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-[#F5F1E8]">
                    <Film className="w-3.5 h-3.5 text-[#E76536]" />
                    <span>Server-Side Export</span>
                  </div>
                  <p className="text-[11px] text-[#77746E]">
                    Headless FFmpeg pipeline producing 1080×1920 MP4 with AAC audio.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Mock Timeline Footer */}
          <div className="px-5 py-3 border-t border-[#292A29] bg-[#1B1C1C] flex flex-wrap items-center gap-2 text-xs">
            <span className="font-mono text-[11px] text-[#77746E] uppercase tracking-wider mr-2">Timeline</span>
            <div className="px-3 py-1.5 rounded-md bg-[#E76536]/10 border border-[#E76536]/30 text-[#F5F1E8] font-mono text-[11px] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#E76536]" />
              <span>Scene 1: 00:00 - 00:05</span>
            </div>
            <div className="px-3 py-1.5 rounded-md bg-[#151616] border border-[#292A29] text-[#A9A49B] font-mono text-[11px] flex items-center gap-2">
              <span>Scene 2: 00:05 - 00:10</span>
            </div>
            <div className="px-3 py-1.5 rounded-md bg-[#151616] border border-[#292A29] text-[#A9A49B] font-mono text-[11px] flex items-center gap-2">
              <span>Scene 3: 00:10 - 00:15</span>
            </div>
          </div>
        </div>

        {/* 3 Pillar Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-24 text-left">
          <div className="p-6 rounded-xl bg-[#151616] border border-[#292A29] space-y-3">
            <div className="w-10 h-10 rounded-md bg-[#E76536]/10 border border-[#E76536]/20 text-[#E76536] flex items-center justify-center font-bold">
              <UserCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-[#F5F1E8] font-display">Persistent Character Memory</h3>
            <p className="text-xs sm:text-sm text-[#A9A49B] leading-relaxed">
              Lock down character appearance, clothing, age, and style. The Character Memory Engine injects stored visual traits into every scene so your audience recognizes your character instantly.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-[#151616] border border-[#292A29] space-y-3">
            <div className="w-10 h-10 rounded-md bg-[#E76536]/10 border border-[#E76536]/20 text-[#E76536] flex items-center justify-center font-bold">
              <Volume2 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-[#F5F1E8] font-display">Indian Voiceover & Synced Subtitles</h3>
            <p className="text-xs sm:text-sm text-[#A9A49B] leading-relaxed">
              Generate natural narration in Indian English (Prabhat, Neerja) and Hindi (Madhur, Swara). Word-level timing tokens synchronize on-screen subtitles perfectly with voice cadence.
            </p>
          </div>

          <div className="p-6 rounded-xl bg-[#151616] border border-[#292A29] space-y-3">
            <div className="w-10 h-10 rounded-md bg-[#E76536]/10 border border-[#E76536]/20 text-[#E76536] flex items-center justify-center font-bold">
              <Film className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-[#F5F1E8] font-display">Server-Side FFmpeg Renderer</h3>
            <p className="text-xs sm:text-sm text-[#A9A49B] leading-relaxed">
              No browser canvas video lag. Our background workers render crisp 1080×1920 MP4 files using FFmpeg with H.264 video, AAC audio, and Ken Burns camera movements.
            </p>
          </div>
        </div>

        {/* 4 Step Workflow */}
        <div className="w-full mb-24 text-left">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-[#F5F1E8] tracking-tight font-display">
              Production pipeline in four steps
            </h2>
            <p className="text-xs sm:text-sm text-[#A9A49B] mt-2">
              From script to final vertical MP4 with minimal friction.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-lg bg-[#151616] border border-[#292A29] space-y-2">
              <span className="font-mono text-xs text-[#E76536] font-bold">01</span>
              <h4 className="text-sm font-semibold text-[#F5F1E8]">Write Your Script</h4>
              <p className="text-xs text-[#A9A49B] leading-relaxed">
                Input your story or hook in English or Hindi. Set tone, voiceover accent, and visual style.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-[#151616] border border-[#292A29] space-y-2">
              <span className="font-mono text-xs text-[#E76536] font-bold">02</span>
              <h4 className="text-sm font-semibold text-[#F5F1E8]">AI Scene Breakdown</h4>
              <p className="text-xs text-[#A9A49B] leading-relaxed">
                The director splits your text into timed visual scenes, camera paths, and narration cues.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-[#151616] border border-[#292A29] space-y-2">
              <span className="font-mono text-xs text-[#E76536] font-bold">03</span>
              <h4 className="text-sm font-semibold text-[#F5F1E8]">Inject Character Memory</h4>
              <p className="text-xs text-[#A9A49B] leading-relaxed">
                Attach your locked character DNA so every generated image maintains identical facial features.
              </p>
            </div>

            <div className="p-5 rounded-lg bg-[#151616] border border-[#292A29] space-y-2">
              <span className="font-mono text-xs text-[#E76536] font-bold">04</span>
              <h4 className="text-sm font-semibold text-[#F5F1E8]">Export 1080×1920 MP4</h4>
              <p className="text-xs text-[#A9A49B] leading-relaxed">
                Background FFmpeg workers compile the video, audio, and subtitles into a ready-to-upload file.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom CTA Banner */}
        <div className="w-full rounded-xl bg-[#151616] border border-[#E76536]/30 p-8 sm:p-12 text-center space-y-5">
          <h2 className="text-2xl sm:text-3xl font-bold text-[#F5F1E8] tracking-tight font-display">
            Ready to produce your next vertical video?
          </h2>
          <p className="text-xs sm:text-sm text-[#A9A49B] max-w-xl mx-auto">
            Experience consistent characters, natural Indian voice narration, and high-definition vertical video rendering.
          </p>
          <div className="pt-2">
            <Link
              href="/projects/new"
              className="btn-primary min-h-[44px] px-8 py-3 rounded-md text-sm font-medium inline-flex items-center gap-2 shadow-sm touch-target"
            >
              <Wand2 className="w-4 h-4" />
              <span>Launch Studio Free</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
        </div>
      </main>

      {/* Editorial Footer */}
      <footer className="border-t border-[#292A29] py-6 px-4 sm:px-8 text-xs text-[#77746E] bg-[#0D0E0E]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Logo href="/" size="sm" />
            <span className="text-[#383938]">•</span>
            <span>Vertical AI Video Studio</span>
          </div>
          <div>© 2026 AkmMotion. Server-side FFmpeg &amp; Character Memory Engine.</div>
        </div>
      </footer>
    </div>
  );
}