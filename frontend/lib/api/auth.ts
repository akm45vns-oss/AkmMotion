import { apiClient } from "./client";

export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  auth_provider: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export const authApi = {
  login: async (email: string, password: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/login", { email, password });
    return response.data;
  },

  register: async (email: string, password: string, fullName: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>("/auth/register", {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>("/auth/me");
    return response.data;
  },

  logout: async (): Promise<void> => {
    await apiClient.post("/auth/logout");
  },
};
