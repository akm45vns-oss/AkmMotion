import { apiClient } from "./client";

export interface SceneAsset {
  id: string;
  scene_id: string;
  asset_type: "image" | "audio" | "video" | "subtitle";
  url: string;
  storage_path: string;
  metadata_json?: any;
}

export interface Scene {
  id: string;
  project_id: string;
  script_id: string;
  scene_number: number;
  duration: number;
  narration: string;
  subtitle: string;
  image_prompt: string;
  animation_style: string;
  transition: string;
  camera_motion: string;
  emotion?: string;
  status: string;
  created_at: string;
  updated_at: string;
  assets: SceneAsset[];
}

export const scenesApi = {
  getForProject: async (projectId: string): Promise<Scene[]> => {
    const response = await apiClient.get<Scene[]>(`/scenes/project/${projectId}`);
    return response.data;
  },

  getByProjectId: async (projectId: string): Promise<Scene[]> => {
    const response = await apiClient.get<Scene[]>(`/scenes/project/${projectId}`);
    return response.data;
  },

  update: async (sceneId: string, data: Partial<Scene>): Promise<Scene> => {
    const response = await apiClient.put<Scene>(`/scenes/${sceneId}`, data);
    return response.data;
  },

  reorder: async (items: { scene_id: string; scene_number: number }[]): Promise<void> => {
    await apiClient.post("/scenes/reorder", { items });
  },

  delete: async (sceneId: string): Promise<void> => {
    await apiClient.delete(`/scenes/${sceneId}`);
  },
};