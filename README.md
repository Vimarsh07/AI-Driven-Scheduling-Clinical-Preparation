Beam Health – AI-Driven Scheduling & Clinical Preparation MVP

This project is a lightweight demonstration of how AI can streamline:
- Patient intake automation
- Risk-aware scheduling
- Clinician pre-visit preparation
- Appointment booking flows
- Replayable visit summaries without repeated LLM calls

It is built as a full-stack TypeScript + Python MVP with local JSON storage.

----------------------------------------------------
TECH STACK
----------------------------------------------------

Frontend
- React + Vite
- TypeScript
- Axios API client
- Local state management
- Custom components (RiskBadge, PrepSummaryPanel, PatientSearch, Scheduler)

Backend
- FastAPI
- Pydantic v2
- OpenAI API (optional)
- Local JSON storage for patients, insurances, appointments

AI
- GPT-4o-mini (configurable)
Used for:
  - Intake automation
  - Risk scoring refinement
  - Pre-visit preparation summary (SOAP template)

All AI outputs are stored in appointments.json to allow replay without re-calling LLMs.

----------------------------------------------------
PROJECT STRUCTURE
----------------------------------------------------

backend/
  app/
    main.py               (API router)
    models.py             (schemas)
    services/
      data_access.py
      risk_engine.py
      prep_engine.py
  patients.json
  insurances.json
  appointments.json
  .env

frontend/
  src/
    components/
      RiskAwareScheduler.tsx
      PrepSummaryPanel.tsx
      PatientSearch.tsx
      BookingSummary.tsx
      BookedAppointments.tsx
    api/client.ts
    types.ts
    App.tsx

----------------------------------------------------
RUNNING THE PROJECT
----------------------------------------------------

A) Running with Backend (Full Functionality)

1. Backend Setup
   cd backend
   python -m venv .venv
   .venv\Scripts\activate     (Windows)
   pip install -r requirements.txt

   Ensure .env contains:
     OPENAI_API_KEY=your-key
     OPENAI_ENABLED=true
     OPENAI_MODEL=gpt-4o-mini

   Run backend:
     uvicorn app.main:app --reload

   Backend URL: http://127.0.0.1:8000

2. Frontend Setup
   cd frontend
   npm install
   npm run dev

   Open: http://localhost:5173





----------------------------------------------------
CORE FEATURES
----------------------------------------------------

1. Intake Automation (AI)
   Free-text narrative → structured reason_for_visit, triage_tags, summary.

2. Risk-Aware Scheduling
   Baseline rules + optional LLM refinement:
   - risk_score (0–100)
   - risk_level (low, medium, high)
   - recommended urgency
   UI shows recommended slots and other available slots.

3. Appointment Booking
   On booking, the system stores:
   - reason_for_visit
   - intake_structured
   - clinical_risk
   - prep_summary
   These allow replay later with no additional LLM calls.

4. Replay Past Appointments
   Clicking a booked appointment loads:
   - appointment info
   - stored risk
   - stored prep summary
   - SOAP template
   - intake structured data
   No LLM calls required.

5. Clinician Pre-Visit Preparation
   Prep summary contains:
   - Patient snapshot
   - Visit details
   - Insurance summary
   - Risk explanation
   - To-do list
   - SOAP template
   - Editable clinician note with copy-to-clipboard

----------------------------------------------------
ERROR LOGGING
----------------------------------------------------

Backend:
- FastAPI validation and exception logs
- Fallbacks when OpenAI is disabled

Frontend:
- API try/catch blocks
- ErrorBanner for user-friendly messages
- Independent loading states for each button

----------------------------------------------------
ROADMAP
----------------------------------------------------

- Eligibility real-time API
- Billing automation
- Multi-provider schedule
- Authentication + RBAC
- Documentation export
- Reminder workflows

