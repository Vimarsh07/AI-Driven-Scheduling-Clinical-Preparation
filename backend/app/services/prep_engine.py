import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

from ..models import Appointment, Patient, Insurance, ClinicalRisk

load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_OPENAI_ENABLED = os.getenv("OPENAI_ENABLED", "true").lower() == "true"

_client: Optional[OpenAI] = None


def _get_client() -> Optional[OpenAI]:
    """
    Lazy-init OpenAI client.
    """
    global _client

    if not _OPENAI_ENABLED:
        return None

    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        _client = OpenAI(api_key=api_key)

    return _client


def _age(dob) -> int:
    today = datetime.utcnow().date()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def build_prep_summary(
    appointment: Appointment,
    patient: Patient,
    insurance: Insurance,
    clinical_risk: ClinicalRisk,
) -> Dict[str, Any]:
    """
    Builds a pre-visit preparation summary.
    Rule-based skeleton + optional OpenAI call for richer note template & suggestions.
    """
    base_summary: Dict[str, Any] = {
        "patient_snapshot": {
            "name": f"{patient.first_name} {patient.last_name}",
            "age": _age(patient.dob),
            "gender": patient.gender,
            "conditions": patient.chronic_conditions,
            "medications": patient.medications,
            "allergies": patient.allergies or ["None documented"],
            "primary_language": patient.primary_language,
        },
        "visit_details": {
            "datetime": appointment.start.isoformat(),
            "location": getattr(appointment, "location", None),
            "visit_type": getattr(appointment, "visit_type", None),
            "reason_for_visit": getattr(appointment, "reason_for_visit", None),
            "is_follow_up": getattr(appointment, "is_follow_up", False),
            "expected_complexity": getattr(appointment, "expected_complexity", "routine"),
        },
        "insurance_summary": {
            "payer": insurance.payer,
            "plan": insurance.plan,
            "coPay": insurance.coPay,
            "eligibility_status": insurance.eligibility_status,
            "requires_referral": insurance.requires_referral,
            "deductible_remaining": insurance.deductible_remaining,
        },
        "risk_assessment": clinical_risk.model_dump(),
        "todo_for_clinic": [
            "Verify that medication list is up to date.",
            "Confirm allergies and update EMR if needed.",
            "Collect any external lab or imaging results relevant to this visit.",
        ],
        "note_template": {
            "subjective": [],
            "objective": [],
            "assessment": [],
            "plan": [],
        },
        "generated_at": datetime.utcnow().isoformat(),
    }

    client = _get_client()
    if client is None:
        # No OpenAI key / disabled; return a sane default note template
        base_summary["note_template"] = {
            "subjective": [
                "Chief complaint and duration",
                "Relevant history of present illness",
            ],
            "objective": [
                "Vital signs and focused exam",
            ],
            "assessment": [
                "Working diagnosis / differential",
            ],
            "plan": [
                "Diagnostics, treatment changes, follow-up",
            ],
        }
        return base_summary

    system_prompt = (
        "You are an experienced primary care clinician helping prepare for a visit. "
        "Given structured patient, appointment, and insurance context, generate:\n"
        "- A brief to-do list for the clinical team before the visit.\n"
        "- A concise SOAP-style note template tailored to the patient’s risk factors and reason for visit.\n"
        "You MUST respond with a single valid JSON object."
    )

    user_context = {
        "patient_snapshot": base_summary["patient_snapshot"],
        "visit_details": base_summary["visit_details"],
        "insurance_summary": base_summary["insurance_summary"],
        "risk_assessment": base_summary["risk_assessment"],
    }

    user_prompt = (
        "Here is the visit context as JSON:\n"
        f"{json.dumps(user_context, default=str)}\n\n"
        "Return a JSON object with keys 'todo_for_clinic' (list of strings) "
        "and 'note_template' (object with keys subjective, objective, assessment, plan)."
    )

    chat = client.chat.completions.create(
        model=OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,
    )

    raw_text = chat.choices[0].message.content
    if not raw_text:
        return base_summary

    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, dict):
            if "todo_for_clinic" in parsed:
                base_summary["todo_for_clinic"] = parsed["todo_for_clinic"]
            if "note_template" in parsed:
                base_summary["note_template"] = parsed["note_template"]
    except Exception:
        # If anything goes wrong, we just keep the base_summary defaults
        pass

    return base_summary
