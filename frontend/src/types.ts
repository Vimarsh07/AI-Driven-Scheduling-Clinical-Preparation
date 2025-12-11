// src/types.ts
export type ClinicalRisk = {
  risk_score: number;
  risk_level: "low" | "medium" | "high";
  factors: string[];
  recommended_urgency: "routine" | "within_7_days" | "within_48_hours" | "within_24_hours";
  generated_at: string;
};

export type Appointment = {
  id: number;
  status: string;
  start: string;
  slot_duration: number;
  patient_id?: number | null;
  provider_id?: number | null;
  location?: string | null;
  visit_type?: string | null;
  created_at?: string | null;
  source?: string | null;
  reason_for_visit?: string | null;
  clinical_risk?: ClinicalRisk | null;
  intake_narrative?: string | null;
  intake_structured?: any | null;
  prep_summary?: any | null;
  final_note?: any | null;
};

// This matches your backend BookingSummary / BookingSummaryResponse
export type BookingSummaryResponse = {
  appointment: Appointment;
  risk: ClinicalRisk;
  prep_summary: any;
};

export type RecommendedSlot = {
  appointment: Appointment;
  score_adjustment: number;
};

export type IntakeResult = {
  reason_for_visit: string;
  triage_tags: string[];
  suggested_urgency: string;
  summary: string;
};

