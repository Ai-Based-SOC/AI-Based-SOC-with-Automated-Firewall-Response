import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8001/api/v1";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("soc_token") || localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // clear stale auth
      localStorage.removeItem("soc_token");
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      localStorage.removeItem("role");

      // IMPORTANT: avoid redirect loop on /login
      if (window.location.pathname !== "/login") {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const loginApi = (email, password) => api.post("/auth/login", { email, password });
export const meApi = () => api.get("/auth/me");

// Health
export const healthApi = () => api.get("/health");

// Attacks
export const getAttacksApi = (limit = 100) => api.get("/attacks", { params: { limit } });
export const createAttackApi = (payload) => api.post("/attacks", payload);

// Firewall
export const blockIpApi = (ip_address, reason = "SOC analyst action") =>
  api.post("/firewall/block", { ip_address, reason });

export const unblockIpApi = (ip_address, reason = "SOC analyst action") =>
  api.post("/firewall/unblock", { ip_address, reason });

// Threat intel / geo / hunting
export const checkThreatIntelApi = (ip) => api.get("/threat-intel/check", { params: { ip } });
export const getGeoIntelApi = (ip) => api.get("/geo/lookup", { params: { ip } });
export const huntApi = (source_ip = "", attack_type = "", severity = "") =>
  api.post("/hunting/search", { source_ip, attack_type, severity });

// Reports
export const generateReportApi = (incident_id) =>
  api.post("/reports/generate", { incident_id });

// Ingestion
export const ingestLogsApi = (file_path) =>
  api.post("/ingestion/file", { file_path });