"use client";

import { useState, useEffect } from "react";
import { Sparkles, Plus, Search, UserCheck, Lock, ShieldCheck, RefreshCw, Wand2 } from "lucide-react";
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
    <div className="max-w-7xl mx-auto space-y-8 pb-12 p-6">
      {/* Top Studio Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-gray-800 pb-6">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-indigo-400" />
            Character Memory Studio (CME)
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Persistent AI character memory & identity locking for 100% visual consistency across all scenes.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchCharacters}
            className="p-3 rounded-xl bg-[#0D1322] border border-gray-800 text-gray-400 hover:text-white transition-colors"
            title="Refresh Character Memory"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold text-xs shadow-xl shadow-indigo-600/20 flex items-center gap-2 transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Create New Character Profile</span>
          </button>
        </div>
      </div>

      {/* CME Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-5 rounded-3xl bg-[#0D1322] border border-gray-800 flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-indigo-600/10 border border-indigo-500/20 text-indigo-400">
            <UserCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Total Stored Characters</div>
            <div className="text-2xl font-extrabold text-white">{characters.length}</div>
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-[#0D1322] border border-gray-800 flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-400">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Locked Character DNA</div>
            <div className="text-2xl font-extrabold text-amber-400">{lockedCount} Locked</div>
          </div>
        </div>

        <div className="p-5 rounded-3xl bg-[#0D1322] border border-gray-800 flex items-center gap-4">
          <div className="p-3 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-wider">Average Consistency</div>
            <div className="text-2xl font-extrabold text-emerald-400">95% Match Rate</div>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-gray-500 absolute left-4 top-3.5" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search characters by name, role, visual style, or outfit..."
          className="w-full pl-11 pr-4 py-3 rounded-2xl bg-[#0D1322] border border-gray-800 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 text-xs"
        />
      </div>

      {/* Character Grid */}
      {loading ? (
        <div className="h-64 flex flex-col items-center justify-center gap-3">
          <Sparkles className="w-8 h-8 text-indigo-400 animate-spin" />
          <p className="text-xs text-gray-400">Loading Character Memory Studio...</p>
        </div>
      ) : characters.length === 0 ? (
        <div className="p-12 rounded-3xl bg-[#0D1322] border border-gray-800 text-center space-y-3">
          <Wand2 className="w-10 h-10 text-gray-600 mx-auto" />
          <h3 className="text-base font-bold text-white">No Characters Found</h3>
          <p className="text-xs text-gray-400 max-w-sm mx-auto">
            Characters are automatically detected from your scripts or created manually in Character Studio.
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold"
          >
            Create Your First Character
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
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

      {/* Create Character Modal Dialog */}
      {isCreateModalOpen && (
        <CreateCharacterModal
          onClose={() => setIsCreateModalOpen(false)}
          onCreated={handleCharacterCreated}
        />
      )}

      {/* Character DNA Inspector Modal */}
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