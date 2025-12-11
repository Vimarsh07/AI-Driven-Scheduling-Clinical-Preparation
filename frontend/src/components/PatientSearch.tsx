import React, { useEffect, useState } from "react";
import api from "../api/client";

export type Patient = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
};

type Props = {
  onSelect: (patient: Patient) => void;
  selectedPatientId: number | null;
};

const PatientSearch: React.FC<Props> = ({ onSelect, selectedPatientId }) => {
  const [query, setQuery] = useState("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);

  const loadPatients = async (q?: string) => {
    setLoading(true);
    const res = await api.get<Patient[]>("/patients", {
      params: q ? { query: q } : {},
    });
    setPatients(res.data);
    setLoading(false);
  };

  useEffect(() => {
    loadPatients();
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadPatients(query);
  };

  return (
    <div className="card">
      <h2>1. Select Patient</h2>
      <form onSubmit={handleSearch} className="row">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search by name, email, or phone"
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>
      <ul className="list">
        {patients.map((p) => {
          const isSelected = selectedPatientId === p.id;
          return (
            <li
              key={p.id}
              className={
                isSelected
                  ? "patient-item patient-item-selected"
                  : "patient-item"
              }
            >
              <button
                className="link"
                type="button"
                onClick={() => onSelect(p)}
              >
                {p.first_name} {p.last_name} – {p.email}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
};

export default PatientSearch;
