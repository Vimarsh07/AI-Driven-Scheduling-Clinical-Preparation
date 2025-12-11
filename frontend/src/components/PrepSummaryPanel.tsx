import React, { useEffect, useMemo, useState } from "react";

type Props = {
  summary: any | null;
};

type NoteTemplateState = {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
};

const normalizeSection = (value: unknown): string => {
  if (Array.isArray(value)) {
    return (value as any[]).join("\n");
  }
  if (typeof value === "string") {
    return value;
  }
  if (value == null) {
    return "";
  }
  return String(value);
};

const PrepSummaryPanel: React.FC<Props> = ({ summary }) => {
  const prep_summary = summary?.prep_summary;

  const ps = prep_summary?.patient_snapshot;
  const vd = prep_summary?.visit_details;
  const ins = prep_summary?.insurance_summary;
  const todo: string[] = prep_summary?.todo_for_clinic || [];

  const [note, setNote] = useState<NoteTemplateState>({
    subjective: "",
    objective: "",
    assessment: "",
    plan: "",
  });
  const [copied, setCopied] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Seed note when a NEW prep summary arrives
  useEffect(() => {
    if (!prep_summary) return;
    const tmpl = prep_summary.note_template || {};
    setNote({
      subjective: normalizeSection((tmpl as any).subjective),
      objective: normalizeSection((tmpl as any).objective),
      assessment: normalizeSection((tmpl as any).assessment),
      plan: normalizeSection((tmpl as any).plan),
    });
    setCopied(false);
    setEditMode(false);
  }, [prep_summary]);

  const handleChange = (section: keyof NoteTemplateState, value: string) => {
    setNote((prev) => ({ ...prev, [section]: value }));
    setCopied(false);
  };

  const combinedNote = useMemo(() => {
    const parts: string[] = [];
    if (note.subjective.trim()) parts.push(`S: ${note.subjective.trim()}`);
    if (note.objective.trim()) parts.push(`O: ${note.objective.trim()}`);
    if (note.assessment.trim()) parts.push(`A: ${note.assessment.trim()}`);
    if (note.plan.trim()) parts.push(`P: ${note.plan.trim()}`);
    return parts.join("\n\n");
  }, [note]);

  const handleCopy = async () => {
    try {
      if (!combinedNote) return;
      await navigator.clipboard.writeText(combinedNote);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  if (!prep_summary) return null;

  return (
    <div className="card prep-card">
      <div className="prep-header">
        <div>
          <h2>4. Clinician Pre-Visit Preparation</h2>
          {ps && (
            <p className="subtext">
              {ps.name} · {ps.age} · {ps.gender}{" "}
              {vd && (
                <>
                  • {vd.visit_type} •{" "}
                  {new Date(vd.datetime).toLocaleString()}
                </>
              )}
            </p>
          )}
        </div>

        <div className="prep-header-actions">
          <button
            type="button"
            className="btn-sm"
            onClick={() => setEditMode((e) => !e)}
          >
            {editMode ? "Done editing" : "Edit note"}
          </button>
          <button
            type="button"
            className="btn-sm primary"
            onClick={handleCopy}
            disabled={!combinedNote}
          >
            {copied ? "Copied!" : "Copy to clipboard"}
          </button>
        </div>
      </div>

      <div className="prep-layout">
        {/* LEFT COLUMN: context */}
        <div className="prep-col">
          {ps && (
            <div className="section compact">
              <h3>Patient snapshot</h3>
              <p className="subtext">
                <strong>Conditions:</strong>{" "}
                {(ps.conditions || []).join(", ") || "None listed"}
              </p>
              <p className="subtext">
                <strong>Medications:</strong>{" "}
                {(ps.medications || []).join(", ") || "None listed"}
              </p>
              <p className="subtext">
                <strong>Allergies:</strong>{" "}
                {(ps.allergies || []).join(", ") || "None documented"}
              </p>
            </div>
          )}

          {ins && (
            <div className="section compact">
              <h3>Insurance</h3>
              <p className="subtext">
                {ins.payer} – {ins.plan}
              </p>
              <p className="subtext">
                <strong>Co-pay:</strong>{" "}
                {ins.coPay !== null && ins.coPay !== undefined
                  ? `$${ins.coPay}`
                  : "N/A"}{" "}
                • <strong>Status:</strong> {ins.eligibility_status}
              </p>
            </div>
          )}

          {vd && (
            <div className="section compact">
              <h3>Visit details</h3>
              <p className="subtext">
                <strong>Reason:</strong>{" "}
                {vd.reason_for_visit || "Not specified"}
              </p>
              <p className="subtext">
                <strong>Location:</strong> {vd.location}
              </p>
            </div>
          )}

          {todo.length > 0 && (
            <div className="section compact">
              <h3>Team to-do before visit</h3>
              <ul className="list small">
                {todo.map((t, idx) => (
                  <li key={idx}>{t}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* RIGHT COLUMN: note */}
        <div className="prep-col note-col">
          <h3>Draft clinical note</h3>

          {/* READ MODE: tidy paragraphs */}
          {!editMode && (
            <div className="note-read">
              {note.subjective.trim() && (
                <div className="note-section">
                  <h4>S – Subjective</h4>
                  <p>{note.subjective}</p>
                </div>
              )}
              {note.objective.trim() && (
                <div className="note-section">
                  <h4>O – Objective</h4>
                  <p>{note.objective}</p>
                </div>
              )}
              {note.assessment.trim() && (
                <div className="note-section">
                  <h4>A – Assessment</h4>
                  <p>{note.assessment}</p>
                </div>
              )}
              {note.plan.trim() && (
                <div className="note-section">
                  <h4>P – Plan</h4>
                  <p>{note.plan}</p>
                </div>
              )}
              {!note.subjective.trim() &&
                !note.objective.trim() &&
                !note.assessment.trim() &&
                !note.plan.trim() && (
                  <p className="subtext">
                    No note content yet. Click &ldquo;Edit note&rdquo; to
                    refine the LLM draft.
                  </p>
                )}
            </div>
          )}

          {/* EDIT MODE: compact stacked textareas */}
          {editMode && (
            <div className="note-edit">
              <div className="note-edit-row">
                <label>
                  <span>S – Subjective</span>
                  <textarea
                    rows={3}
                    value={note.subjective}
                    onChange={(e) =>
                      handleChange("subjective", e.target.value)
                    }
                  />
                </label>
              </div>
              <div className="note-edit-row">
                <label>
                  <span>O – Objective</span>
                  <textarea
                    rows={3}
                    value={note.objective}
                    onChange={(e) =>
                      handleChange("objective", e.target.value)
                    }
                  />
                </label>
              </div>
              <div className="note-edit-row">
                <label>
                  <span>A – Assessment</span>
                  <textarea
                    rows={3}
                    value={note.assessment}
                    onChange={(e) =>
                      handleChange("assessment", e.target.value)
                    }
                  />
                </label>
              </div>
              <div className="note-edit-row">
                <label>
                  <span>P – Plan</span>
                  <textarea
                    rows={3}
                    value={note.plan}
                    onChange={(e) => handleChange("plan", e.target.value)}
                  />
                </label>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PrepSummaryPanel;
