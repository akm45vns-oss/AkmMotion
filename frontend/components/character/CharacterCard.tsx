"use client";

import { Lock, Unlock, User, ShieldCheck, Shirt, Palette } from "lucide-react";
import { Character } from "@/lib/api/characters";

interface CharacterCardProps {
  character: Character;
  onSelect: (char: Character) => void;
  onToggleLock: (char: Character) => void;
}

export default function CharacterCard({ character, onSelect, onToggleLock }: CharacterCardProps) {
  const dna = character.dna || {};

  return (
    <div
      onClick={() => onSelect(character)}
      className="p-5 rounded-3xl bg-[#0D1322] border border-gray-800 hover:border-indigo-500/50 shadow-xl transition-all cursor-pointer group relative flex flex-col justify-between space-y-4"
    >
      {/* Top Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-lg">
            <User className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white group-hover:text-indigo-400 transition-colors flex items-center gap-2">
              <span>{character.name}</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-gray-800 text-gray-400 font-mono">
                {character.character_code}
              </span>
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">{character.role || "Protagonist"}</p>
          </div>
        </div>

        {/* Lock Toggle Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleLock(character);
          }}
          className={`p-2 rounded-xl border transition-colors ${
            character.is_locked
              ? "bg-amber-500/10 border-amber-500/30 text-amber-400 hover:bg-amber-500/20"
              : "bg-gray-800 border-gray-700 text-gray-400 hover:text-white"
          }`}
          title={character.is_locked ? "Character Identity Locked (Consistent across scenes)" : "Unlock for editing"}
        >
          {character.is_locked ? <Lock className="w-4 h-4" /> : <Unlock className="w-4 h-4" />}
        </button>
      </div>

      {/* DNA Attributes Summary */}
      <div className="space-y-2 bg-[#090D16] p-3 rounded-2xl border border-gray-800/80 text-xs">
        <div className="flex items-center justify-between text-gray-300">
          <span className="text-gray-500">Demographics:</span>
          <span className="font-semibold text-white">
            {dna.age || 25}y · {dna.gender || "Male"} · {dna.skin_tone || "Medium"}
          </span>
        </div>

        <div className="flex items-center justify-between text-gray-300">
          <span className="text-gray-500 flex items-center gap-1">
            <Shirt className="w-3 h-3 text-indigo-400" /> Outfit:
          </span>
          <span className="font-semibold text-white truncate max-w-[170px]">{dna.outfit || "Casual Outfit"}</span>
        </div>

        <div className="flex items-center justify-between text-gray-300">
          <span className="text-gray-500 flex items-center gap-1">
            <Palette className="w-3 h-3 text-purple-400" /> Art Style:
          </span>
          <span className="font-semibold text-purple-300">{dna.visual_style || "Pixar 3D Render"}</span>
        </div>
      </div>

      {/* Footer Consistency Rating */}
      <div className="flex items-center justify-between pt-1 text-[11px]">
        <span className="text-emerald-400 font-semibold flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{character.consistency_score || 95}% DNA Consistency</span>
        </span>

        <span className="text-gray-500 text-[10px]">
          {character.is_locked ? "🔒 Locked" : "✏️ Editable"}
        </span>
      </div>
    </div>
  );
}