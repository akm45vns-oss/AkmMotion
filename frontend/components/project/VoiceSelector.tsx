"use client";

import { Check } from "lucide-react";

const voices = [
  { id: "voice_indian_en", name: "Rishi (Indian Accent English)", gender: "Male", style: "Warm & Native Accent" },
  { id: "voice_indian_hi", name: "Heera (Native Hindi Voice)", gender: "Female", style: "Authentic & Expressive" },
  { id: "voice_alloy", name: "Alloy (Narrator)", gender: "Male", style: "Calm & Direct" },
  { id: "voice_echo", name: "Echo (Energetic)", gender: "Male", style: "Upbeat & Dynamic" },
  { id: "voice_fable", name: "Fable (Storyteller)", gender: "Female", style: "Warm & Storyteller" },
  { id: "voice_onyx", name: "Onyx (Deep Voice)", gender: "Male", style: "Authoritative & Deep" },
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
                ? "border-indigo-500 bg-indigo-600/20 ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/20"
                : "border-gray-800 bg-[#0D1322] hover:border-gray-700 hover:bg-[#111827]"
            }`}
          >
            <div>
              <div className="font-bold text-sm text-white">{v.name}</div>
              <div className="text-xs text-gray-400 mt-0.5">{v.gender} • {v.style}</div>
            </div>
            <div className={`w-5 h-5 rounded-full border flex items-center justify-center transition-all ${isSelected ? "border-indigo-400 bg-indigo-500 text-white" : "border-gray-700 bg-gray-900"}`}>
              {isSelected ? <Check className="w-3.5 h-3.5" /> : null}
            </div>
          </div>
        );
      })}
    </div>
  );
}