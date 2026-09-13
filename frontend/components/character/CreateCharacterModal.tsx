"use client";

import { useState } from "react";
import { X, Sparkles, UserCheck, ShieldCheck } from "lucide-react";
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
  const [visualStyle, setVisualStyle] = useState("Pixar 3D Render");
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
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-lg p-6 rounded-3xl bg-[#0D1322] border border-gray-800 shadow-2xl relative space-y-6">
        {/* Top Header */}
        <div className="flex items-center justify-between border-b border-gray-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Create AI Character Profile</h2>
              <p className="text-xs text-gray-400">Lock persistent DNA identity across all video scenes</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-full text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">Character Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Rahul, Dr. Sharma"
                className="w-full px-3 py-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">Story Role</label>
              <select
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="Protagonist">Protagonist (Hero)</option>
                <option value="Antagonist">Antagonist (Villain)</option>
                <option value="Mentor">Mentor / Guide</option>
                <option value="Supporting">Supporting Character</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">Age</label>
              <input
                type="number"
                min="1"
                max="100"
                value={age}
                onChange={(e) => setAge(Number(e.target.value))}
                className="w-full px-3 py-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">Gender</label>
              <select
                value={gender}
                onChange={(e) => setGender(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Non-binary">Non-binary</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">Hair Color</label>
              <input
                type="text"
                value={hairColor}
                onChange={(e) => setHairColor(e.target.value)}
                className="w-full px-3 py-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">Locked Outfit Description</label>
            <input
              type="text"
              value={outfit}
              onChange={(e) => setOutfit(e.target.value)}
              placeholder="e.g. Yellow hoodie and black sunglasses"
              className="w-full px-3 py-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-300 uppercase mb-1">Art / Visual Style</label>
            <select
              value={visualStyle}
              onChange={(e) => setVisualStyle(e.target.value)}
              className="w-full px-3 py-2.5 rounded-xl bg-[#090D16] border border-gray-800 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="Pixar 3D Render">Pixar 3D Render</option>
              <option value="Photorealistic 8K">Photorealistic 8K Cinema</option>
              <option value="Anime Studio Ghibli">Anime Studio Ghibli</option>
              <option value="Cyberpunk Digital Art">Cyberpunk Digital Art</option>
            </select>
          </div>

          <div className="flex items-center gap-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs">
            <ShieldCheck className="w-4 h-4 flex-shrink-0" />
            <span>Character DNA will be locked automatically for 100% prompt consistency.</span>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2.5 rounded-xl bg-gray-800 text-xs text-gray-300 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {loading ? "Creating Character..." : "Create Character DNA"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}