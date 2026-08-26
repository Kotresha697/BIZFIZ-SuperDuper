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

function hasToken() {
  return getClientToken() ? true : false;
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
                  <Redirect to="/login" />
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

            {/* Protected: borrower dashboard (home). */}
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
                  <Redirect to="/login" />
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
