import { apiClient } from "./client";
import { Project } from "./projects";

export const aiApi = {
  generatePipeline: async (projectId: string): Promise<Project> => {
    const response = await apiClient.post<Project>(`/ai/generate-pipeline/${projectId}`);
    return response.data;
  },

  getVoices: async () => {
    const response = await apiClient.get("/ai/voices");
    return response.data;
  },

  getStyles: async () => {
    const response = await apiClient.get("/ai/styles");
    return response.data;
  },
};
