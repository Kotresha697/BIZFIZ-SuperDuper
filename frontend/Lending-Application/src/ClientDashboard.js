import React, { useEffect, useState } from "react";
import api from "./api";

// Values that may legitimately be blank on older records.
const valueOrNA = (value) =>
  value === null || value === undefined || value === "" ? "N/A" : value;

const money = (value) =>
  value === null || value === undefined || value === "" || Number(value) === 0
    ? "N/A"
    : "₹" + Number(value).toLocaleString();

// BizFiz score comes from the backend scoring engine (0-100). Never defaulted.
const score = (value) => {
  if (value === null || value === undefined || value === "") return "N/A";
  var n = Number(value);
  if (isNaN(n)) return "N/A";
  return n.toFixed(1) + " / 100";
};

// State / district are stored lower-cased by the backend; present them nicely.
const titleCase = (value) => {
  if (!value) return "N/A";
  return String(value)
    .split(" ")
    .map((word) => (word ? word.charAt(0).toUpperCase() + word.slice(1) : word))
    .join(" ");
};

const businessLabels = {
  fashion: "Fashion",
  hospitality: "Hospitality",
  jewellery: "Diamond, Gems & Jewellery",
  entertainment: "Entertainment",
  "daily-essentials": "Daily Essentials"
};
const prettyBusiness = (value) =>
  value ? (businessLabels[value] || titleCase(value)) : "N/A";

const formatDate = (value) => {
  if (!value) return "N/A";
  var d = new Date(value);
  if (isNaN(d.getTime())) return "N/A";
  return d.toLocaleDateString();
};

// Application status enum shared with the backend (ApplicationStatus).
const statusLabels = { 0: "Pending", 1: "Approved", 2: "Under Review", 3: "Rejected" };
const statusStyles = {
  0: "status-pending",
  1: "status-approved",
  2: "status-review",
  3: "status-rejected"
};

function StatusBadge({ status }) {
  const label = statusLabels[status] || "Pending";
  const style = statusStyles[status] || "status-pending";
  return <span className={"status-badge " + style}>{label}</span>;
}

