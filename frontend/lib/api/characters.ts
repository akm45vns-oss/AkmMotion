import { apiClient } from "./client";

export interface CharacterDNAData {
  character_code: string;
  age: number;
  gender: string;
  ethnicity?: string;
  skin_tone: string;
  hair_color: string;
  hair_style: string;
  hair_length: string;
  eye_color: string;
  face_shape: string;
  outfit: string;
  shoes: string;
  accessories: string[];
  expression: string;
  visual_style: string;
  lighting_preference: string;
  camera_preference: string;
  prompt_prefix: string;
  prompt_suffix: string;
  negative_prompt: string;
  consistency_strength: number;
}

export interface Character {
  id: string;
  user_id: string;
  project_id?: string;
  character_code: string;
  name: string;
  role: string;
  description?: string;
  is_locked: boolean;
  is_favorite: boolean;
  consistency_score: number;
  dna: CharacterDNAData;
  versions?: any[];
  scene_appearances?: number[];
  created_at: string;
  updated_at: string;
}

export const charactersApi = {
  list: async (projectId?: string, search?: string): Promise<Character[]> => {
    let url = "/characters?";
    if (projectId) url += `project_id=${projectId}&`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    const response = await apiClient.get<Character[]>(url);
    return response.data;
  },

  getById: async (id: string): Promise<Character> => {
    const response = await apiClient.get<Character>(`/characters/${id}`);
    return response.data;
  },

  create: async (data: any): Promise<Character> => {
    const response = await apiClient.post<Character>("/characters", data);
    return response.data;
  },

  lock: async (id: string): Promise<Character> => {
    const response = await apiClient.post<Character>(`/characters/${id}/lock`);
    return response.data;
  },

  unlock: async (id: string): Promise<Character> => {
    const response = await apiClient.post<Character>(`/characters/${id}/unlock`);
    return response.data;
  },

  extractFromScript: async (script: string): Promise<any> => {
    const response = await apiClient.post("/characters/extract", { script });
    return response.data;
  },
};