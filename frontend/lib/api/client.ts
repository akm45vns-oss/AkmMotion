import axios from "axios";

// In production (Vercel), route through Next.js proxy to avoid CORS.
// In development, call the local FastAPI server directly.
const isProduction = typeof window !== "undefined" && !window.location.hostname.includes("localhost");
export const API_BASE_URL = isProduction
  ? "/api/backend"  // Vercel proxy → no CORS
  : (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1");

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