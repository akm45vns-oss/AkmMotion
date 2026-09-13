import axios from "axios";

// Use the Next.js backend proxy in all environments EXCEPT when explicitly
// pointing to localhost (local development without proxy).
const explicitUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "";
const isLocalDev = explicitUrl.includes("localhost") || explicitUrl.includes("127.0.0.1");

// In production on Vercel: /api/backend proxies to Render (no CORS).
// In local dev: point directly at FastAPI.
export const API_BASE_URL = isLocalDev
  ? explicitUrl
  : "/api/backend";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});



// Request interceptor to attach JWT token (auto-initializes guest token if not set)
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      let token = localStorage.getItem("akmmotion_jwt_token");
      if (!token) {
        token = "guest_studio_session_token";
        localStorage.setItem("akmmotion_jwt_token", token);
      }
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling 401 Unauthorized gracefully
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.setItem("akmmotion_jwt_token", "guest_studio_session_token");
    }
    return Promise.reject(error);
  }
);