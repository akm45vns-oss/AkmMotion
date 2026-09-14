"use client";

import { useState, useEffect } from "react";
import { Plus, Search, UserCheck, Lock, ShieldCheck, RefreshCw } from "lucide-react";
import CharacterCard from "@/components/character/CharacterCard";
import CharacterDNAInspector from "@/components/character/CharacterDNAInspector";
import CreateCharacterModal from "@/components/character/CreateCharacterModal";
import { charactersApi, Character } from "@/lib/api/characters";

export default function CharacterStudioPage() {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedCharacter, setSelectedCharacter] = useState<Character | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchCharacters = async () => {
    setLoading(true);
    try {
      const data = await charactersApi.list(undefined, search);
      setCharacters(data);
    } catch (err) {
      console.error("Failed to load characters:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCharacters();
  }, [search]);

  const handleToggleLock = async (char: Character) => {
    try {
      const updated = char.is_locked
        ? await charactersApi.unlock(char.id)
        : await charactersApi.lock(char.id);

      setCharacters((prev) =>
        prev.map((c) => (c.id === updated.id ? updated : c))
      );
    } catch (err) {
      console.error("Failed to toggle character lock:", err);
    }
  };

  const handleCharacterCreated = (newChar: Character) => {
    setCharacters((prev) => [newChar, ...prev]);
  };

  const lockedCount = characters.filter((c) => c.is_locked).length;

  return (
    <div className="max-w-6xl mx-auto space-y-6 pb-12">
      {/* Top Studio Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#24272E] pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#F2F2F3] tracking-tight">
            Character Memory Studio (CME)
          </h1>
          <p className="text-xs sm:text-sm text-neutral-400 mt-1">
            Lock persistent visual identity across all scenes to ensure consistent faces, hairstyles, and outfits.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchCharacters}
            className="p-2.5 rounded-xl bg-[#141517] border border-[#24272E] text-neutral-400 hover:text-white transition-colors"
            title="Refresh Characters"
            aria-label="Refresh Characters"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="btn-primary text-xs flex items-center gap-1.5 shadow-sm touch-target"
          >
            <Plus className="w-4 h-4" />
            <span>Create Character</span>
          </button>
        </div>
      </div>

      {/* CME Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        <div className="p-4 rounded-xl bg-[#141517] border border-[#24272E] flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#1B1D21] border border-[#24272E] text-neutral-300 flex items-center justify-center">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-neutral-400 uppercase font-semibold">Total Characters</div>
            <div className="text-lg font-bold text-[#F2F2F3]">{characters.length}</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#141517] border border-[#24272E] flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#E0693B]/10 border border-[#E0693B]/25 text-[#E0693B] flex items-center justify-center">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-neutral-400 uppercase font-semibold">Locked DNA</div>
            <div className="text-lg font-bold text-[#E0693B]">{lockedCount} Locked</div>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#141517] border border-[#24272E] flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-[#2EB88A]/10 border border-[#2EB88A]/25 text-[#2EB88A] flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-neutral-400 uppercase font-semibold">Consistency Score</div>
            <div className="text-lg font-bold text-[#2EB88A]">95% Match</div>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-neutral-500 absolute left-3.5 top-3" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search characters by name, role, visual style, or outfit..."
          className="input-base text-xs pl-10 py-2.5"
        />
      </div>

      {/* Character Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-44 rounded-xl bg-[#141517] border border-[#24272E] animate-pulse" />
          ))}
        </div>
      ) : characters.length === 0 ? (
        <div className="p-10 rounded-xl border border-dashed border-[#24272E] bg-[#141517]/40 text-center space-y-3">
          <div className="w-12 h-12 rounded-xl bg-[#1B1D21] border border-[#24272E] flex items-center justify-center mx-auto text-neutral-400">
            <UserCheck className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-[#F2F2F3]">No characters found</h3>
          <p className="text-xs text-neutral-400 max-w-sm mx-auto">
            Characters are automatically detected from script prompts or created manually for persistent identity locking.
          </p>
          <div className="pt-2">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="btn-primary text-xs"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Create Character</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {characters.map((char) => (
            <CharacterCard
              key={char.id}
              character={char}
              onSelect={setSelectedCharacter}
              onToggleLock={handleToggleLock}
            />
          ))}
        </div>
      )}

      {/* Create Modal Dialog */}
      {isCreateModalOpen && (
        <CreateCharacterModal
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={handleCharacterCreated}
        />
      )}

      {/* DNA Inspector Modal */}
      {selectedCharacter && (
        <CharacterDNAInspector
          character={selectedCharacter}
          onClose={() => setSelectedCharacter(null)}
          onSave={(updated) => {
            setCharacters((prev) =>
              prev.map((c) => (c.id === updated.id ? updated : c))
            );
            setSelectedCharacter(null);
          }}
        />
      )}
    </div>
  );
}