"use client";

import { Check, Mic2 } from "lucide-react";

const voices = [
  { id: "voice_indian_en", name: "Rishi (Indian English)", gender: "Male", flag: "🇮🇳", desc: "Warm & natural native Indian English" },
  { id: "voice_indian_hi", name: "Heera (Hindi Voice)", gender: "Female", flag: "🇮🇳", desc: "Authentic & expressive Hindi narration" },
  { id: "voice_alloy", name: "Alloy (Narrator)", gender: "Neutral", flag: "🌐", desc: "Calm & direct studio pacing" },
  { id: "voice_echo", name: "Echo (Dynamic)", gender: "Male", flag: "🌐", desc: "Upbeat, energetic YouTube Shorts delivery" },
  { id: "voice_fable", name: "Fable (Storyteller)", gender: "Female", flag: "🌐", desc: "Warm, engaging storytelling timbre" },
  { id: "voice_onyx", name: "Onyx (Deep Voice)", gender: "Male", flag: "🌐", desc: "Deep & authoritative documentary style" },
];

interface VoiceSelectorProps {
  selected: string;
  onSelect: (id: string) => void;
}

export default function VoiceSelector({ selected, onSelect }: VoiceSelectorProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
      {voices.map((v) => {
        const isSelected = selected === v.id;
        return (
          <div
            key={v.id}
            onClick={() => onSelect(v.id)}
            className={`p-3.5 rounded-xl border text-left flex items-center justify-between transition-all select-none cursor-pointer ${
              isSelected
                ? "border-[#E0693B] bg-[#E0693B]/10 shadow-sm"
                : "border-[#24272E] bg-[#141517] hover:border-[#333742] hover:bg-[#1B1D21]"
            }`}
          >
            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-[#F2F2F3]">
                <span>{v.flag}</span>
                <span>{v.name}</span>
              </div>
              <div className="text-[11px] text-neutral-400">{v.gender} · {v.desc}</div>
            </div>
            <div className={`w-4 h-4 rounded-full border flex items-center justify-center transition-all ${isSelected ? "border-[#E0693B] bg-[#E0693B] text-white" : "border-[#333742] bg-[#1B1D21]"}`}>
              {isSelected ? <Check className="w-3 h-3 stroke-[3]" /> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}