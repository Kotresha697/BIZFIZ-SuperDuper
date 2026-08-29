import React, { useState } from "react";
import api from "./api";
import { setClientSession } from "./api";

const ADMIN_PORTAL_URL =
  (process.env.REACT_APP_ADMIN_PORTAL_URL && process.env.REACT_APP_ADMIN_PORTAL_URL.trim()) ||
  "http://localhost:3001";

// Borrower / client authentication screen for the Lending-Application portal.
// Talks to the canonical backend auth APIs:
//   POST /api/auth/client/register  -> { accessToken, client }
//   POST /api/auth/client/login     -> { accessToken, client }
export default function ClientAuth({ onLoginSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    mobileNumber: "",
    password: ""
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData(Object.assign({}, formData, {
      [e.target.name]: e.target.value
    }));
    setError("");
  };

  const readError = (err, fallback) => {
    // FastAPI returns errors as { detail: "..." }
    if (err && err.response && err.response.data && err.response.data.detail) {
      var detail = err.response.data.detail;
      return typeof detail === "string" ? detail : fallback;
    }
    if (err && err.response) {
      return fallback;
    }
    return "Unable to connect to the server. Please ensure the backend is running.";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        if (!formData.name || !formData.email || !formData.mobileNumber || !formData.password) {
          setError("Please fill in all required fields.");
          setLoading(false);
          return;
        }
        if (formData.mobileNumber.length < 10) {
          setError("Please enter a valid 10-digit mobile number.");
          setLoading(false);
          return;
        }
        const res = await api.post("/api/auth/client/register", {
          name: formData.name,
          email: formData.email,
          mobileNumber: formData.mobileNumber,
          password: formData.password
        });
        setClientSession(res.data.accessToken, res.data.client);
        onLoginSuccess(res.data.client);
      } else {
        if (!formData.email || !formData.password) {
          setError("Please enter your email and password.");
          setLoading(false);
          return;
        }
        const res = await api.post("/api/auth/client/login", {
          email: formData.email,
          password: formData.password
        });
        setClientSession(res.data.accessToken, res.data.client);
        onLoginSuccess(res.data.client);
      }
    } catch (err) {
      console.error(err);
      setError(readError(err, isRegister ? "Registration failed. Please try again." : "Login failed. Please check your details."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="client-auth-page">
      <div className="client-auth-card">

        <div className="client-auth-heading">
          <div className="client-auth-mark">BF</div>
          <p className="client-auth-kicker">BIZFIZ / Smart Loan Platform</p>
          <h2>{isRegister ? "Create Client Account" : "Borrower Portal Login"}</h2>
          <p className="client-auth-subtitle">
            {isRegister
              ? "Register to apply for MSME loans with alternative credit scoring"
              : "Sign in to track your loan applications and credit scores"}
          </p>
        </div>

        <div className="client-auth-tabs">
          <button
            type="button"
            className={!isRegister ? "auth-tab active" : "auth-tab"}
            onClick={() => { setIsRegister(false); setError(""); }}
          >
            Sign In
          </button>
          <button
            type="button"
            className={isRegister ? "auth-tab active" : "auth-tab"}
            onClick={() => { setIsRegister(true); setError(""); }}
          >
            Register New Business
          </button>
        </div>

        {error ? (
          <div
            role="alert"
            style={{
              margin: "0 0 16px",
              padding: "10px 12px",
              borderRadius: "8px",
              background: "#fee2e2",
              border: "1px solid #fecaca",
              color: "#991b1b",
              fontSize: "13px"
            }}
          >
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit}>
          {isRegister ? (
            <div>
              <div>
                <label>Full Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="e.g. Ramesh Patel"
                  required
                />
              </div>
              <div>
                <label>Mobile Number</label>
                <input
                  type="tel"
                  name="mobileNumber"
                  value={formData.mobileNumber}
                  onChange={handleChange}
                  placeholder="10-digit mobile number"
                  maxLength="10"
                  required
                />
              </div>
            </div>
          ) : null}

          <div>
            <label>Email Address</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="ramesh@example.com"
              required
            />
          </div>

          <div>
            <label>Password</label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Enter your password"
              required
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Processing..." : (isRegister ? "Create Account & Continue" : "Sign In to Dashboard")}
          </button>
        </form>

        <div style={{ textAlign: "center" }}>
          <p style={{ fontSize: "12px", color: "#64748b", margin: 0 }}>
            Bank employee or administrator?{" "}
            <a
              href={ADMIN_PORTAL_URL}
              target="_blank"
              rel="noreferrer"
              style={{ fontWeight: 700, color: "#4f46e5" }}
            >
              Access Bank Admin Portal →
            </a>
          </p>
        </div>

      </div>
    </div>
  );
}
