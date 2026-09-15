"use client";

import { Check } from "lucide-react";

const styles = [
  { id: "Cinematic", label: "Cinematic", desc: "Dramatic lighting & 8k photorealistic depth" },
  { id: "Explainer", label: "Explainer", desc: "Crisp documentary aesthetic & authentic subjects" },
  { id: "Story",     label: "Story",     desc: "Warm golden-hour narrative storytelling" },
  { id: "Anime",     label: "Anime",     desc: "Makoto Shinkai aesthetic & cel-shaded color" },
];

interface StyleSelectorProps {
  selected: string;
  onSelect: (id: string) => void;
}

export default function StyleSelector({ selected, onSelect }: StyleSelectorProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
      {styles.map((s) => {
        const isSelected = selected === s.id;
        return (
          <button
            type="button"
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`p-3 rounded-lg border text-left transition-all relative select-none cursor-pointer ${
              isSelected
                ? "border-[#E76536] bg-[#1B1C1C] ring-1 ring-[#E76536]"
                : "border-[#292A29] bg-[#151616] hover:border-[#383938] hover:bg-[#1B1C1C]"
            }`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="font-semibold text-xs text-[#F5F1E8]">{s.label}</span>
              {isSelected && (
                <div className="w-3.5 h-3.5 rounded-full bg-[#E76536] text-white flex items-center justify-center">
                  <Check className="w-2.5 h-2.5 stroke-[3]" />
                </div>
              )}
            </div>
            <p className="text-[11px] text-[#77746E] leading-snug">{s.desc}</p>
          </button>
        );
      })}
    </div>
  );
}