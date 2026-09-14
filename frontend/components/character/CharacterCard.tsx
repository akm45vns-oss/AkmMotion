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
      className="p-4 sm:p-5 rounded-xl bg-[#141517] border border-[#24272E] hover:border-[#333742] hover:bg-[#1B1D21]/60 transition-all cursor-pointer group flex flex-col justify-between space-y-3.5 select-none"
    >
      {/* Top Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-lg bg-[#1B1D21] border border-[#24272E] text-neutral-300 flex items-center justify-center font-bold text-sm">
            <User className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-[#F2F2F3] group-hover:text-[#E0693B] transition-colors flex items-center gap-1.5">
              <span>{character.name}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-[#1B1D21] text-neutral-400 font-mono">
                {character.character_code}
              </span>
            </h3>
            <p className="text-[11px] text-neutral-400">{character.role || "Protagonist"}</p>
          </div>
        </div>

        {/* Lock Toggle Button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onToggleLock(character);
          }}
          className={`p-1.5 rounded-lg border transition-colors ${
            character.is_locked
              ? "bg-[#E0693B]/10 border-[#E0693B]/30 text-[#E0693B] hover:bg-[#E0693B]/20"
              : "bg-[#1B1D21] border-[#24272E] text-neutral-400 hover:text-white"
          }`}
          title={character.is_locked ? "Character Locked (Consistent across scenes)" : "Unlock for editing"}
          aria-label={character.is_locked ? "Unlock character" : "Lock character"}
        >
          {character.is_locked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
        </button>
      </div>

      {/* DNA Attributes Summary */}
      <div className="space-y-1.5 bg-[#0C0D0E] p-2.5 rounded-lg border border-[#24272E] text-xs">
        <div className="flex items-center justify-between text-neutral-400 text-[11px]">
          <span>Demographics:</span>
          <span className="font-medium text-[#F2F2F3]">
            {dna.age || 25}y · {dna.gender || "Male"} · {dna.skin_tone || "Medium"}
          </span>
        </div>

        <div className="flex items-center justify-between text-neutral-400 text-[11px]">
          <span className="flex items-center gap-1">
            <Shirt className="w-3 h-3 text-[#E0693B]" /> Outfit:
          </span>
          <span className="font-medium text-[#F2F2F3] truncate max-w-[150px]">{dna.outfit || "Casual"}</span>
        </div>

        <div className="flex items-center justify-between text-neutral-400 text-[11px]">
          <span className="flex items-center gap-1">
            <Palette className="w-3 h-3 text-[#E0693B]" /> Style:
          </span>
          <span className="font-medium text-neutral-300">{dna.visual_style || "Pixar 3D Render"}</span>
        </div>
      </div>

      {/* Footer Consistency Rating */}
      <div className="flex items-center justify-between pt-1 text-[11px]">
        <span className="text-[#2EB88A] font-medium flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>{character.consistency_score || 95}% Consistency</span>
        </span>

        <span className="text-neutral-500 text-[10px]">
          {character.is_locked ? "🔒 Locked" : "✏️ Editable"}
        </span>
      </div>
    </div>
  );
}