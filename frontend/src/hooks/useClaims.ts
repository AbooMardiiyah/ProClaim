import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "../lib/api";
import { Claim, ClaimListItem, ClaimStatus, DashboardStats, Page } from "../types";

// ── List ──────────────────────────────────────────────────────────────────────
export function useClaims(params?: {
  page?: number;
  page_size?: number;
  status?: ClaimStatus;
  search?: string;
}) {
  return useQuery<Page<ClaimListItem>>({
    queryKey: ["claims", params],
    queryFn: () =>
      api
        .get("/claims", { params })
        .then((r) => r.data),
    staleTime: 30_000,
  });
}

// ── Single claim ──────────────────────────────────────────────────────────────
export function useClaim(id: string | undefined) {
  return useQuery<Claim>({
    queryKey: ["claim", id],
    queryFn: () => api.get(`/claims/${id}`).then((r) => r.data),
    enabled: !!id,
    refetchInterval: (query) => {
      // Auto-poll while claim is processing
      const claim = query.state.data;
      return claim?.status === "processing" ? 3000 : false;
    },
  });
}

// ── Create ────────────────────────────────────────────────────────────────────
export function useCreateClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post("/claims").then((r) => r.data as Claim),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claims"] }),
  });
}

// ── Upload documents ──────────────────────────────────────────────────────────
export function useUploadDocuments(claimId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (files: File[]) => {
      const form = new FormData();
      files.forEach((f) => form.append("files", f));
      return api.post(`/claims/${claimId}/documents`, form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claim", claimId] }),
  });
}

// ── Trigger extraction ────────────────────────────────────────────────────────
export function useTriggerExtraction(claimId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post(`/claims/${claimId}/extract`).then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claim", claimId] }),
  });
}

// ── Update field manually ─────────────────────────────────────────────────────
export function useUpdateField(claimId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      fieldKey,
      value,
      note,
    }: {
      fieldKey: string;
      value: string;
      note?: string;
    }) =>
      api
        .patch(`/claims/${claimId}/fields/${fieldKey}`, { value, note })
        .then((r) => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claim", claimId] }),
  });
}

// ── Status transition ─────────────────────────────────────────────────────────
export function useTransitionStatus(claimId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ status, note }: { status: ClaimStatus; note?: string }) =>
      api
        .patch(`/claims/${claimId}/status`, { status, note })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["claim", claimId] });
      qc.invalidateQueries({ queryKey: ["claims"] });
    },
  });
}

// ── Delete claim (admin only) ─────────────────────────────────────────────────
export function useDeleteClaim() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (claimId: string) => api.delete(`/claims/${claimId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["claims"] }),
  });
}

// ── Dashboard ─────────────────────────────────────────────────────────────────
export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: () => api.get("/dashboard/stats").then((r) => r.data),
    staleTime: 60_000,
  });
}

// ── Audit log ─────────────────────────────────────────────────────────────────
export function useAuditLog(claimId: string | undefined) {
  return useQuery({
    queryKey: ["audit", claimId],
    queryFn: () => api.get(`/claims/${claimId}/audit`).then((r) => r.data),
    enabled: !!claimId,
    staleTime: 15_000,
  });
}
