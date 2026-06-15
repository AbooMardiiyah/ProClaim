/**
 * ProClaim — Axios API Client
 * Handles auth token injection and transparent refresh.
 */
import axios, { AxiosInstance, AxiosRequestConfig } from "axios";
import { TokenPair } from "../types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8001/api/v1";

const STORAGE_KEY_ACCESS = "pc_access";
const STORAGE_KEY_REFRESH = "pc_refresh";

export const getAccessToken = () => localStorage.getItem(STORAGE_KEY_ACCESS);
export const getRefreshToken = () => localStorage.getItem(STORAGE_KEY_REFRESH);

export const setTokens = (pair: TokenPair) => {
  localStorage.setItem(STORAGE_KEY_ACCESS, pair.access_token);
  localStorage.setItem(STORAGE_KEY_REFRESH, pair.refresh_token);
};

export const clearTokens = () => {
  localStorage.removeItem(STORAGE_KEY_ACCESS);
  localStorage.removeItem(STORAGE_KEY_REFRESH);
};

// ── Axios instance ────────────────────────────────────────────────────────────
const api: AxiosInstance = axios.create({ baseURL: BASE_URL });

// Request interceptor: attach access token
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor: refresh on 401
let refreshingPromise: Promise<void> | null = null;

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config as AxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = getRefreshToken();
      if (!refresh) {
        clearTokens();
        window.location.href = "/login";
        return Promise.reject(error);
      }
      if (!refreshingPromise) {
        refreshingPromise = api
          .post<TokenPair>("/auth/refresh", { refresh_token: refresh })
          .then(({ data }) => {
            setTokens(data);
          })
          .catch(() => {
            clearTokens();
            window.location.href = "/login";
          })
          .finally(() => {
            refreshingPromise = null;
          });
      }
      await refreshingPromise;
      return api(original);
    }
    return Promise.reject(error);
  }
);

export default api;
