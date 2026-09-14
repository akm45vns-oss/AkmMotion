"use client";

import { useState } from "react";
import { X, Lock, Unlock, User, Shirt, Palette, Check } from "lucide-react";
import { Character } from "@/lib/api/characters";

interface CharacterDNAInspectorProps {
  character: Character;
  onClose: () => void;
  onSave: (updatedChar: Character) => void;
}

export default function CharacterDNAInspector({ character, onClose, onSave }: CharacterDNAInspectorProps) {
  const [dna, setDna] = useState(character.dna || {});
  const [isLocked, setIsLocked] = useState(character.is_locked);
  const [name, setName] = useState(character.name);
  const [role, setRole] = useState(character.role || "Protagonist");

  const handleChange = (field: string, val: any) => {
    setDna((prev: any) => ({ ...prev, [field]: val }));
  };

  const handleSave = () => {
    const updated = {
      ...character,
      name,
      role,
      is_locked: isLocked,
      dna,
    };
    onSave(updated);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="w-full max-w-xl max-h-[90vh] overflow-y-auto rounded-2xl bg-[#141517] border border-[#24272E] shadow-2xl relative p-5 sm:p-6 space-y-5">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-[#1B1D21] transition-colors"
          aria-label="Close inspector"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center justify-between border-b border-[#24272E] pb-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[#1B1D21] border border-[#24272E] text-[#E0693B]">
              <User className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-[#F2F2F3] flex items-center gap-2">
                <span>{name}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-[#1B1D21] text-neutral-400 font-mono">
                  {character.character_code}
                </span>
              </h2>
              <p className="text-xs text-neutral-400">Character Memory Engine DNA Profile</p>
            </div>
          </div>

          <button
            onClick={() => setIsLocked(!isLocked)}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-colors ${
              isLocked
                ? "bg-[#E0693B]/10 border-[#E0693B]/30 text-[#E0693B]"
                : "bg-[#1B1D21] border-[#24272E] text-neutral-300"
            }`}
          >
            {isLocked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
            <span>{isLocked ? "Locked" : "Unlocked"}</span>
          </button>
        </div>

        {/* Demographics */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-neutral-300 uppercase tracking-wider">
            1. Identity & Demographics
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="input-base text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Role</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="input-base text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Age</label>
              <input
                type="number"
                value={dna.age || 25}
                onChange={(e) => handleChange("age", Number(e.target.value))}
                className="input-base text-xs"
              />
            </div>
          </div>
        </div>

        {/* Appearance & Physical Traits */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-neutral-300 uppercase tracking-wider">
            2. Appearance & Features
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Gender</label>
              <select
                value={dna.gender || "Male"}
                onChange={(e) => handleChange("gender", e.target.value)}
                className="input-base text-xs py-2"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Non-Binary">Non-Binary</option>
              </select>
            </div>
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Skin Tone</label>
              <input
                type="text"
                value={dna.skin_tone || "Medium"}
                onChange={(e) => handleChange("skin_tone", e.target.value)}
                className="input-base text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Hair Style & Color</label>
              <input
                type="text"
                value={dna.hair_color || "Black wavy hair"}
                onChange={(e) => handleChange("hair_color", e.target.value)}
                className="input-base text-xs"
              />
            </div>
          </div>
        </div>

        {/* Outfit & Visual Style */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-neutral-300 uppercase tracking-wider flex items-center gap-1.5">
            <Shirt className="w-3.5 h-3.5 text-[#E0693B]" />
            <span>3. Outfit & Visual Style</span>
          </h3>
          <div className="space-y-2 text-xs">
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Locked Outfit Description</label>
              <input
                type="text"
                value={dna.outfit || "Casual dark shirt and denim jeans"}
                onChange={(e) => handleChange("outfit", e.target.value)}
                className="input-base text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] text-neutral-400 mb-1">Visual Render Style</label>
              <input
                type="text"
                value={dna.visual_style || "Cinematic photorealistic 8k render"}
                onChange={(e) => handleChange("visual_style", e.target.value)}
                className="input-base text-xs"
              />
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#24272E]">
          <button onClick={onClose} className="btn-secondary text-xs">
            Cancel
          </button>
          <button onClick={handleSave} className="btn-primary text-xs shadow-sm">
            Save Character DNA
          </button>
        </div>
      </div>
    </div>
  );
}