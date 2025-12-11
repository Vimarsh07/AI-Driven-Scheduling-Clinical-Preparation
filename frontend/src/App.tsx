import React, { useState } from "react";
import PatientSearch, { Patient } from "./components/PatientSearch";
import RiskAwareScheduler from "./components/RiskAwareScheduler";
import BookingSummary from "./components/BookingSummary";
import PrepSummaryPanel from "./components/PrepSummaryPanel";

const App: React.FC = () => {
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [bookingSummary, setBookingSummary] = useState<any | null>(null);

  return (
    <div className="app">
      <header className="header">
        <h1>Beam AI Risk & Pre-Visit Prep MVP</h1>
        <p>
          Single unified view that simulates front-desk scheduling and clinician
          preparation – without authentication.
        </p>
      </header>

      <main className="grid">
        <section>
          <PatientSearch
            selectedPatientId={selectedPatient?.id ?? null}
            onSelect={(p) => {
              setSelectedPatient(p);
              setBookingSummary(null); // clear previous visit summary on patient change
            }}
          />

          {selectedPatient && (
            <div className="selected-patient-banner">
              <div>
                <div className="selected-patient-name">
                  {selectedPatient.first_name} {selectedPatient.last_name}
                </div>
                {/* You can enrich this if you add more fields to PatientSearch type */}
                <div className="selected-patient-subtext">
                  ID: {selectedPatient.id} · {selectedPatient.email}
                </div>
              </div>
              <span className="selected-patient-pill">Patient selected</span>
            </div>
          )}

          <RiskAwareScheduler
            patient={selectedPatient}
            onBooked={setBookingSummary}
          />
        </section>

        <section>
          <BookingSummary summary={bookingSummary} />
          <PrepSummaryPanel summary={bookingSummary} />
        </section>
      </main>
    </div>
  );
};

export default App;
