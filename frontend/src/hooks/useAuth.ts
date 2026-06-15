import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import api, { clearTokens, setTokens } from "../lib/api";
import { User } from "../types";

export function useMe() {
  return useQuery<User>({
    queryKey: ["me"],
    queryFn: () => api.get("/auth/me").then((r) => r.data),
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (creds: { email: string; password: string }) =>
      api.post("/auth/login", creds).then((r) => r.data),
    onSuccess: (tokens) => {
      // Clear ALL cached data from any previous session before setting new tokens
      queryClient.clear();
      setTokens(tokens);
      navigate("/dashboard");
    },
  });
}

export function useSignup() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return useMutation({
    mutationFn: (data: { email: string; password: string; full_name: string; hospital_name: string }) =>
      api.post("/auth/signup", data).then((r) => r.data),
    onSuccess: () => {
      navigate("/login");
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  return () => {
    clearTokens();
    queryClient.clear();
    navigate("/login");
  };
}
