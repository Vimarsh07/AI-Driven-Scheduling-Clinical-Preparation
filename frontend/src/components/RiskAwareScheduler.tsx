import React, { useState, useMemo, useEffect } from "react";
import api from "../api/client";
import { RiskBadge } from "./RiskBadge";
import type { Patient } from "./PatientSearch";
import ErrorBanner from "./ErrorBanner";
import type {
  Appointment,
  ClinicalRisk,
  BookingSummaryResponse,
  RecommendedSlot,
  IntakeResult,
} from "../types";

type Props = {
  patient: Patient | null;
  onBooked: (summary: BookingSummaryResponse) => void;
};

type OtherSlotsFilterRange = "week" | "month";

const RiskAwareScheduler: React.FC<Props> = ({ patient, onBooked }) => {
  const [intakeNarrative, setIntakeNarrative] = useState("");
  const [intakeResult, setIntakeResult] = useState<IntakeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [reason, setReason] = useState("");
  const [risk, setRisk] = useState<ClinicalRisk | null>(null);
  const [recommendedSlots, setRecommendedSlots] = useState<RecommendedSlot[]>(
    []
  );
  const [otherSlots, setOtherSlots] = useState<Appointment[]>([]);

  const [loadingIntake, setLoadingIntake] = useState(false);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [bookingSlotId, setBookingSlotId] = useState<number | null>(null);

  const [otherFilterRange, setOtherFilterRange] =
    useState<OtherSlotsFilterRange>("week");

  // Booked appointments UI
  const [showBooked, setShowBooked] = useState(false);
  const [bookedAppointments, setBookedAppointments] = useState<Appointment[]>(
    []
  );
  const [loadingBooked, setLoadingBooked] = useState(false);
  const [selectedBookedId, setSelectedBookedId] = useState<number | null>(null);

  // 🔁 Reset everything when the selected patient changes
  useEffect(() => {
    setIntakeNarrative("");
    setIntakeResult(null);
    setError(null);
    setReason("");
    setRisk(null);
    setRecommendedSlots([]);
    setOtherSlots([]);
    setLoadingIntake(false);
    setLoadingSlots(false);
    setBookingSlotId(null);
    setOtherFilterRange("week");
    setShowBooked(false);
    setBookedAppointments([]);
    setLoadingBooked(false);
    setSelectedBookedId(null);
  }, [patient?.id]);

  const handleRunIntake = async () => {
    if (!patient || !intakeNarrative.trim()) return;
    setError(null);
    setLoadingIntake(true);
    try {
      const res = await api.post("/intake/structure", {
        patient_id: patient.id,
        narrative: intakeNarrative,
      });
      const data: IntakeResult = res.data;
      setIntakeResult(data);
      setReason(data.reason_for_visit);
    } catch (err: any) {
      setError(err.message || "Failed to run intake automation.");
    } finally {
      setLoadingIntake(false);
    }
  };

  const handleGetSlots = async () => {
    if (!patient || !reason.trim()) return;
    setError(null);
    setLoadingSlots(true);
    try {
      const res = await api.post("/appointments/available", {
        patient_id: patient.id,
        reason_for_visit: reason,
      });
      setRisk(res.data.risk);
      setRecommendedSlots(res.data.recommended_slots || []);
      setOtherSlots(res.data.other_slots || []);
    } catch (err: any) {
      setError(err.message || "Failed to fetch available slots.");
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleBook = async (slotId: number) => {
    if (!patient || !reason.trim()) return;
    setError(null);
    setBookingSlotId(slotId);
    try {
      const res = await api.post("/appointments/book", {
        patient_id: patient.id,
        appointment_id: slotId,
        reason_for_visit: reason,
      });
      onBooked(res.data);

      // Refresh booked list if panel is open
      if (showBooked) {
        await fetchBookedAppointments();
      }
    } catch (err: any) {
      setError(err.message || "Failed to book appointment.");
    } finally {
      setBookingSlotId(null);
    }
  };

  const fetchBookedAppointments = async () => {
    if (!patient) return;
    setLoadingBooked(true);
    try {
      const res = await api.get(`/patients/${patient.id}/appointments`);
      setBookedAppointments(res.data.appointments || []);
    } catch (err: any) {
      setError(err.message || "Failed to load booked appointments.");
    } finally {
      setLoadingBooked(false);
    }
  };

  const handleToggleBooked = async () => {
    if (!patient) return;
    if (!showBooked) {
      await fetchBookedAppointments();
    }
    setShowBooked((prev) => !prev);
  };

  const handleSelectBooked = async (appointmentId: number) => {
    setSelectedBookedId(appointmentId);
    try {
      const res = await api.get<BookingSummaryResponse>(
        `/appointments/${appointmentId}/details`
      );
      onBooked(res.data);
    } catch (err) {
      console.error("Failed to load appointment details", err);
      setError("Failed to load appointment details.");
    }
  };

  const filteredOtherSlots = useMemo(() => {
    if (otherSlots.length === 0) return [];

    const now = new Date();
    const maxDate = new Date(now);

    if (otherFilterRange === "week") {
      maxDate.setDate(maxDate.getDate() + 7);
    } else {
      maxDate.setMonth(maxDate.getMonth() + 1);
    }

    return otherSlots.filter((slot) => {
      const start = new Date(slot.start);
      return start >= now && start <= maxDate;
    });
  }, [otherSlots, otherFilterRange]);

  return (
    <div className="card">
      <div className="card-header-row">
        <h2>2. Risk-aware Scheduling</h2>
        {patient && (
          <button
            type="button"
            className="btn-sm"
            onClick={handleToggleBooked}
            disabled={loadingBooked}
          >
            {loadingBooked
              ? "Loading booked..."
              : showBooked
              ? "Hide booked appointments"
              : "View booked appointments"}
          </button>
        )}
      </div>

      {error && <ErrorBanner message={error} />}

      {!patient && <p>Select a patient first.</p>}
      {patient && (
        <>
          {/* Intake automation block */}
          <div className="intake-block">
            <label className="field">
              Intake narrative (what the patient told you)
              <textarea
                rows={3}
                placeholder="e.g. Patient says they've had worsening shortness of breath for 3 days, history of COPD..."
                value={intakeNarrative}
                onChange={(e) => setIntakeNarrative(e.target.value)}
              />
            </label>
            <button
              onClick={handleRunIntake}
              disabled={loadingIntake || !intakeNarrative.trim()}
            >
              {loadingIntake ? "Processing..." : "Run intake automation"}
            </button>

            {intakeResult && (
              <div className="intake-summary">
                <div className="subtext">
                  <strong>Structured reason:</strong>{" "}
                  {intakeResult.reason_for_visit}
                </div>
                <div className="subtext">
                  <strong>Triage tags:</strong>{" "}
                  {intakeResult.triage_tags.join(", ") || "None"}
                </div>
                <div className="subtext">
                  <strong>Summary for clinician:</strong>{" "}
                  {intakeResult.summary}
                </div>
              </div>
            )}
          </div>

          <hr />

          {/* Reason for visit (editable) */}
          <label className="field">
            Reason for visit (editable)
            <input
              placeholder="e.g. Shortness of breath, follow-up for diabetes"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
            />
          </label>
          <button onClick={handleGetSlots} disabled={loadingSlots || !reason}>
            {loadingSlots ? "Calculating..." : "Get Recommended Slots"}
          </button>

          {risk && (
            <div className="risk-header">
              <RiskBadge level={risk.risk_level} score={risk.risk_score} />
              <span className="subtext">
                Recommended urgency:{" "}
                {risk.recommended_urgency.replace(/_/g, " ")}
              </span>
            </div>
          )}

          {/* Recommended slots section */}
          {recommendedSlots.length > 0 && (
            <div className="slots">
              <h3>Recommended slots</h3>
              <ul className="list">
                {recommendedSlots.map(({ appointment }) => (
                  <li key={appointment.id} className="slot-item">
                    <div>
                      <strong>
                        {new Date(appointment.start).toLocaleString()}
                      </strong>
                      <div className="subtext">
                        {appointment.location} · {appointment.visit_type}
                      </div>
                    </div>
                    <button
                      onClick={() => handleBook(appointment.id)}
                      disabled={bookingSlotId === appointment.id}
                    >
                      {bookingSlotId === appointment.id ? "Booking..." : "Book"}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {risk && recommendedSlots.length === 0 && otherSlots.length > 0 && (
            <p className="subtext">
              No slots available in the LLM-recommended time window. You can
              still choose from other available dates below.
            </p>
          )}

          {/* Other slots + filters */}
          {otherSlots.length > 0 && (
            <div className="slots">
              <div className="slots-header">
                <h3>Other available slots</h3>
                <div className="filters">
                  <span className="subtext">Filter by:</span>
                  <button
                    type="button"
                    className={
                      otherFilterRange === "week" ? "btn-sm primary" : "btn-sm"
                    }
                    onClick={() => setOtherFilterRange("week")}
                  >
                    Next 7 days
                  </button>
                  <button
                    type="button"
                    className={
                      otherFilterRange === "month" ? "btn-sm primary" : "btn-sm"
                    }
                    onClick={() => setOtherFilterRange("month")}
                  >
                    Next 30 days
                  </button>
                </div>
              </div>

              {filteredOtherSlots.length === 0 ? (
                <p className="subtext">
                  No other slots found in the selected range.
                </p>
              ) : (
                <ul className="list">
                  {filteredOtherSlots.map((appointment) => (
                    <li key={appointment.id} className="slot-item">
                      <div>
                        <strong>
                          {new Date(appointment.start).toLocaleString()}
                        </strong>
                        <div className="subtext">
                          {appointment.location} · {appointment.visit_type}
                        </div>
                      </div>
                      <button
                        onClick={() => handleBook(appointment.id)}
                        disabled={bookingSlotId === appointment.id}
                      >
                        {bookingSlotId === appointment.id
                          ? "Booking..."
                          : "Book"}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Booked appointments panel */}
          {showBooked && bookedAppointments.length > 0 && (
            <div className="slots">
              <h3>Booked appointments</h3>
              <ul className="list">
                {bookedAppointments.map((appt) => (
                  <li
                    key={appt.id}
                    className={`slot-item booked-row ${
                      selectedBookedId === appt.id ? "selected" : ""
                    }`}
                    onClick={() => handleSelectBooked(appt.id)}
                  >
                    <div>
                      <strong>{new Date(appt.start).toLocaleString()}</strong>
                      <div className="subtext">
                        {appt.location} · {appt.visit_type || "visit"}
                      </div>
                      {appt.clinical_risk && (
                        <div className="subtext">
                          Risk: {appt.clinical_risk.risk_level} (
                          {appt.clinical_risk.risk_score})
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default RiskAwareScheduler;
