import axios from "axios";

const API_BASE =
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE.replace(/\/$/, ""),
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    const token =
      localStorage.getItem("soc_token") ||
      localStorage.getItem("access_token");

    if (token) {
      config.headers = config.headers || {};
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
      localStorage.removeItem("soc_token");
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
      localStorage.removeItem("role");

      if (
        window.location.pathname !== "/login" &&
        window.location.pathname !== "/signup"
      ) {
        window.location.assign("/login");
      }
    }

    return Promise.reject(error);
  }
);

export default api;

/* -------------------------------------------------------------------------- */
/* AUTH                                                                       */
/* -------------------------------------------------------------------------- */

export const loginApi = (email, password) =>
  api.post("/auth/login", {
    email,
    password,
  });

export const signupApi = (payload) =>
  api.post("/auth/signup", payload);

export const meApi = () =>
  api.get("/auth/me");

/* -------------------------------------------------------------------------- */
/* HEALTH                                                                     */
/* -------------------------------------------------------------------------- */

export const healthApi = () =>
  api.get("/health");

export const systemHealthApi = () =>
  api.get("/system/health");

/* -------------------------------------------------------------------------- */
/* ATTACKS                                                                    */
/* -------------------------------------------------------------------------- */

export const getAttacksApi = (limit = 300) =>
  api.get("/attacks", {
    params: { limit },
  });

export const getAttackApi = (attackId) =>
  api.get(`/attacks/${encodeURIComponent(attackId)}`);

export const createAttackApi = (payload) =>
  api.post("/attacks", payload);

/* -------------------------------------------------------------------------- */
/* LOGS                                                                       */
/* -------------------------------------------------------------------------- */

export const getAttackLogsApi = (params = {}) =>
  api.get("/logs", {
    params,
  });

export const exportAttackLogsApi = (params = {}) =>
  api.get("/logs/export", {
    params,
    responseType: "blob",
  });

/* -------------------------------------------------------------------------- */
/* FIREWALL                                                                   */
/* -------------------------------------------------------------------------- */

export const blockIpApi = (
  ipAddress,
  reason = "SOC analyst action"
) =>
  api.post("/firewall/block", {
    ip_address: ipAddress,
    reason,
  });

export const unblockIpApi = (
  ipAddress,
  reason = "SOC analyst action"
) =>
  api.post("/firewall/unblock", {
    ip_address: ipAddress,
    reason,
  });

export const getFirewallRulesApi = () =>
  api.get("/db/firewall-rules");

/* -------------------------------------------------------------------------- */
/* THREAT INTELLIGENCE                                                        */
/* -------------------------------------------------------------------------- */

export const checkThreatIntelApi = (ip) =>
  api.get("/threat-intel/check", {
    params: { ip },
  });

export const getGeoIntelApi = (ip) =>
  api.get("/geo/lookup", {
    params: { ip },
  });

export const huntApi = (
  sourceIp = "",
  attackType = "",
  severity = ""
) =>
  api.post("/hunting/search", {
    source_ip: sourceIp,
    attack_type: attackType,
    severity,
  });

/* -------------------------------------------------------------------------- */
/* REPORTS                                                                    */
/* -------------------------------------------------------------------------- */

export const generateReportApi = (incidentId) =>
  api.post("/reports/generate", {
    incident_id: incidentId,
  });

export const getReportsApi = (params = {}) =>
  api.get("/reports", {
    params,
  });

/* -------------------------------------------------------------------------- */
/* AI ASSISTANT                                                               */
/* -------------------------------------------------------------------------- */

export const askAssistantApi = (
  message,
  history = []
) =>
  api.post("/assistant", {
    message,
    history,
  });

/* -------------------------------------------------------------------------- */
/* SETTINGS                                                                   */
/* -------------------------------------------------------------------------- */

export const getSettingsApi = () =>
  api.get("/settings");

export const updateProfileApi = (payload) =>
  api.patch("/settings/profile", payload);

export const changePasswordApi = (payload) =>
  api.post("/settings/password", payload);

/* -------------------------------------------------------------------------- */
/* SAFE SYNTHETIC SIMULATION                                                 */
/* -------------------------------------------------------------------------- */

export const triggerDosSimulationApi = (payload = {}) =>
  api.post("/simulations/dos", payload);

/* -------------------------------------------------------------------------- */
/* INGESTION / ML / SIEM                                                      */
/* -------------------------------------------------------------------------- */

export const ingestLogsApi = (filePath) =>
  api.post("/ingestion/file", {
    file_path: filePath,
  });

export const predictRiskApi = (payload) =>
  api.post("/ml/predict", payload);

export const exportSiemApi = (limit = 500) =>
  api.get("/siem/export", {
    params: { limit },
  });