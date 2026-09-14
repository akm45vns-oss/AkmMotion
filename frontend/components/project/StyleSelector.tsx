"use client";

import { Check } from "lucide-react";

const styles = [
  { id: "Explainer", label: "Explainer", desc: "Step-by-step visuals & narrative text", icon: "📘" },
  { id: "Cinematic", label: "Cinematic", desc: "Dramatic lighting & mood imagery", icon: "🎬" },
  { id: "Storytelling", label: "Storytelling", desc: "Character-driven visual narrative", icon: "📖" },
  { id: "Educational", label: "Educational", desc: "Clear, informative layout & captions", icon: "💡" },
  { id: "Finance & Money", label: "Finance & Market", desc: "Sleek charts & wealth visual motifs", icon: "📈" },
  { id: "Anime / Manga", label: "Anime / Manga", desc: "Stylized expressive illustration", icon: "✨" },
];

interface StyleSelectorProps {
  selected: string;
  onSelect: (id: string) => void;
}

export default function StyleSelector({ selected, onSelect }: StyleSelectorProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
      {styles.map((s) => {
        const isSelected = selected === s.id;
        return (
          <div
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`p-3.5 rounded-xl border text-left transition-all relative select-none cursor-pointer ${
              isSelected
                ? "border-[#E0693B] bg-[#E0693B]/10 shadow-sm"
                : "border-[#24272E] bg-[#141517] hover:border-[#333742] hover:bg-[#1B1D21]"
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-xl">{s.icon}</span>
              {isSelected && (
                <div className="w-4 h-4 rounded-full bg-[#E0693B] text-white flex items-center justify-center">
                  <Check className="w-3 h-3 stroke-[3]" />
                </div>
              )}
            </div>
            <div className="font-semibold text-xs text-[#F2F2F3] mb-0.5">{s.label}</div>
            <div className="text-[11px] text-neutral-400 leading-snug">{s.desc}</div>
          </div>
        );
      })}
    </div>
  );
}