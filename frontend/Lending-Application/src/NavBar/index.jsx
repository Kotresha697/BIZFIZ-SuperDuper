import * as React from 'react';
import './index.css'

const ADMIN_PORTAL_URL =
  (process.env.REACT_APP_ADMIN_PORTAL_URL && process.env.REACT_APP_ADMIN_PORTAL_URL.trim()) ||
  'http://localhost:3001';

export default function NavBar({ authed, onLogout }) {
  return (
    <nav className="user-nav" aria-label="BizFiz borrower navigation">
      <div>
        <a className="brand-lockup" href="/">
          <span className="brand-mark">BF</span>
          <span>
            <strong>BIZFIZ</strong>
            <small>{authed ? 'Borrower Portal' : 'Business Lending Platform'}</small>
          </span>
        </a>

        <div className="user-nav-links">
          {authed ? (
            <React.Fragment>
              <a href="/">Dashboard</a>
              <a href="/apply">Apply for Loan</a>
              <a href="/#applications">My Applications</a>
              <button type="button" onClick={onLogout}>Logout</button>
            </React.Fragment>
          ) : (
            <React.Fragment>
              <a href="/">Home</a>
              <a href="/login">User Login</a>
              <a href={ADMIN_PORTAL_URL}>Bank Admin Login</a>
            </React.Fragment>
          )}
        </div>
      </div>
    </nav>
  )
}
