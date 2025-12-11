from datetime import date
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from .models import (
    Patient,
    Appointment,
    Insurance,
    RiskPreviewRequest,
    RiskPreviewResponse,
    AvailableSlotsRequest,
    AvailableSlotsResponse,
    RecommendedSlot,
    BookAppointmentRequest,
    BookingSummary,
    ClinicianScheduleItem,
    IntakeRequest, IntakeResponse,
    PatientAppointmentsResponse,
)
from .services import data_access, risk_engine, prep_engine,intake_engine



app = FastAPI(title="Beam AI Risk & Prep MVP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/patients", response_model=List[Patient])
def list_patients(query: str | None = Query(default=None)):
    patients = data_access.load_patients()
    if query:
        q = query.lower()
        patients = [
            p
            for p in patients
            if q in p.first_name.lower()
            or q in p.last_name.lower()
            or q in p.email.lower()
            or q in p.phone.lower()
        ]
    return patients


@app.post("/risk/preview", response_model=RiskPreviewResponse)
def preview_risk(req: RiskPreviewRequest):
    patients = data_access.load_patients()
    insurances = data_access.load_insurances()
    appointments = data_access.load_appointments()

    patient = data_access.find_patient(patients, req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    insurance = data_access.find_insurance(insurances, patient.insurance_id)
    if not insurance:
        raise HTTPException(status_code=404, detail="Insurance not found")

    risk = risk_engine.calculate_risk(
        patient=patient,
        insurance=insurance,
        proposed_reason=req.reason_for_visit,
        existing_appointments=appointments,
    )

    return RiskPreviewResponse(risk=risk)


@app.get("/appointments/{appointment_id}/details", response_model=BookingSummary)
def get_appointment_details(appointment_id: int):
    patients = data_access.load_patients()
    insurances = data_access.load_insurances()
    appointments = data_access.load_appointments()

    appt = data_access.find_appointment(appointments, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if not appt.patient_id or appt.status != "booked":
        raise HTTPException(status_code=400, detail="Appointment is not booked")

    patient = data_access.find_patient(patients, appt.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    insurance = data_access.find_insurance(insurances, patient.insurance_id)
    if not insurance:
        raise HTTPException(status_code=404, detail="Insurance not found")

    # 🔑 no new LLM calls:
    risk = appt.clinical_risk
    prep_summary = appt.prep_summary

    return BookingSummary(
        appointment=appt,
        patient=patient,
        insurance=insurance,
        risk=risk,
        prep_summary=prep_summary,
    )


@app.get("/patients/{patient_id}/appointments", response_model=PatientAppointmentsResponse)
def get_patient_appointments(patient_id: int):
    patients = data_access.load_patients()
    appointments = data_access.load_appointments()

    patient = data_access.find_patient(patients, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # Only show booked appointments for this patient
    booked = [
        a for a in appointments
        if a.patient_id == patient.id and a.status == "booked"
    ]

    # Optionally sort by start time
    booked = sorted(booked, key=lambda a: a.start)

    return PatientAppointmentsResponse(appointments=booked)


@app.post("/intake/structure", response_model=IntakeResponse)
def intake_structure(req: IntakeRequest):
    patients = data_access.load_patients()
    patient = data_access.find_patient(patients, req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    result = intake_engine.run_intake(patient=patient, free_text=req.narrative)
    return IntakeResponse(**result)


@app.post("/appointments/available", response_model=AvailableSlotsResponse)
def available_slots(req: AvailableSlotsRequest):
    patients = data_access.load_patients()
    insurances = data_access.load_insurances()
    appointments = data_access.load_appointments()

    patient = data_access.find_patient(patients, req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    insurance = data_access.find_insurance(insurances, patient.insurance_id)
    if not insurance:
        raise HTTPException(status_code=404, detail="Insurance not found")

    # 🔹 1) Get LLM risk
    risk = risk_engine.calculate_risk(
        patient=patient,
        insurance=insurance,
        proposed_reason=req.reason_for_visit,
        existing_appointments=appointments,
    )

    # 🔹 2) Base set of available slots (by provider + status)
    now = datetime.utcnow()
    available = [
        a
        for a in appointments
        if a.status == "available"
        and a.start >= now
        and (req.provider_id is None or a.provider_id == req.provider_id)
    ]

    # 🔹 3) Map risk → urgency window
    urgency = risk.recommended_urgency  # "routine" | "within_7_days" | "within_48_hours" | "within_24_hours"

    if urgency == "within_24_hours":
        max_days = 1
    elif urgency == "within_48_hours":
        max_days = 2
    elif urgency == "within_7_days":
        max_days = 7
    else:  # "routine"
        max_days = 30  # or whatever upper bound you want

    max_start = now + timedelta(days=max_days)

    # 🔹 4) Split into recommended vs other
    recommended_appts = [a for a in available if a.start <= max_start]
    other_appts = [a for a in available if a.start > max_start]

    # Sort chronologically
    recommended_appts.sort(key=lambda a: a.start)
    other_appts.sort(key=lambda a: a.start)

    # 🔹 5) Wrap recommended_appts in RecommendedSlot
    recommended_slots: List[RecommendedSlot] = [
        RecommendedSlot(
            appointment=a,
            score_adjustment=0,  # later you can tweak by risk_level / factors
        )
        for a in recommended_appts
    ]

    return AvailableSlotsResponse(
        risk=risk,
        recommended_slots=recommended_slots,
        other_slots=other_appts,
    )


@app.post("/appointments/book", response_model=BookingSummary)
def book_appointment(req: BookAppointmentRequest):
    patients = data_access.load_patients()
    insurances = data_access.load_insurances()
    appointments = data_access.load_appointments()

    patient = data_access.find_patient(patients, req.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    appointment = data_access.find_appointment(appointments, req.appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status != "available":
        raise HTTPException(status_code=400, detail="Appointment not available")

    insurance = data_access.find_insurance(insurances, patient.insurance_id)
    if not insurance:
        raise HTTPException(status_code=404, detail="Insurance not found")

    # Compute risk and attach to appointment
    risk = risk_engine.calculate_risk(
        patient=patient,
        insurance=insurance,
        proposed_reason=req.reason_for_visit,
        existing_appointments=appointments,
    )

    appointment.patient_id = patient.id
    appointment.status = "booked"
    appointment.reason_for_visit = req.reason_for_visit
    appointment.clinical_risk = risk

    # Persist appointments for demo purposes
    

    prep_summary = prep_engine.build_prep_summary(
        appointment=appointment,
        patient=patient,
        insurance=insurance,
        clinical_risk=risk,
    )
    appointment.prep_summary = prep_summary
    data_access.save_appointments(appointments)

    return BookingSummary(appointment=appointment, risk=risk, prep_summary=prep_summary)


@app.get("/clinician/schedule", response_model=List[ClinicianScheduleItem])
def clinician_schedule(
    provider_id: int,
    date_str: str | None = None,
):
    appointments = data_access.load_appointments()
    patients = data_access.load_patients()

    if date_str:
        target_date = date.fromisoformat(date_str)
        appointments = [
            a
            for a in appointments
            if a.start.date() == target_date and a.provider_id == provider_id and a.status == "booked"
        ]
    else:
        appointments = [a for a in appointments if a.provider_id == provider_id and a.status == "booked"]

    items: List[ClinicianScheduleItem] = []

    for a in sorted(appointments, key=lambda x: x.start):
        patient = data_access.find_patient(patients, a.patient_id) if a.patient_id else None
        if not patient:
            continue
        age_years = prep_engine._age(patient.dob)
        items.append(
            ClinicianScheduleItem(
                appointment_id=a.id,
                start=a.start,
                patient_name=f"{patient.first_name} {patient.last_name}",
                patient_age=age_years,
                clinical_risk=a.clinical_risk,
                prep_summary_status="ready",
            )
        )

    return items


@app.get("/prep-summary/{appointment_id}")
def get_prep_summary(appointment_id: int):
    appointments = data_access.load_appointments()
    patients = data_access.load_patients()
    insurances = data_access.load_insurances()

    appointment = data_access.find_appointment(appointments, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if not appointment.patient_id:
        raise HTTPException(status_code=400, detail="Appointment has no patient")

    patient = data_access.find_patient(patients, appointment.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    insurance = data_access.find_insurance(insurances, patient.insurance_id)
    if not insurance:
        raise HTTPException(status_code=404, detail="Insurance not found")

    # If you already computed risk during booking, use that; otherwise recompute:
    risk = (
        appointment.clinical_risk
        if getattr(appointment, "clinical_risk", None)
        else risk_engine.calculate_risk(
            patient=patient,
            insurance=insurance,
            proposed_reason=getattr(appointment, "reason_for_visit", "") or "",
            existing_appointments=appointments,
        )
    )

    summary = prep_engine.build_prep_summary(
        appointment=appointment,
        patient=patient,
        insurance=insurance,
        clinical_risk=risk,
    )

    return summary
