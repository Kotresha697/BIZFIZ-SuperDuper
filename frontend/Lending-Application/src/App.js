import React, { useState } from "react";
import { Switch, Route, Redirect, useHistory } from "react-router-dom";
import MuiThemeProvider from "material-ui/styles/MuiThemeProvider";

import "./App.css";
import "./UserPortal.css";
import Form from "./Form";
import ConfirmationScreen from "./ConfirmationScreen";
import ClientAuth from "./ClientAuth";
import ClientDashboard from "./ClientDashboard";
import NavBar from "./NavBar";
import { getClientToken, clearClientAuth } from "./api";

const ADMIN_PORTAL_URL =
  (process.env.REACT_APP_ADMIN_PORTAL_URL && process.env.REACT_APP_ADMIN_PORTAL_URL.trim()) ||
  "http://localhost:3001";

function PublicHome({ onApply, onLogin }) {
  return (
    <div className="public-home">
      <section className="public-home-hero">
        <div className="public-home-copy">
          <p className="eyebrow">BIZFIZ / Business Lending</p>
          <h1>Intelligent Lending for Growing Businesses</h1>
          <p className="public-home-lead">Data-informed lending for MSMEs, with a simple digital application experience for borrowers and a structured review platform for lenders.</p>
          <div className="public-home-actions">
            <button type="button" onClick={onApply}>User Login / Apply for Loan</button>
            <button type="button" className="secondary" onClick={() => { window.location.href = ADMIN_PORTAL_URL; }}>Bank Admin Login</button>
          </div>
        </div>
        <div className="public-home-panel">
          <span className="public-home-mark">BF</span>
          <p className="eyebrow">Built for business owners</p>
          <h2>Clear decisions. Better momentum.</h2>
          <p>Complete one focused application and track every update from your dashboard.</p>
        </div>
      </section>
      <section className="public-home-info">
        <div>
          <p className="eyebrow">How BizFiz Works</p>
          <h2>One connected lending workflow</h2>
          <div className="public-home-steps">
            <div><strong>01 / Apply</strong><span>Submit business, financial and loan information.</span></div>
            <div><strong>02 / Analyze</strong><span>BizFiz processes structured business intelligence.</span></div>
            <div><strong>03 / Review</strong><span>Bank administrators review the application and analysis.</span></div>
            <div><strong>04 / Decide</strong><span>The bank approves, rejects or reviews the request.</span></div>
          </div>
        </div>
        <div className="public-home-responsible">
          <p className="eyebrow">Built for Responsible Business Lending</p>
          <ul>
            <li>Structured application data</li>
            <li>Consistent review workflow</li>
            <li>Role-based access</li>
            <li>Data-driven decision support</li>
            <li>Transparent application status</li>
          </ul>
        </div>
      </section>
    </div>
  );
}

function hasToken() {
  return typeof localStorage !== "undefined" && getClientToken() ? true : false;
}

// Borrower portal shell. Routing + auth state live here; individual screens are
// unchanged in look/behaviour beyond being wired to the real backend.
export default function App() {
  const history = useHistory();
  const [authed, setAuthed] = useState(hasToken());

  const handleLoginSuccess = () => {
    setAuthed(true);
    history.replace("/");
  };

  const handleLogout = () => {
    clearClientAuth();
    setAuthed(false);
    history.push("/login");
  };

  return (
    <MuiThemeProvider>
      <div className="user-portal">
        <NavBar title={"Apply for Business Loans"} authed={authed} onLogout={handleLogout} />
        <main>
          <Switch>
            {/* Public: login / register. If already signed in, go to dashboard. */}
            <Route
              path="/login"
              render={() =>
                authed ? <Redirect to="/" /> : <ClientAuth onLoginSuccess={handleLoginSuccess} />
              }
            />

            {/* Protected: new loan application form. */}
            <Route
              path="/apply"
              render={() =>
                authed ? (
                  <div style={{ textAlign: "center", padding: "28px 16px" }}>
                    <Form onSubmitSuccess={() => history.push("/")} />
                  </div>
                ) : (
                  <PublicHome onApply={() => history.push("/login")} onLogin={() => history.push("/login")} />
                )
              }
            />

            {/* Protected: legacy Setu consent confirmation screen. */}
            <Route
              path="/confirmscreen/:userId"
              render={(props) =>
                authed ? (
                  <div style={{ textAlign: "center", padding: "28px 16px" }}>
                    <ConfirmationScreen userId={props.match.params.userId} />
                  </div>
                ) : (
                  <Redirect to="/login" />
                )
              }
            />

            {/* Public: Home page with role entry points. Or dashboard if authenticated. */}
            <Route
              exact
              path="/"
              render={() =>
                authed ? (
                  <ClientDashboard
                    onNewApplication={() => history.push("/apply")}
                    onLogout={handleLogout}
                  />
                ) : (
                  <PublicHome onApply={() => history.push("/login")} onLogin={() => history.push("/login")} />
                )
              }
            />

            {/* Anything else: send to the right place based on auth state. */}
            <Route render={() => <Redirect to={authed ? "/" : "/login"} />} />
          </Switch>
        </main>
      </div>
    </MuiThemeProvider>
  );
}
