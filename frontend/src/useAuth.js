import { useEffect, useState } from "react";

import { meApi, loginApi, signupApi } from "./services/api";

export function useAuth() {
  const [profile, setProfile] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("soc_token") || localStorage.getItem("access_token");

    if (!token) {
      setIsAuthenticated(false);
      setIsLoading(false);
      // Do NOT navigate here - let App.jsx handle routing
      return;
    }

    const loadProfile = async () => {
      try {
        const meRes = await meApi();
        setProfile(meRes);
        setIsAuthenticated(true);
      } catch (err) {
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    loadProfile();
  }, []);

  const refreshAuth = async () => {
    setIsLoading(true);
    try {
      const meRes = await meApi();
      setProfile(meRes);
      setIsAuthenticated(true);
    } catch (err) {
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  return { profile, isAuthenticated, isLoading, refreshAuth };
}