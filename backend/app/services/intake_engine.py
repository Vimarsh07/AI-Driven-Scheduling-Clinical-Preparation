# app/services/intake_engine.py

import os
import json
from typing import Optional, List, Dict

from dotenv import load_dotenv
from openai import OpenAI

from ..models import Patient

load_dotenv()

_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
_OPENAI_ENABLED = os.getenv("OPENAI_ENABLED", "true").lower() == "true"

_client: Optional[OpenAI] = None


def _get_client() -> Optional[OpenAI]:
    global _client

    if not _OPENAI_ENABLED:
        return None

    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        _client = OpenAI(api_key=api_key)

    return _client


def run_intake(patient: Patient, free_text: str) -> Dict:
    """
    Takes a raw intake narrative (what the patient told front-desk / MA)
    and turns it into structured data:
      - reason_for_visit
      - triage_tags
      - suggested_urgency
      - summary
    """
    client = _get_client()

    # If no LLM configured, just echo back a minimal structure
    if client is None:
        return {
            "reason_for_visit": free_text[:200],
            "triage_tags": ["llm_unavailable"],
            "suggested_urgency": "routine",
            "summary": free_text,
        }

    payload = {
        "patient": patient.model_dump(),
        "intake_narrative": free_text,
    }

    system_prompt = (
        "You are a medical intake assistant. You receive a free-text narrative "
        "from a patient (or staff) and basic patient context. "
        "Your job is to structure this into fields that downstream triage & "
        "scheduling logic can use.\n\n"
        "Respond with a single JSON object with keys:\n"
        "- reason_for_visit: short phrase (used as scheduling reason)\n"
        "- triage_tags: array of short snake_case tags, e.g. "
        "['chest_pain', 'post_ed_followup', 'medication_refill']\n"
        "- suggested_urgency: one of 'routine', 'within_7_days', "
        "'within_48_hours', 'within_24_hours'\n"
        "- summary: 2-3 sentence summary for the clinician\n"
    )

    user_prompt = (
        "Here is the patient context and intake narrative as JSON. "
        "Apply the schema above and return ONLY the JSON object.\n\n"
        f"{json.dumps(payload, default=str)}"
    )

    chat = client.chat.completions.create(
        model=_OPENAI_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=400,
    )

    raw_text = chat.choices[0].message.content or ""

    try:
        parsed = json.loads(raw_text)
    except Exception:
        return {
            "reason_for_visit": free_text[:200],
            "triage_tags": ["parse_error"],
            "suggested_urgency": "within_7_days",
            "summary": free_text,
        }

    reason_for_visit = parsed.get("reason_for_visit", free_text[:200])
    triage_tags = parsed.get("triage_tags", []) or []
    suggested_urgency = parsed.get("suggested_urgency", "within_7_days")
    summary = parsed.get("summary", free_text)

    if not isinstance(triage_tags, List):
        triage_tags = [str(triage_tags)]

    return {
        "reason_for_visit": str(reason_for_visit),
        "triage_tags": [str(t) for t in triage_tags],
        "suggested_urgency": str(suggested_urgency),
        "summary": str(summary),
    }
