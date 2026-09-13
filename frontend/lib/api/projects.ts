import { apiClient } from "./client";

export interface ScriptData {
  id: string;
  project_id: string;
  content: string;
  word_count?: number;
  estimated_duration?: number;
  language: string;
  status: string;
}

export interface Project {
  id: string;
  user_id: string;
  title: string;
  description?: string;
  style: string;
  language: string;
  status: string;
  thumbnail_url?: string;
  created_at: string;
  updated_at: string;
  script?: ScriptData;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  limit: number;
}

export const projectsApi = {
  list: async (page = 1, limit = 20): Promise<ProjectListResponse> => {
    const response = await apiClient.get<ProjectListResponse>(`/projects?page=${page}&limit=${limit}`);
    return response.data;
  },

  get: async (id: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/projects/${id}`);
    return response.data;
  },

  getById: async (id: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/projects/${id}`);
    return response.data;
  },

  create: async (data: { title: string; description?: string; style: string; language: string; script_content?: string }): Promise<Project> => {
    const response = await apiClient.post<Project>("/projects", data);
    return response.data;
  },

  update: async (id: string, data: Partial<Project>): Promise<Project> => {
    const response = await apiClient.put<Project>(`/projects/${id}`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
  },
};