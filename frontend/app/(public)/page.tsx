"use client";

import Link from "next/link";
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
    <div className="flex flex-col min-h-screen bg-[#0C0D0E] text-white selection:bg-[#E0693B]/30 selection:text-white">
      {/* Editorial Header */}
      <header className="border-b border-[#24272E] bg-[#0C0D0E]/90 backdrop-blur-md sticky top-0 z-50 px-4 sm:px-8 py-3.5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-[#E0693B] flex items-center justify-center font-bold text-white text-base shadow-sm">
            A
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-lg font-bold tracking-tight text-white">
              AkmMotion
            </span>
            <span className="hidden sm:inline-block text-[10px] font-mono px-2 py-0.5 rounded border border-[#24272E] bg-[#141517] text-[#9DA4B2]">
              STUDIO v7.3
            </span>
          </div>
        </div>

        <nav className="flex items-center gap-3 sm:gap-6">
          <Link
            href="/characters"
            className="hidden md:flex items-center gap-1.5 text-xs font-medium text-[#9DA4B2] hover:text-white transition-colors"
          >
            <UserCheck className="w-3.5 h-3.5 text-[#E0693B]" />
            <span>Character Studio</span>
          </Link>

          <Link
            href="/projects"
            className="hidden sm:flex items-center gap-1.5 text-xs font-medium text-[#9DA4B2] hover:text-white transition-colors"
          >
            <span>Projects</span>
          </Link>

          <Link
            href="/login"
            className="text-xs font-medium text-[#9DA4B2] hover:text-white transition-colors px-2 py-1.5"
          >
            Sign In
          </Link>

          <Link
            href="/projects/new"
            className="btn-primary min-h-[38px] px-4 py-2 text-xs font-medium rounded-xl inline-flex items-center gap-1.5 shadow-sm"
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>Create Video</span>
          </Link>
        </nav>
      </header>

      {/* Main Hero */}
      <main className="flex-1 flex flex-col items-center px-4 sm:px-8 pt-12 sm:pt-20 pb-20 max-w-7xl mx-auto w-full">
        {/* Architecture Highlight Badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#141517] border border-[#24272E] text-xs text-[#9DA4B2] mb-8">
          <span className="w-2 h-2 rounded-full bg-[#2EB88A] animate-pulse" />
          <span className="font-mono text-[11px] uppercase tracking-wider text-white">Character Memory Engine</span>
          <span className="text-[#333742]">•</span>
          <span className="text-[11px] text-[#9DA4B2]">Server-Side 1080×1920 MP4</span>
        </div>

        {/* Editorial Headline */}
        <div className="text-center max-w-4xl space-y-4 mb-8">
          <h1 className="text-3xl sm:text-5xl md:text-6xl font-bold tracking-tight text-white leading-[1.15]">
            Script to vertical cinema. <br className="hidden sm:inline" />
            <span className="text-[#E0693B]">Locked character consistency.</span>
          </h1>
          <p className="text-sm sm:text-lg text-[#9DA4B2] max-w-2xl mx-auto leading-relaxed font-normal">
            Turn raw scripts into production-ready vertical Shorts and Reels. Automated scene director, visual character memory, native Indian voiceovers, and server-side FFmpeg MP4 rendering in under 2 minutes.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3.5 w-full sm:w-auto mb-16 z-10">
          <Link
            href="/projects/new"
            className="btn-primary min-h-[48px] w-full sm:w-auto px-8 py-3 rounded-xl text-sm font-medium flex items-center justify-center gap-2 shadow-sm"
          >
            <Wand2 className="w-4 h-4" />
            <span>Launch Studio Project</span>
            <ArrowRight className="w-4 h-4 ml-1" />
          </Link>

          <Link
            href="/characters"
            className="btn-secondary min-h-[48px] w-full sm:w-auto px-6 py-3 rounded-xl text-sm font-medium flex items-center justify-center gap-2"
          >
            <UserCheck className="w-4 h-4 text-[#E0693B]" />
            <span>Character Studio</span>
          </Link>
        </div>

        {/* Studio Workspace Showcase */}
        <div className="w-full rounded-2xl bg-[#141517] border border-[#24272E] shadow-2xl shadow-black/60 overflow-hidden mb-24">
          {/* Mock Window Header */}
          <div className="px-5 py-3 border-b border-[#24272E] bg-[#1B1D21] flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-[#333742]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#333742]" />
                <div className="w-2.5 h-2.5 rounded-full bg-[#333742]" />
              </div>
              <span className="text-[#687082] ml-2 font-mono">/</span>
              <span className="text-white font-medium">The Sacred Temples of Varanasi</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-[#0C0D0E] border border-[#24272E] text-[#2EB88A]">
                1080 × 1920 (9:16)
              </span>
              <span className="hidden sm:inline font-mono text-[11px] text-[#687082]">
                30 FPS • H.264
              </span>
            </div>
          </div>

          {/* Mock Studio Content */}
          <div className="p-4 sm:p-8 grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            {/* 9:16 Video Player Mock */}
            <div className="lg:col-span-5 flex justify-center">
              <div className="relative w-[240px] sm:w-[280px] aspect-[9/16] rounded-2xl overflow-hidden border border-[#24272E] bg-black shadow-2xl flex flex-col justify-between p-4 group">
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
                    <div className="inline-block px-3 py-1.5 rounded-lg bg-black/85 backdrop-blur border border-white/10 text-xs font-bold text-white leading-snug">
                      <span className="text-[#E0693B]">Rahul</span> walks through the sacred ghats at dawn
                    </div>
                  </div>
                  <div className="flex items-center justify-between text-[10px] font-mono text-[#9DA4B2] pt-1">
                    <span>00:03.200</span>
                    <span>00:15.000</span>
                  </div>
                  <div className="w-full h-1 rounded-full bg-white/20 overflow-hidden">
                    <div className="w-[32%] h-full bg-[#E0693B]" />
                  </div>
                </div>
              </div>
            </div>

            {/* Studio Inspector Details */}
            <div className="lg:col-span-7 space-y-4 text-left">
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-[#E0693B]/10 border border-[#E0693B]/20 text-[#E0693B] text-xs font-medium">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>CME Active: Rahul (Archaeologist)</span>
              </div>

              <h2 className="text-xl sm:text-2xl font-bold text-white">
                Zero character drift across every frame
              </h2>

              <p className="text-xs sm:text-sm text-[#9DA4B2] leading-relaxed">
                AkmMotion&apos;s Character Memory Engine (CME) stores facial traits, clothing style, and lighting conditions in structured PostgreSQL DNA vectors. Each scene automatically injects locked visual prompts and negative prompts, ensuring your protagonist never changes face or outfit between scenes.
              </p>

              {/* Inspector Metadata Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded-xl bg-[#1B1D21] border border-[#24272E] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-white">
                    <UserCheck className="w-3.5 h-3.5 text-[#E0693B]" />
                    <span>Character DNA Lock</span>
                  </div>
                  <p className="text-[11px] text-[#687082]">
                    Rugged jacket, brown leather messenger bag, 28-year-old South Asian male.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#1B1D21] border border-[#24272E] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-white">
                    <Volume2 className="w-3.5 h-3.5 text-[#E0693B]" />
                    <span>Neural Voiceover</span>
                  </div>
                  <p className="text-[11px] text-[#687082]">
                    en-IN-PrabhatNeural • 160 WPM • Word-level timestamp alignment.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#1B1D21] border border-[#24272E] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-white">
                    <Sliders className="w-3.5 h-3.5 text-[#E0693B]" />
                    <span>Ken Burns Motion</span>
                  </div>
                  <p className="text-[11px] text-[#687082]">
                    Subtle horizontal panning (0.05 speed) with ease-in-out interpolation.
                  </p>
                </div>

                <div className="p-3.5 rounded-xl bg-[#1B1D21] border border-[#24272E] space-y-1">
                  <div className="flex items-center gap-2 text-xs font-medium text-white">
                    <Film className="w-3.5 h-3.5 text-[#E0693B]" />
                    <span>Server-Side Export</span>
                  </div>
                  <p className="text-[11px] text-[#687082]">
                    Headless FFmpeg pipeline producing 1080×1920 MP4 with AAC audio.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Mock Timeline Footer */}
          <div className="px-5 py-3 border-t border-[#24272E] bg-[#1B1D21] flex flex-wrap items-center gap-2 text-xs">
            <span className="font-mono text-[11px] text-[#687082] uppercase tracking-wider mr-2">Timeline</span>
            <div className="px-3 py-1.5 rounded-lg bg-[#E0693B]/10 border border-[#E0693B]/30 text-white font-mono text-[11px] flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[#E0693B]" />
              <span>Scene 1: 00:00 - 00:05</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-[#141517] border border-[#24272E] text-[#9DA4B2] font-mono text-[11px] flex items-center gap-2">
              <span>Scene 2: 00:05 - 00:10</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-[#141517] border border-[#24272E] text-[#9DA4B2] font-mono text-[11px] flex items-center gap-2">
              <span>Scene 3: 00:10 - 00:15</span>
            </div>
          </div>
        </div>

        {/* 3 Pillar Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mb-24 text-left">
          <div className="p-6 rounded-2xl bg-[#141517] border border-[#24272E] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#E0693B]/10 border border-[#E0693B]/20 text-[#E0693B] flex items-center justify-center font-bold">
              <UserCheck className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Persistent Character Memory</h3>
            <p className="text-xs sm:text-sm text-[#9DA4B2] leading-relaxed">
              Lock down character appearance, clothing, age, and style. The Character Memory Engine injects stored visual traits into every scene so your audience recognizes your character instantly.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-[#141517] border border-[#24272E] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#E0693B]/10 border border-[#E0693B]/20 text-[#E0693B] flex items-center justify-center font-bold">
              <Volume2 className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Indian Voiceover & Synced Subtitles</h3>
            <p className="text-xs sm:text-sm text-[#9DA4B2] leading-relaxed">
              Generate natural narration in Indian English (Prabhat, Neerja) and Hindi (Madhur, Swara). Word-level timing tokens synchronize on-screen subtitles perfectly with voice cadence.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-[#141517] border border-[#24272E] space-y-3">
            <div className="w-10 h-10 rounded-xl bg-[#E0693B]/10 border border-[#E0693B]/20 text-[#E0693B] flex items-center justify-center font-bold">
              <Film className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-white">Server-Side FFmpeg Renderer</h3>
            <p className="text-xs sm:text-sm text-[#9DA4B2] leading-relaxed">
              No browser canvas video lag. Our background workers render crisp 1080×1920 MP4 files using FFmpeg with H.264 video, AAC audio, and Ken Burns camera movements.
            </p>
          </div>
        </div>

        {/* 4 Step Workflow */}
        <div className="w-full mb-24 text-left">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Production pipeline in four steps
            </h2>
            <p className="text-xs sm:text-sm text-[#9DA4B2] mt-2">
              From script to final vertical MP4 with minimal friction.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-2">
              <span className="font-mono text-xs text-[#E0693B] font-bold">01</span>
              <h4 className="text-sm font-semibold text-white">Write Your Script</h4>
              <p className="text-xs text-[#9DA4B2] leading-relaxed">
                Input your story or hook in English or Hindi. Set tone, voiceover accent, and visual style.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-2">
              <span className="font-mono text-xs text-[#E0693B] font-bold">02</span>
              <h4 className="text-sm font-semibold text-white">AI Scene Breakdown</h4>
              <p className="text-xs text-[#9DA4B2] leading-relaxed">
                The director splits your text into timed visual scenes, camera paths, and narration cues.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-2">
              <span className="font-mono text-xs text-[#E0693B] font-bold">03</span>
              <h4 className="text-sm font-semibold text-white">Inject Character Memory</h4>
              <p className="text-xs text-[#9DA4B2] leading-relaxed">
                Attach your locked character DNA so every generated image maintains identical facial features.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-[#141517] border border-[#24272E] space-y-2">
              <span className="font-mono text-xs text-[#E0693B] font-bold">04</span>
              <h4 className="text-sm font-semibold text-white">Export 1080×1920 MP4</h4>
              <p className="text-xs text-[#9DA4B2] leading-relaxed">
                Background FFmpeg workers compile the video, audio, and subtitles into a ready-to-upload file.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom CTA Banner */}
        <div className="w-full rounded-2xl bg-[#141517] border border-[#E0693B]/30 p-8 sm:p-12 text-center space-y-5">
          <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Ready to produce your next vertical video?
          </h2>
          <p className="text-xs sm:text-sm text-[#9DA4B2] max-w-xl mx-auto">
            Experience consistent characters, natural Indian voice narration, and high-definition vertical video rendering.
          </p>
          <div className="pt-2">
            <Link
              href="/projects/new"
              className="btn-primary min-h-[48px] px-8 py-3 rounded-xl text-sm font-medium inline-flex items-center gap-2 shadow-sm"
            >
              <Wand2 className="w-4 h-4" />
              <span>Launch Studio Free</span>
              <ArrowRight className="w-4 h-4 ml-1" />
            </Link>
          </div>
        </div>
      </main>

      {/* Editorial Footer */}
      <footer className="border-t border-[#24272E] py-6 px-4 sm:px-8 text-xs text-[#687082] bg-[#0C0D0E]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-lg bg-[#E0693B] font-bold text-white flex items-center justify-center text-[10px]">
              A
            </div>
            <span className="font-semibold text-[#9DA4B2]">AkmMotion Studio</span>
            <span className="text-[#333742]">•</span>
            <span>Vertical AI Video Studio</span>
          </div>
          <div>© 2026 AkmMotion. Server-side FFmpeg &amp; Character Memory Engine.</div>
        </div>
      </footer>
    </div>
  );
}