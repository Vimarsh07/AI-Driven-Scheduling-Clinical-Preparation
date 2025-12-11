import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 10000,
});

// Optional: log all requests
api.interceptors.request.use((config) => {
  console.info("[API request]", config.method?.toUpperCase(), config.url);
  return config;
});

// Centralize error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("[API error]", error);

    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      "Something went wrong while talking to the server.";

    // Reject with a normalized Error so components can just use err.message
    return Promise.reject(new Error(message));
  }
);

export default api;
