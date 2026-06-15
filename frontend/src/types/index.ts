// ProClaim — Shared TypeScript Types

export type UserRole = "admin" | "billing_officer";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  hospital_id: string;
  hospital_name: string | null;
  is_active: boolean;
  created_at: string;
}

export type ClaimStatus =
  | "draft"
  | "processing"
  | "extracted"
  | "under_review"
  | "ready"
  | "submitted"
  | "paid"
  | "rejected";

export type FieldStatus = "extracted" | "missing" | "manual" | "verified";

export interface ClaimDocument {
  id: string;
  file_name: string;
  file_size_bytes: number;
  mime_type: string;
  document_type: string | null;
  page_count: number | null;
  created_at: string;
}

export interface ClaimField {
  id: string;
  field_key: string;
  field_label: string;
  value: string | null;
  confidence_score: number | null;
  status: FieldStatus;
  source_document_id: string | null;
  page_number: number | null;
  bounding_box: Record<string, unknown> | null;
}

export interface Claim {
  id: string;
  reference_number: string;
  patient_name: string | null;
  nhia_id: string | null;
  date_of_service: string | null;
  hospital_id: string;
  hospital_name: string | null;
  primary_diagnosis: string | null;
  icd10_code: string | null;
  procedure_desc: string | null;
  nhia_tariff_code: string | null;
  physician_name: string | null;
  physician_id: string | null;
  total_cost: string | null;
  consultation_fee: string | null;
  drug_cost: string | null;
  lab_cost: string | null;
  status: ClaimStatus;
  rejection_reason: string | null;
  submission_reference: string | null;
  created_at: string;
  updated_at: string;
  documents: ClaimDocument[];
  fields: ClaimField[];
}

export interface ClaimListItem {
  id: string;
  reference_number: string;
  patient_name: string | null;
  nhia_id: string | null;
  date_of_service: string | null;
  status: ClaimStatus;
  total_cost: string | null;
  created_at: string;
  document_count: number;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditLog {
  id: string;
  claim_id: string;
  user_id: string | null;
  action: string;
  field_name: string | null;
  old_value: string | null;
  new_value: string | null;
  source_type: string | null;
  note: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_claims: number;
  claims_this_month: number;
  avg_processing_seconds: number;
  acceptance_rate: number;
  missing_field_rate: number;
  pending_review_count: number;
}

export interface FieldConfig {
  id: string;
  name: string;
  api_key: string;
  field_type: string;
  required: boolean;
  is_active: boolean;
  order: number;
  extraction_hint: string | null;
  validation_rules: Record<string, unknown> | null;
  created_at: string;
}

export interface TokenPair {
  access_token: string;
  refresh_token: string;
  token_type: string;
}
