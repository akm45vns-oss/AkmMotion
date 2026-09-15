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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#292A29] pb-5">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-[#F5F1E8] tracking-tight font-display">
            Character Memory Studio (CME)
          </h1>
          <p className="text-xs sm:text-sm text-[#A9A49B] mt-1">
            Lock persistent visual identity across all scenes to ensure consistent faces, hairstyles, and outfits.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={fetchCharacters}
            className="p-2.5 rounded-lg bg-[#151616] border border-[#292A29] text-[#A9A49B] hover:text-[#F5F1E8] hover:bg-[#1B1C1C] transition-colors touch-target"
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
        <div className="p-4 rounded-lg bg-[#151616] border border-[#292A29] flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-[#1B1C1C] border border-[#292A29] text-[#A9A49B] flex items-center justify-center">
            <UserCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-[#77746E] uppercase font-semibold font-mono">Total Characters</div>
            <div className="text-lg font-bold text-[#F5F1E8] font-mono">{characters.length}</div>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-[#151616] border border-[#292A29] flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-[#E76536]/10 border border-[#E76536]/25 text-[#E76536] flex items-center justify-center">
            <Lock className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-[#77746E] uppercase font-semibold font-mono">Locked DNA</div>
            <div className="text-lg font-bold text-[#E76536] font-mono">{lockedCount} Locked</div>
          </div>
        </div>

        <div className="p-4 rounded-lg bg-[#151616] border border-[#292A29] flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-[#4FAE7B]/10 border border-[#4FAE7B]/25 text-[#4FAE7B] flex items-center justify-center">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <div className="text-[10px] text-[#77746E] uppercase font-semibold font-mono">Consistency Score</div>
            <div className="text-lg font-bold text-[#4FAE7B] font-mono">95% Match</div>
          </div>
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-[#77746E] absolute left-3.5 top-3" />
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
            <div key={i} className="h-44 rounded-lg bg-[#151616] border border-[#292A29] animate-pulse" />
          ))}
        </div>
      ) : characters.length === 0 ? (
        <div className="p-10 rounded-lg border border-dashed border-[#292A29] bg-[#151616]/40 text-center space-y-3">
          <div className="w-12 h-12 rounded-lg bg-[#1B1C1C] border border-[#292A29] flex items-center justify-center mx-auto text-[#A9A49B]">
            <UserCheck className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold text-[#F5F1E8]">No characters found</h3>
          <p className="text-xs text-[#A9A49B] max-w-sm mx-auto">
            Characters are automatically detected from script prompts or created manually for persistent identity locking.
          </p>
          <div className="pt-2">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="btn-primary text-xs touch-target inline-flex items-center gap-2"
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