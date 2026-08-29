import React, { useState } from "react";
import { useHistory } from "react-router-dom";
import adminApi, { setAdminSession, isAdminAuthed, USER_PORTAL_URL } from "../../api";

// Bank-Admin login. Talks to the canonical backend admin auth API:
//   POST /api/auth/admin/login -> { accessToken, admin: { username } }
const AdminLoginPage = () => {
  const history = useHistory();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Already signed in? Skip straight to the dashboard.
  if (isAdminAuthed()) {
    history.replace("/all-report");
  }

  const readError = (err) => {
    if (err && err.response && err.response.data && err.response.data.detail) {
      const detail = err.response.data.detail;
      if (typeof detail === "string") return detail;
    }
    if (err && err.response) {
      return "Login failed. Please check your credentials.";
    }
    return "Unable to connect to the server. Please ensure the backend is running.";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!username || !password) {
      setError("Please enter your username and password.");
      return;
    }
    setLoading(true);
    try {
      const res = await adminApi.post("/api/auth/admin/login", {
        username: username,
        password: password
      });
      setAdminSession(res.data.accessToken, res.data.admin);
      history.replace("/all-report");
    } catch (err) {
      console.error(err);
      setError(readError(err));
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "#0f172a",
        padding: "24px",
        boxSizing: "border-box"
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "400px",
          background: "#fff",
          borderRadius: "16px",
          padding: "34px 30px",
          boxShadow: "0 20px 50px rgba(0,0,0,0.35)"
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "24px" }}>
          <img
            src="https://i.ibb.co/6vYxk8n/logo.png"
            alt="BIZFIZ"
            style={{ width: "44px", marginBottom: "10px" }}
          />
          <div style={{ fontSize: "12px", fontWeight: 800, letterSpacing: "0.12em", color: "#4f46e5", textTransform: "uppercase" }}>
            BIZFIZ / Bank Admin
          </div>
          <h2 style={{ margin: "8px 0 4px", fontSize: "22px", color: "#0f172a" }}>
            Administrator Sign In
          </h2>
          <p style={{ margin: 0, fontSize: "13px", color: "#64748b" }}>
            Restricted access — bank staff only.
          </p>
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
          <div style={{ marginBottom: "14px" }}>
            <label style={{ display: "block", fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em", textTransform: "uppercase", color: "#334155", marginBottom: "5px" }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => { setUsername(e.target.value); setError(""); }}
              placeholder="admin"
              autoComplete="username"
              style={{
                width: "100%",
                boxSizing: "border-box",
                minHeight: "44px",
                padding: "10px 12px",
                border: "1px solid #cbd5e1",
                borderRadius: "8px",
                background: "#f8fafc",
                color: "#0f172a",
                fontSize: "14px",
                outline: "none"
              }}
            />
          </div>

          <div style={{ marginBottom: "18px" }}>
            <label style={{ display: "block", fontSize: "11px", fontWeight: 800, letterSpacing: "0.05em", textTransform: "uppercase", color: "#334155", marginBottom: "5px" }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => { setPassword(e.target.value); setError(""); }}
              placeholder="Enter your password"
              autoComplete="current-password"
              style={{
                width: "100%",
                boxSizing: "border-box",
                minHeight: "44px",
                padding: "10px 12px",
                border: "1px solid #cbd5e1",
                borderRadius: "8px",
                background: "#f8fafc",
                color: "#0f172a",
                fontSize: "14px",
                outline: "none"
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              minHeight: "44px",
              border: 0,
              borderRadius: "8px",
              color: "#fff",
              background: "#4f46e5",
              fontSize: "14px",
              fontWeight: 800,
              cursor: loading ? "wait" : "pointer",
              opacity: loading ? 0.7 : 1
            }}
          >
            {loading ? "Signing in..." : "Sign In to Admin Dashboard"}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: "20px" }}>
          <a href={USER_PORTAL_URL} style={{ fontSize: "12px", color: "#64748b", textDecoration: "none" }}>
            ← Back to home
          </a>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;