// Compact at-a-glance counts computed entirely from the already-loaded list
// (no extra API call). Real numbers only — nothing is defaulted or invented.
function SummaryCards({ applications }) {
  const countBy = (status) => applications.filter((a) => a.applicationStatus === status).length;
  const cards = [
    { label: "Total", value: applications.length, color: "#4f46e5", bg: "#eef2ff" },
    { label: "Pending", value: countBy(0), color: "#1d4ed8", bg: "#dbeafe" },
    { label: "Under Review", value: countBy(2), color: "#92400e", bg: "#fef3c7" },
    { label: "Approved", value: countBy(1), color: "#166534", bg: "#dcfce7" },
    { label: "Rejected", value: countBy(3), color: "#991b1b", bg: "#fee2e2" }
  ];
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "12px",
        margin: "24px 0 4px"
      }}
    >
      {cards.map((c) => (
        <div
          key={c.label}
          style={{
            flex: "1 1 120px",
            minWidth: "120px",
            padding: "16px 18px",
            borderRadius: "12px",
            background: c.bg,
            border: "1px solid rgba(15,23,42,.06)"
          }}
        >
          <div style={{ fontSize: "26px", fontWeight: 800, color: c.color, lineHeight: 1 }}>{c.value}</div>
          <div
            style={{
              marginTop: "6px",
              fontSize: "11px",
              fontWeight: 800,
              letterSpacing: ".06em",
              textTransform: "uppercase",
              color: "#475569"
            }}
          >
            {c.label}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ClientDashboard({ onNewApplication, onLogout }) {
  const [applications, setApplications] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  let clientName = "";
  try {
    clientName = (JSON.parse(localStorage.getItem("client_user") || "{}") || {}).name || "";
  } catch (parseError) {
    clientName = "";
  }

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        setLoading(true);
        setError("");
        // Bearer token is attached automatically by the shared `api` instance.
        const response = await api.get("/api/client/applications");
        if (!active) return;
        const list = response.data || [];
        setApplications(list);
        if (list.length) {
          setSelectedUserId(list[0].userId);
        }
      } catch (requestError) {
        console.error("Error loading client applications:", requestError);
        if (active) setError("Unable to load your applications. Please try again.");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => { active = false; };
  }, []);

  // The list item already carries every field the backend exposes, so the
  // detail panel is rendered from the selected item (no separate detail call).
  const selected = applications.filter((a) => a.userId === selectedUserId)[0] || null;

  const detailRows = selected
    ? [
        ["Applicant", valueOrNA(selected.name)],
        ["Mobile", valueOrNA(selected.mobileNumber)],
        ["Business name", valueOrNA(selected.businessName)],
        ["Business type", prettyBusiness(selected.businessSector || selected.typeOfBusiness)],
        ["Business address", valueOrNA(selected.businessAddress)],
        ["District", titleCase(selected.businessDistrict)],
        ["State", titleCase(selected.businessState)],
        ["Pincode", valueOrNA(selected.businessPinCode)],
        ["Amount requested", money(selected.amountApplied)],
        ["Amount approved", money(selected.amountApproved)],
        ["BizFiz score", score(selected.bizfizScore)],
        ["Risk level", valueOrNA(selected.riskCategory)],
        ["Application date", formatDate(selected.applicationDate)]
      ]
    : [];

  return (
    <div className="client-dashboard">
      <div className="dashboard-hero">
        <div>
          <span>Client Business Portal</span>
          <h1>Welcome back{clientName ? ", " + clientName : ""}.</h1>
          <p>Track your business loan applications and their current status.</p>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={onNewApplication}>+ New application</button>
          <button type="button" onClick={onLogout}>Log out</button>
        </div>
      </div>

      {error ? (
        <div
          role="alert"
          style={{
            margin: "20px 0 0",
            padding: "12px 14px",
            borderRadius: "10px",
            background: "#fee2e2",
            border: "1px solid #fecaca",
            color: "#991b1b",
            fontSize: "13px"
          }}
        >
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="dashboard-message" style={{ marginTop: "28px" }}>
          Loading your applications...
        </div>
      ) : applications.length === 0 ? (
        <div className="dashboard-message" style={{ marginTop: "28px" }}>
          <h2>No loan applications yet</h2>
          <p>Start an application to request business funding.</p>
          <button type="button" onClick={onNewApplication}>Apply for a loan</button>
        </div>
      ) : (
        <React.Fragment>
          <SummaryCards applications={applications} />
          <div className="dashboard-grid">
          <div className="applications-panel">
            <h3>MY APPLICATIONS ({applications.length})</h3>
            {applications.map((app) => (
              <button
                key={app.userId}
                type="button"
                className={app.userId === selectedUserId ? "application-item selected" : "application-item"}
                onClick={() => setSelectedUserId(app.userId)}
              >
                <div>
                  <span>{prettyBusiness(app.businessSector || app.typeOfBusiness)}</span>
                  <StatusBadge status={app.applicationStatus} />
                </div>
                <strong>{valueOrNA(app.businessName) === "N/A" ? valueOrNA(app.name) : app.businessName}</strong>
                <small>
                  Requested: {money(app.amountApplied)} · {titleCase(app.businessDistrict)}
                </small>
              </button>
            ))}
          </div>

          <div className="application-detail-panel">
            {!selected ? (
              <div className="dashboard-message">Select an application to see its details.</div>
            ) : (
              <div className="application-details-card">
                <div className="detail-header">
                  <div>
                    <span>Application details</span>
                    <h2 style={{ margin: "6px 0 0", fontSize: "20px", color: "#172554" }}>
                      {valueOrNA(selected.businessName) === "N/A"
                        ? prettyBusiness(selected.businessSector || selected.typeOfBusiness)
                        : selected.businessName}
                    </h2>
                    <p>Application ID: {selected.userId}</p>
                  </div>
                  <StatusBadge status={selected.applicationStatus} />
                </div>
                <div className="details-grid">
                  {detailRows.map((row) => (
                    <div className="detail-item" key={row[0]}>
                      <span>{row[0]}</span>
                      <strong>{row[1]}</strong>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
        </React.Fragment>
      )}
    </div>
  );
}
