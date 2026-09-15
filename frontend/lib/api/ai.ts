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

  generateSceneVideo: async (
    sceneId: string,
    prompt?: string,
    duration?: string
  ): Promise<{
    job_id: string;
    status: string;
    scene_id: string;
    provider: string;
    message?: string;
  }> => {
    const response = await apiClient.post("/ai/generate-scene-video", {
      scene_id: sceneId,
      prompt,
      duration: duration || "5",
      aspect_ratio: "9:16",
    });
    return response.data;
  },

  getVideoJobStatus: async (
    jobId: string
  ): Promise<{
    job_id: string;
    status: string;
    scene_id: string;
    video_url?: string;
    error?: string;
  }> => {
    const response = await apiClient.get(`/ai/video-jobs/${jobId}`);
    return response.data;
  },
};
