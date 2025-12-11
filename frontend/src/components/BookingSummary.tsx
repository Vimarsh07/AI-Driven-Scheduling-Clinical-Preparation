import React from "react";
import { RiskBadge } from "./RiskBadge";

type Props = {
  summary: any | null;
};

const BookingSummary: React.FC<Props> = ({ summary }) => {
  if (!summary) return null;
  const { appointment, risk } = summary;

  return (
    <div className="card">
      <h2>3. Booking & Risk Summary</h2>
      <p>
        Appointment booked for{" "}
        <strong>{new Date(appointment.start).toLocaleString()}</strong> at{" "}
        <strong>{appointment.location}</strong>.
      </p>
      {risk && (
        <>
          <RiskBadge level={risk.risk_level} score={risk.risk_score} />
          <p className="subtext">Key factors: {risk.factors.join(", ")}</p>
        </>
      )}
      <p className="subtext">
        Clinician will see full risk breakdown and pre-visit prep below.
      </p>
    </div>
  );
};

export default BookingSummary;
