"use client";

import { useState } from "react";
import { X, UserCheck } from "lucide-react";
import { Character, charactersApi } from "@/lib/api/characters";

interface CreateCharacterModalProps {
  onClose: () => void;
  onCreated: (newCharacter: Character) => void;
}

export default function CreateCharacterModal({ onClose, onCreated }: CreateCharacterModalProps) {
  const [name, setName] = useState("");
  const [role, setRole] = useState("Protagonist");
  const [age, setAge] = useState(25);
  const [gender, setGender] = useState("Male");
  const [hairColor, setHairColor] = useState("Black");
  const [skinTone, setSkinTone] = useState("Medium");
  const [outfit, setOutfit] = useState("Casual shirt and denim jeans");
  const [visualStyle, setVisualStyle] = useState("Cinematic photorealistic");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter a character name.");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const created = await charactersApi.create({
        name: name.trim(),
        role,
        is_locked: true,
        dna: {
          age: Number(age),
          gender,
          hair_color: hairColor,
          skin_tone: skinTone,
          outfit,
          visual_style: visualStyle,
        },
      });

      onCreated(created);
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create character. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-3 sm:p-4">
      <div className="w-full max-w-lg max-h-[90vh] overflow-y-auto p-5 sm:p-6 rounded-xl bg-[#151616] border border-[#292A29] shadow-2xl relative space-y-4">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-[#292A29] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-[#1B1C1C] border border-[#292A29] text-[#E76536]">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-[#F5F1E8] font-display">Create Character Profile</h2>
              <p className="text-[11px] text-[#A9A49B]">Lock persistent visual identity for video scenes</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-md text-[#A9A49B] hover:text-[#F5F1E8] hover:bg-[#1B1C1C] transition-colors"
            aria-label="Close modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-[#C95C5C]/10 border border-[#C95C5C]/25 text-[#C95C5C] text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Character Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Rahul, Dr. Sen"
                className="input-base text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Story Role</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="Protagonist, Mentor..."
                className="input-base text-xs"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-2.5">
            <div>
              <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Age</label>
              <input
                type="number"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                className="input-base text-xs"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="input-base text-xs py-2"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Non-Binary">Non-Binary</option>
              </select>
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Skin Tone</label>
              <input
                type="text"
                value={skinTone}
                onChange={(e) => setSkinTone(e.target.value)}
                placeholder="Fair, Medium, Dark"
                className="input-base text-xs"
              />
            </div>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Hair Style & Color</label>
            <input
              type="text"
              value={hairColor}
              onChange={(e) => setHairColor(e.target.value)}
              placeholder="e.g. Short black hair, side part"
              className="input-base text-xs"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Locked Outfit</label>
            <input
              type="text"
              value={outfit}
              onChange={(e) => setOutfit(e.target.value)}
              placeholder="e.g. Navy blue blazer, white collared shirt"
              className="input-base text-xs"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-[#A9A49B] uppercase mb-1">Visual Render Style</label>
            <input
              type="text"
              value={visualStyle}
              onChange={(e) => setVisualStyle(e.target.value)}
              placeholder="e.g. Cinematic photorealistic 8k render"
              className="input-base text-xs"
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-3 border-t border-[#292A29]">
            <button type="button" onClick={onClose} className="btn-secondary text-xs touch-target">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary text-xs shadow-sm touch-target">
              {loading ? "Creating..." : "Save Character DNA"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}