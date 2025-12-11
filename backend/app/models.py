from typing import List, Optional, Literal, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class Address(BaseModel):
    line1: str
    city: str
    state: str
    zip: str


class Patient(BaseModel):
    id: int
    first_name: str
    last_name: str
    dob: date
    email: str
    phone: str
    gender: str
    primary_language: str
    address: Address
    insurance_id: int
    chronic_conditions: List[str] = []
    medications: List[str] = []
    allergies: List[str] = []
    last_visit_date: Optional[date] = None
    preferred_contact_method: Literal["sms", "phone", "email"] = "sms"
    no_show_count: int = 0
    risk_flags: List[str] = []


class Insurance(BaseModel):
    id: int
    payer: str
    plan: str
    plan_type: str
    member_id: str
    group_number: Optional[str] = None
    eligible: bool
    eligibility_status: str
    coPay: Optional[float] = None
    coverage_start: Optional[date] = None
    coverage_end: Optional[date] = None
    deductible_remaining: Optional[float] = None
    out_of_pocket_max_remaining: Optional[float] = None
    requires_referral: bool = False
    eligibility_last_checked: Optional[datetime] = None


class ClinicalRisk(BaseModel):
    risk_score: int
    risk_level: Literal["low", "medium", "high"]
    factors: List[str]
    recommended_urgency: Literal[
        "routine", "within_7_days", "within_48_hours", "within_24_hours"
    ]
    generated_at: datetime


# 🔹 structured intake we want to persist on the appointment
class IntakeStructured(BaseModel):
    reason_for_visit: str
    triage_tags: List[str]
    suggested_urgency: Literal[
        "routine", "within_7_days", "within_48_hours", "within_24_hours"
    ]
    summary: str


class Appointment(BaseModel):
    id: int
    status: str
    start: datetime
    slot_duration: int
    patient_id: Optional[int] = None

    # Existing / extra fields — all OPTIONAL
    provider_id: Optional[int] = None
    location: Optional[str] = None
    visit_type: Optional[str] = None
    created_at: Optional[datetime] = None
    source: Optional[str] = None

    # 🔹 booking / clinical context we want to replay later
    reason_for_visit: Optional[str] = None
    clinical_risk: Optional[ClinicalRisk] = None

    # 🔹 NEW: persist intake + prep + (optionally) final SOAP note
    intake_narrative: Optional[str] = None
    intake_structured: Optional[IntakeStructured] = None
    prep_summary: Optional[Dict[str, Any]] = None  # what you send to PrepSummaryPanel
    final_note: Optional[Dict[str, Any]] = None    # optional: clinician-edited SOAP

    # Ignore any extra keys in JSON instead of erroring
    model_config = ConfigDict(extra="ignore")


class RiskPreviewRequest(BaseModel):
    patient_id: int
    reason_for_visit: str


class RiskPreviewResponse(BaseModel):
    risk: ClinicalRisk


class IntakeRequest(BaseModel):
    patient_id: int
    narrative: str


# 🔹 API response just reuses the same shape as IntakeStructured
class IntakeResponse(IntakeStructured):
    pass


class AvailableSlotsRequest(BaseModel):
    patient_id: int
    reason_for_visit: str
    provider_id: Optional[int] = None


class RecommendedSlot(BaseModel):
    appointment: Appointment
    score_adjustment: int


class AvailableSlotsResponse(BaseModel):
    risk: ClinicalRisk
    recommended_slots: List[RecommendedSlot]
    other_slots: List[Appointment]


class BookAppointmentRequest(BaseModel):
    patient_id: int
    appointment_id: int
    reason_for_visit: str


class BookingSummary(BaseModel):
    appointment: Appointment
    risk: ClinicalRisk
    prep_summary: Dict[str, Any]


class ClinicianScheduleItem(BaseModel):
    appointment_id: int
    start: datetime
    patient_name: str
    patient_age: int
    clinical_risk: Optional[ClinicalRisk] = None
    prep_summary_status: Literal["ready", "not_generated"] = "ready"


class PatientAppointmentsResponse(BaseModel):
    appointments: List[Appointment]
