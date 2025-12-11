Beam Health MVP – System Architecture

This architecture describes an AI-augmented scheduling and documentation system for outpatient clinics. The goal is to demonstrate how AI can accelerate intake, risk assessment, scheduling, and clinical preparation.

----------------------------------------------------
OVERVIEW
----------------------------------------------------

The system has three main layers:

1. Frontend (React)
2. Backend (FastAPI)
3. AI Engine (OpenAI)

JSON files act as a local lightweight database.

----------------------------------------------------
BACKEND ARCHITECTURE
----------------------------------------------------

Responsibilities:
- Data loading and persistence (patients, insurances, appointments)
- LLM-assisted clinical risk scoring
- LLM-assisted patient intake structuring
- LLM-assisted pre-visit preparation
- Appointment booking with permanent storage
- Replay of stored visit summaries without AI calls

Directory Structure:
backend/
  app/
    main.py               (entrypoint + routes)
    models.py             (Pydantic schemas)
    services/
      data_access.py      (JSON file CRUD)
      risk_engine.py      (baseline + LLM risk)
      prep_engine.py      (prep summary via LLM)

API Endpoints:
POST /intake/structure                → AI intake automation
POST /risk/preview                    → risk-only calculation
POST /appointments/available          → recommended & other slots
POST /appointments/book               → booking + LLM generation
GET  /appointments/{id}/details       → replay past booking
GET  /patients/{id}/appointments      → list user’s booked appointments

JSON Storage:
patients.json       → demographics + risk flags
insurances.json     → payer + eligibility
appointments.json   → each appointment stores:
  - reason_for_visit
  - intake_structured
  - clinical_risk
  - prep_summary
  - final_note (optional)
  - no extra LLM needed later

----------------------------------------------------
AI ARCHITECTURE
----------------------------------------------------

1. Risk Engine
   Baseline rules:
     - age
     - chronic conditions
     - risk flags
     - missed visits
     - insurance eligibility
     - keyword-based urgency
   Optional LLM refinement.
   Output: risk_score, risk_level, recommended_urgency.

2. Intake Automation
   Converts narrative → structured:
     - reason_for_visit
     - triage_tags
     - suggested_urgency
     - summary

3. Pre-Visit Preparation Engine
   LLM generates:
     - Patient snapshot
     - Visit details
     - Insurance summary
     - Risk explanation
     - Clinic to-dos
     - SOAP template

All outputs stored directly on the appointment object at booking time.

----------------------------------------------------
FRONTEND ARCHITECTURE
----------------------------------------------------

Components:
- PatientSearch
- RiskAwareScheduler
- BookingSummary
- PrepSummaryPanel
- BookedAppointments
- RiskBadge
- Axios API client (mock or real mode)

State Flow:
1. Select patient
2. Optional intake automation
3. Risk scoring
4. Recommended slots
5. Book appointment
6. View summary + prep panel
7. Click booked appointment → replay (no AI)

UI Enhancements:
- Separate loading states for intake, slot generation, booking
- Error banners
- Clean panel layout for clinician-friendly viewing
- Editable SOAP note section

----------------------------------------------------
APPOINTMENT REPLAY ARCHITECTURE
----------------------------------------------------

Goal: Zero additional LLM API calls for past appointments.

When booking:
- risk_engine produces clinical_risk
- intake_engine produces intake_structured
- prep_engine produces prep_summary
- all stored in appointments.json

When viewing:
- Backend simply returns stored structures
- Frontend renders BookingSummary + PrepSummaryPanel instantly

Benefits:
- Deterministic replay
- No API cost
- Works offline
- Fast UI

----------------------------------------------------
RUNNING MODES
----------------------------------------------------

1. With Backend
   - Full AI capability
   - JSON persistence
   - Booking replay

2. Without Backend (Mock Mode)
   - UI-only mode
   - Simulated slots, risk, intake
   - Useful for demos and development

----------------------------------------------------
LIMITATIONS (Intentional for MVP)
----------------------------------------------------

- No role-based authentication
- Single provider schedule
- JSON instead of a real DB
- No EMR integration
- No scheduling optimization algorithms (yet)

----------------------------------------------------
FUTURE ENHANCEMENTS
----------------------------------------------------

- Multi-provider calendar
- Billing and eligibility APIs
- Secure clinical documentation export
- Provider productivity dashboard
- Reminder and engagement automation
- Full audit history

