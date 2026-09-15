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
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
      {voices.map((v) => {
        const isSelected = selected === v.id;
        return (
          <button
            type="button"
            key={v.id}
            onClick={() => onSelect(v.id)}
            className={`p-3 rounded-lg border text-left flex items-center justify-between transition-all select-none cursor-pointer ${
              isSelected
                ? "border-[#E76536] bg-[#1B1C1C] ring-1 ring-[#E76536]"
                : "border-[#292A29] bg-[#151616] hover:border-[#383938] hover:bg-[#1B1C1C]"
            }`}
          >
            <div className="space-y-0.5">
              <div className="flex items-center gap-1.5 font-semibold text-xs text-[#F5F1E8]">
                <span>{v.flag}</span>
                <span>{v.name}</span>
              </div>
              <div className="text-[11px] text-[#77746E]">{v.gender} · {v.desc}</div>
            </div>
            <div className={`w-3.5 h-3.5 rounded-full border flex items-center justify-center transition-all ${isSelected ? "border-[#E76536] bg-[#E76536] text-white" : "border-[#383938] bg-[#1B1C1C]"}`}>
              {isSelected ? <Check className="w-2.5 h-2.5 stroke-[3]" /> : null}
            </div>
          </button>
        );
      })}
    </div>
  );
}