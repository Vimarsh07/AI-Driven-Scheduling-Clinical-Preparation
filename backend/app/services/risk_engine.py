import os
import json
from datetime import datetime, date
from typing import Optional, List, Dict

from dotenv import load_dotenv
from openai import OpenAI

from ..models import Patient, Insurance, Appointment, ClinicalRisk

load_dotenv()

# Env config
_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_OPENAI_ENABLED = os.getenv("OPENAI_ENABLED", "true").lower() == "true"

_client: Optional[OpenAI] = None


def _get_client() -> Optional[OpenAI]:
    """
    Lazy-init OpenAI client.
    Does NOT crash the app if the key is missing or OpenAI is disabled.
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
    """Compute age from a date or ISO string."""
    if isinstance(dob, str):
        dob_date = date.fromisoformat(dob)
    else:
        dob_date = dob

    today = date.today()
    return (
        today.year
        - dob_date.year
        - ((today.month, today.day) < (dob_date.month, dob_date.day))
    )


def _build_llm_payload(
    patient: Patient,
    insurance: Insurance,
    proposed_reason: str,
    existing_appointments: List[Appointment],
) -> Dict:
    """
    Build a compact JSON payload with derived fields (like age) that
    the LLM can use to apply heuristic rules.
    """
    # Derive age safely
    try:
        age = _age(patient.dob)
    except Exception:
        age = None

    patient_dict = patient.model_dump()
    insurance_dict = insurance.model_dump()
    appointments_dicts = [a.model_dump() for a in existing_appointments]

    return {
        "patient": {
            **patient_dict,
            "age": age,
            # keep these explicit for the LLM
            "chronic_conditions": getattr(patient, "chronic_conditions", []),
            "risk_flags": getattr(patient, "risk_flags", []),
            "no_show_count": getattr(patient, "no_show_count", 0),
        },
        "insurance": insurance_dict,
        "proposed_reason": proposed_reason,
        "existing_appointments": appointments_dicts,
    }


def _call_llm_for_risk(
    patient: Patient,
    insurance: Insurance,
    proposed_reason: str,
    existing_appointments: List[Appointment],
) -> Dict:
    """
    Pure LLM-based risk scoring.

    The LLM is instructed with the same *logic* that used to live in our
    rule-based function (age bands, chronic conditions, risk flags, no-shows,
    insurance eligibility, visit reason keywords, etc.), but now learns/applies
    that inside the prompt and outputs a structured JSON schema.
    """
    client = _get_client()
    payload = _build_llm_payload(
        patient=patient,
        insurance=insurance,
        proposed_reason=proposed_reason,
        existing_appointments=existing_appointments,
    )

    # If LLM is disabled or key missing -> deterministic default
    if client is None:
        return {
            "risk_score": 50,  # midline
            "risk_level": "medium",
            "factors": ["llm_unavailable_default_medium_risk"],
            "recommended_urgency": "within_7_days",
            "reason": "LLM not configured; using default medium risk.",
        }

    system_prompt = (
        "You are a clinical triage assistant helping a small outpatient clinic prioritize patients.\n\n"
        "You receive structured JSON with:\n"
        "- patient: demographics, chronic_conditions, risk_flags, no_show_count\n"
        "- insurance: eligibility info, plan, requires_referral, etc.\n"
        "- proposed_reason: free-text reason for the upcoming visit\n"
        "- existing_appointments: recent appointment history (including statuses like 'no_show' or 'cancelled').\n\n"
        "Use these heuristic principles (you can weigh them, not just add them):\n"
        "- Older age increases risk: especially >=75, then 65–74, then 50–64.\n"
        "- High-risk chronic conditions (e.g., heart failure, CAD, COPD, diabetes, asthma) increase risk.\n"
        "- Risk flags like high_cardiac_risk, behavioral_health, frequent_no_show increase risk.\n"
        "- More no_show_count or many recent missed/cancelled appointments increase 'operational' risk.\n"
        "- Insurance issues (not eligible, unclear eligibility, requires_referral) increase risk somewhat.\n"
        "- Concerning reasons (chest pain, shortness of breath, suicidal ideation, overdose, psych crisis, "
        "recent ED/ER follow-up) should push risk to high.\n"
        "- Routine/annual/wellness visits with few risk factors should be low.\n\n"
        "OUTPUT SCHEMA (very important):\n"
        "Respond with a SINGLE JSON object:\n"
        "{\n"
        '  \"risk_score\": <int between 0 and 100>,\n'
        '  \"risk_level\": \"low\" | \"medium\" | \"high\",\n'
        '  \"factors\": [\"short_snake_case_reasons\"],\n'
        '  \"recommended_urgency\": \"routine\" | \"within_7_days\" | \"within_48_hours\" | \"within_24_hours\",\n'
        '  \"reason\": \"Short natural-language explanation\"\n'
        "}\n\n"
        "Consistency rules:\n"
        "- If risk_level is 'high', recommended_urgency should usually be 'within_24_hours' or 'within_48_hours'.\n"
        "- If risk_level is 'medium', recommended_urgency is usually 'within_7_days'.\n"
        "- If risk_level is 'low', recommended_urgency is usually 'routine'.\n"
        "- Make risk_score broadly align with the level (e.g., high: 70–100, medium: 30–69, low: 0–29).\n"
    )

    user_prompt = (
        "Here is the visit context as JSON. Apply the heuristic rules above and "
        "return ONLY the JSON object in the exact schema specified.\n\n"
        f"{json.dumps(payload, default=str)}"
    )

    try:
        chat = client.chat.completions.create(
            model=_OPENAI_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=400,
        )
    except Exception:
        # Network / API errors -> deterministic fallback
        return {
            "risk_score": 50,
            "risk_level": "medium",
            "factors": ["llm_error_default_medium_risk"],
            "recommended_urgency": "within_7_days",
            "reason": "LLM call failed; using default medium risk.",
        }

    raw_text = chat.choices[0].message.content or ""

    try:
        parsed = json.loads(raw_text)
    except Exception:
        return {
            "risk_score": 50,
            "risk_level": "medium",
            "factors": ["llm_parse_error_default_medium_risk"],
            "recommended_urgency": "within_7_days",
            "reason": "LLM response could not be parsed; using default medium risk.",
        }

    # Extract fields with strong defaults
    risk_score = parsed.get("risk_score", 50)
    risk_level = str(parsed.get("risk_level", "medium")).lower()
    factors = parsed.get("factors", []) or []
    recommended_urgency = str(
        parsed.get("recommended_urgency", "within_7_days")
    ).lower()
    reason = str(parsed.get("reason", "") or "").strip()

    # Normalize / sanitize
    # risk_score -> int 0–100
    try:
        risk_score_int = int(round(float(risk_score)))
    except Exception:
        risk_score_int = 50
    risk_score_int = max(0, min(100, risk_score_int))

    if risk_level not in {"low", "medium", "high"}:
        if risk_score_int >= 70:
            risk_level = "high"
        elif risk_score_int >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"

    allowed_urgencies = {
        "routine",
        "within_7_days",
        "within_48_hours",
        "within_24_hours",
    }
    if recommended_urgency not in allowed_urgencies:
        # derive from level if invalid
        if risk_level == "high":
            recommended_urgency = "within_24_hours"
        elif risk_level == "medium":
            recommended_urgency = "within_7_days"
        else:
            recommended_urgency = "routine"

    if not isinstance(factors, list):
        factors = [str(factors)]
    factors = [str(f) for f in factors]

    if not reason:
        reason = "LLM did not provide a reason."

    return {
        "risk_score": risk_score_int,
        "risk_level": risk_level,
        "factors": factors,
        "recommended_urgency": recommended_urgency,
        "reason": reason,
    }


def score_risk_with_llm(
    patient: Patient,
    insurance: Insurance,
    proposed_reason: str,
    existing_appointments: List[Appointment],
) -> ClinicalRisk:
    """
    Used by /risk/preview and /appointments/available.
    Pure LLM-based risk scoring -> ClinicalRisk model.
    """
    result = _call_llm_for_risk(
        patient=patient,
        insurance=insurance,
        proposed_reason=proposed_reason,
        existing_appointments=existing_appointments,
    )

    return ClinicalRisk(
        risk_score=result["risk_score"],
        risk_level=result["risk_level"],
        factors=result["factors"],
        recommended_urgency=result["recommended_urgency"],
        generated_at=datetime.utcnow(),
    )


def calculate_risk(
    patient: Patient,
    insurance: Insurance,
    proposed_reason: str,
    existing_appointments: List[Appointment],
) -> ClinicalRisk:
    """
    Used by /appointments/book and prep flows.
    Currently just delegates to the LLM-based scorer.
    """
    return score_risk_with_llm(
        patient=patient,
        insurance=insurance,
        proposed_reason=proposed_reason,
        existing_appointments=existing_appointments,
    )
