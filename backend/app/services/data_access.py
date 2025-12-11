import json
from pathlib import Path
from typing import List, Dict, Optional

from . import risk_engine  # noqa: F401 (used indirectly)
from ..models import Patient, Appointment, Insurance

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"


def _load_json(filename: str) -> List[Dict]:
    path = DATA_DIR / filename
    with path.open() as f:
        return json.load(f)


def _save_json(filename: str, data: List[Dict]) -> None:
    path = DATA_DIR / filename
    with path.open("w") as f:
        json.dump(data, f, indent=2, default=str)


def load_patients() -> List[Patient]:
    raw = _load_json("patients.json")
    return [Patient.model_validate(p) for p in raw]


def load_insurances() -> List[Insurance]:
    raw = _load_json("insurances.json")
    return [Insurance.model_validate(i) for i in raw]


def load_appointments() -> List[Appointment]:
    raw = _load_json("appointments.json")
    return [Appointment.model_validate(a) for a in raw]


def save_appointments(appointments: List[Appointment]) -> None:
    _save_json("appointments.json", [a.model_dump() for a in appointments])


def find_patient(patients: List[Patient], patient_id: int) -> Optional[Patient]:
    return next((p for p in patients if p.id == patient_id), None)


def find_insurance(insurances: List[Insurance], insurance_id: int) -> Optional[Insurance]:
    return next((i for i in insurances if i.id == insurance_id), None)


def find_appointment(appointments: List[Appointment], appointment_id: int) -> Optional[Appointment]:
    return next((a for a in appointments if a.id == appointment_id), None)
