"use client";

import { useState } from "react";
import { X, Lock, Unlock, Sparkles, ShieldCheck, User, Shirt, Palette, Camera, Sliders } from "lucide-react";
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
    setDna((prev) => ({ ...prev, [field]: val }));
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
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-2xl rounded-3xl bg-[#0D1322] border border-gray-800 shadow-2xl relative p-6 space-y-6 max-h-[90vh] overflow-y-auto scrollbar-thin">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-full text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
              <User className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>{name}</span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-gray-800 text-gray-400 font-mono">
                  {character.character_code}
                </span>
              </h2>
              <p className="text-xs text-gray-400">Character DNA & Visual Consistency Inspector</p>
            </div>
          </div>

          <button
            onClick={() => setIsLocked(!isLocked)}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-colors ${
              isLocked
                ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                : "bg-gray-800 border-gray-700 text-gray-300"
            }`}
          >
            {isLocked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
            <span>{isLocked ? "Character Locked" : "Character Unlocked"}</span>
          </button>
        </div>

        {/* Demographics & Core Identity */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
            <User className="w-3.5 h-3.5" /> 1. Identity & Demographics
          </h3>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Role</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Age</label>
              <input
                type="number"
                value={dna.age || 25}
                onChange={(e) => handleChange("age", parseInt(e.target.value))}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Facial Features & Hair */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-purple-400 uppercase tracking-wider flex items-center gap-1.5">
            <Sliders className="w-3.5 h-3.5" /> 2. Facial Features & Hair
          </h3>
          <div className="grid grid-cols-3 gap-3 text-xs">
            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Hair Color</label>
              <input
                type="text"
                value={dna.hair_color || "Black"}
                onChange={(e) => handleChange("hair_color", e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Hair Style</label>
              <input
                type="text"
                value={dna.hair_style || "Short neat"}
                onChange={(e) => handleChange("hair_style", e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Skin Tone</label>
              <input
                type="text"
                value={dna.skin_tone || "Medium"}
                onChange={(e) => handleChange("skin_tone", e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Outfit & Visual Style */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-pink-400 uppercase tracking-wider flex items-center gap-1.5">
            <Shirt className="w-3.5 h-3.5" /> 3. Outfit & Visual Style
          </h3>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Outfit Description</label>
              <input
                type="text"
                value={dna.outfit || "Casual blue hoodie and black jeans"}
                onChange={(e) => handleChange("outfit", e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-[10px] text-gray-400 mb-1">Visual Art Style</label>
              <select
                value={dna.visual_style || "Pixar 3D Render"}
                onChange={(e) => handleChange("visual_style", e.target.value)}
                className="w-full p-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="Pixar 3D Render">Pixar 3D Render</option>
                <option value="Anime / Manga">Anime / Manga</option>
                <option value="Hyper-Realistic 8k">Hyper-Realistic 8k</option>
                <option value="Comic Book Art">Comic Book Art</option>
                <option value="Flat Illustration">Flat Illustration</option>
                <option value="Watercolor Painting">Watercolor Painting</option>
              </select>
            </div>
          </div>
        </div>

        {/* Prompt Injection Summary */}
        <div className="p-4 rounded-2xl bg-[#090D16] border border-gray-800/80 space-y-2">
          <div className="flex items-center justify-between text-xs font-bold text-emerald-400">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4" /> Prompt Injection Preview
            </span>
            <span className="text-[10px] text-gray-500">Auto-injected into scene prompts</span>
          </div>
          <p className="text-xs text-gray-300 leading-relaxed font-mono bg-black/50 p-3 rounded-xl border border-gray-800">
            Character {character.character_code}: {dna.age || 25}yo {dna.gender || "Male"}, {dna.hair_style || "Short neat"} {dna.hair_color || "Black"} hair, {dna.skin_tone || "Medium"} skin, wearing {dna.outfit || "Outfit"}, {dna.visual_style || "Pixar 3D Render"} style.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end gap-3 pt-2 border-t border-gray-800">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-semibold"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/20"
          >
            Save Character DNA Changes
          </button>
        </div>
      </div>
    </div>
  );
}