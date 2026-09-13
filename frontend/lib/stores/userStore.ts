import { create } from "zustand";
import { User } from "../api/auth";

interface UserState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
}

export const useUserStore = create<UserState>((set) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("akmmotion_jwt_token") : null,
  isAuthenticated: false,
  isLoading: true,

  setAuth: (user, token) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("akmmotion_jwt_token", token);
    }
    set({ user, token, isAuthenticated: true, isLoading: false });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("akmmotion_jwt_token");
    }
    set({ user: null, token: null, isAuthenticated: false, isLoading: false });
  },
}));
