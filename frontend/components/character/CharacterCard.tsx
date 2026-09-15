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
      className="p-4 sm:p-5 rounded-lg bg-[#151616] border border-[#292A29] hover:border-[#383938] hover:bg-[#1B1C1C] transition-all cursor-pointer group flex flex-col justify-between space-y-3.5 select-none"
    >
      {/* Top Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-md bg-[#1B1C1C] border border-[#292A29] text-[#A9A49B] flex items-center justify-center font-bold text-sm">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#F5F1E8] group-hover:text-[#E76536] transition-colors flex items-center gap-1.5 font-display">
              <span>{character.name}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#1B1C1C] border border-[#292A29] text-[#77746E] font-mono">
                {character.character_code}
              </span>
            </h3>
            <p className="text-[11px] text-[#A9A49B]">{character.role || "Protagonist"}</p>
          </div>
        </div>

        {/* Lock Toggle Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleLock(character);
          }}
          className={`p-1.5 rounded-md border transition-colors touch-target ${
            character.is_locked
              ? "bg-[#E76536]/10 border-[#E76536]/30 text-[#E76536] hover:bg-[#E76536]/20"
              : "bg-[#1B1C1C] border-[#292A29] text-[#A9A49B] hover:text-[#F5F1E8]"
          }`}
          title={character.is_locked ? "Character Locked (Consistent across scenes)" : "Unlock for editing"}
          aria-label={character.is_locked ? "Unlock character" : "Lock character"}
        >
          {character.is_locked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* DNA Attributes Summary */}
      <div className="space-y-1.5 bg-[#0D0E0E] p-2.5 rounded-md border border-[#292A29] text-xs">
        <div className="flex items-center justify-between text-[#A9A49B] text-[11px]">
          <span>Demographics:</span>
          <span className="font-medium text-[#F5F1E8]">
            {dna.age || 25}y · {dna.gender || "Male"} · {dna.skin_tone || "Medium"}
          </span>
        </div>

        <div className="flex items-center justify-between text-[#A9A49B] text-[11px]">
          <span className="flex items-center gap-1">
            <Shirt className="w-3 h-3 text-[#E76536]" /> Outfit:
          </span>
          <span className="font-medium text-[#F5F1E8] truncate max-w-[150px]">{dna.outfit || "Casual"}</span>
        </div>

        <div className="flex items-center justify-between text-[#A9A49B] text-[11px]">
          <span className="flex items-center gap-1">
            <Palette className="w-3 h-3 text-[#E76536]" /> Style:
          </span>
          <span className="font-medium text-[#A9A49B]">{dna.visual_style || "Pixar 3D Render"}</span>
        </div>
      </div>

      {/* Footer Consistency Rating */}
      <div className="flex items-center justify-between pt-1 text-[11px]">
        <span className="text-[#4FAE7B] font-medium flex items-center gap-1 font-mono">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{character.consistency_score || 95}% Consistency</span>
        </span>

        <span className="text-[#77746E] text-[10px]">
          {character.is_locked ? "🔒 Locked" : "✏️ Editable"}
        </span>
      </div>
    </div>
  );
}