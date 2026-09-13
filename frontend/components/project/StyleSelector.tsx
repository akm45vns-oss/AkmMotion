"use client";

import { Check } from "lucide-react";

const styles = [
  { id: "Educational", label: "Educational", desc: "Clear, engaging, informative layout", color: "from-blue-600 to-indigo-600" },
  { id: "Explainer", label: "Explainer", desc: "Step-by-step visuals & text popups", color: "from-indigo-600 to-purple-600" },
  { id: "Cinematic", label: "Cinematic", desc: "Dramatic lighting & mood imagery", color: "from-purple-600 to-pink-600" },
  { id: "Storytelling", label: "Storytelling", desc: "Character driven visual narrative", color: "from-amber-600 to-orange-600" },
  { id: "Finance & Money", label: "Finance & Money", desc: "Sleek charts, gold/green tones", color: "from-emerald-600 to-teal-600" },
  { id: "Anime / Manga", label: "Anime / Manga", desc: "Vibrant stylized illustration", color: "from-rose-600 to-red-600" },
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
            className={`p-4 rounded-xl border text-left transition-all relative overflow-hidden select-none cursor-pointer ${
              isSelected
                ? "border-indigo-500 bg-indigo-600/20 ring-2 ring-indigo-500 shadow-xl shadow-indigo-500/20"
                : "border-gray-800 bg-[#0D1322] hover:border-gray-700 hover:bg-[#111827]"
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className={`w-8 h-8 rounded-lg bg-gradient-to-tr ${s.color} flex items-center justify-center font-bold text-xs text-white shadow-md`} />
              {isSelected && (
                <div className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow">
                  <Check className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
            <div className="font-bold text-sm text-white mb-0.5">{s.label}</div>
            <div className="text-[11px] text-gray-400 leading-tight">{s.desc}</div>
          </div>
        );
      })}
    </div>
  );
}