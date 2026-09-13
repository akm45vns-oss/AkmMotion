import { apiClient } from "./client";

export interface RenderJob {
  id: string;
  project_id: string;
  user_id: string;
  status: "pending" | "processing" | "completed" | "failed" | "cancelled";
  progress: number;
  error_message?: string;
  estimated_seconds?: number;
  created_at: string;
  updated_at: string;
}

export const renderApi = {
  start: async (projectId: string): Promise<RenderJob> => {
    const response = await apiClient.post<RenderJob>(`/render/start/${projectId}`);
    return response.data;
  },

  getStatus: async (jobId: string): Promise<RenderJob> => {
    const response = await apiClient.get<RenderJob>(`/render/status/${jobId}`);
    return response.data;
  },
};
