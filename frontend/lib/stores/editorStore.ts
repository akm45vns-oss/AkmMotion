import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Scene } from "../api/scenes";
import { Project } from "../api/projects";

// ─── Types ───────────────────────────────────────────────────────────────────

export type SubtitleStyle = "yellow-cyan" | "karaoke" | "minimal";
export type AspectRatio   = "9:16" | "1:1" | "16:9";
export type VoiceLang     = "en" | "hi";
export type VoiceGender   = "male" | "female";
export type StylePreset   = "Explainer" | "Cinematic" | "Vlog" | "Anime" | "Story" | "Finance";

export interface WordTiming {
  word:  string;
  start: number;
  end:   number;
  index: number;
}

// ─── State Interface ──────────────────────────────────────────────────────────

interface EditorState {
  // Project & Scene state
  project:          Project | null;
  scenes:           Scene[];
  activeSceneId:    string | null;
  activeSceneIndex: number;
  isPlaying:        boolean;
  currentTime:      number;
  zoomLevel:        number;
  isGenerating:     boolean;
  isLoading:        boolean;

  // Quality controls (persist across sessions)
  subtitleStyle:    SubtitleStyle;
  aspectRatio:      AspectRatio;
  voiceLang:        VoiceLang;
  voiceGender:      VoiceGender;
  stylePreset:      StylePreset;

  // Karaoke runtime (ephemeral, not persisted)
  currentWordIndex: number;
  wordTimings:      WordTiming[];

  // Scene actions
  setProject:          (project: Project) => void;
  setScenes:           (scenes: Scene[]) => void;
  setActiveSceneId:    (id: string | null) => void;
  setActiveSceneIndex: (index: number) => void;
  updateSceneInStore:  (sceneId: string, updated: Partial<Scene>) => void;
  setIsPlaying:        (playing: boolean) => void;
  setCurrentTime:      (time: number) => void;
  setZoomLevel:        (zoom: number) => void;
  setIsGenerating:     (gen: boolean) => void;
  setIsLoading:        (loading: boolean) => void;

  // Quality control setters
  setSubtitleStyle:    (style: SubtitleStyle) => void;
  setAspectRatio:      (ratio: AspectRatio) => void;
  setVoiceLang:        (lang: VoiceLang) => void;
  setVoiceGender:      (gender: VoiceGender) => void;
  setStylePreset:      (preset: StylePreset) => void;

  // Karaoke runtime setters
  setCurrentWordIndex: (index: number) => void;
  setWordTimings:      (timings: WordTiming[]) => void;
  resetKaraoke:        () => void;
}

// ─── Store ────────────────────────────────────────────────────────────────────

export const useEditorStore = create<EditorState>()(
  persist(
    (set, get) => ({
      // ── Project & Scene defaults ──
      project:          null,
      scenes:           [],
      activeSceneId:    null,
      activeSceneIndex: 0,
      isPlaying:        false,
      currentTime:      0,
      zoomLevel:        1,
      isGenerating:     false,
      isLoading:        false,

      // ── Quality control defaults ──
      subtitleStyle: "yellow-cyan",
      aspectRatio:   "9:16",
      voiceLang:     "hi",
      voiceGender:   "male",
      stylePreset:   "Explainer",

      // ── Karaoke runtime defaults (not persisted) ──
      currentWordIndex: 0,
      wordTimings:      [],

      // ── Scene actions ──
      setProject: (project) => set({ project }),

      setScenes: (scenes) =>
        set({
          scenes,
          activeSceneIndex: 0,
          activeSceneId: scenes.length > 0 ? scenes[0].id : null,
        }),

      setActiveSceneId: (activeSceneId) =>
        set((state) => {
          const idx = state.scenes.findIndex((s) => s.id === activeSceneId);
          return { activeSceneId, activeSceneIndex: idx >= 0 ? idx : 0 };
        }),

      setActiveSceneIndex: (activeSceneIndex) =>
        set((state) => ({
          activeSceneIndex,
          activeSceneId: state.scenes[activeSceneIndex]?.id ?? null,
        })),

      updateSceneInStore: (sceneId, updated) =>
        set((state) => ({
          scenes: state.scenes.map((s) => (s.id === sceneId ? { ...s, ...updated } : s)),
        })),

      setIsPlaying:    (isPlaying)    => set({ isPlaying }),
      setCurrentTime:  (currentTime)  => set({ currentTime }),
      setZoomLevel:    (zoomLevel)    => set({ zoomLevel }),
      setIsGenerating: (isGenerating) => set({ isGenerating }),
      setIsLoading:    (isLoading)    => set({ isLoading }),

      // ── Quality control setters ──
      setSubtitleStyle: (subtitleStyle) => set({ subtitleStyle }),
      setAspectRatio:   (aspectRatio)   => set({ aspectRatio }),
      setVoiceLang:     (voiceLang)     => set({ voiceLang }),
      setVoiceGender:   (voiceGender)   => set({ voiceGender }),
      setStylePreset:   (stylePreset)   => set({ stylePreset }),

      // ── Karaoke runtime setters ──
      setCurrentWordIndex: (currentWordIndex) => set({ currentWordIndex }),
      setWordTimings:      (wordTimings)      => set({ wordTimings }),
      resetKaraoke: () => set({ currentWordIndex: 0, wordTimings: [] }),
    }),
    {
      name: "akmmotion-editor-prefs",
      // Only persist quality control prefs, not ephemeral runtime state
      partialize: (state) => ({
        subtitleStyle: state.subtitleStyle,
        aspectRatio:   state.aspectRatio,
        voiceLang:     state.voiceLang,
        voiceGender:   state.voiceGender,
        stylePreset:   state.stylePreset,
      }),
    }
  )
);