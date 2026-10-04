import { useEffect, useState } from "react";
import { meApi } from "../services/api";

export function useAuth() {
  const [profile, setProfile] = useState(null);

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const token = localStorage.getItem("soc_token") || localStorage.getItem("access_token");
        if (!token) return;
        
        const meRes = await meApi();
        const data = await meRes.data;
        setProfile(data.profile || data);
      } catch {
        // ignore auth errors, keep fallback
      }
    };
    loadProfile();
  }, []);

  return { profile };
}