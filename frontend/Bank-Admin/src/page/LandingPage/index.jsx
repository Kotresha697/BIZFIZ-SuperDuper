import React from "react";
import { useNavigate } from "react-router-dom";
import "./LandingPage.css";

const LandingPage = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-page">

      {/* HERO SECTION */}
      <main className="hero-section">

        {/* LEFT CONTENT */}
        <section className="hero-content">

          <div className="brand-badge">
            <span className="brand-icon">BF</span>
            <span>BIZFIZ</span>
          </div>

          <p className="hero-eyebrow">
            SMART BUSINESS LENDING PLATFORM
          </p>

          <h1>
            Business loans,
            <br />
            <span>made smarter.</span>
          </h1>

          <p className="hero-description">
            BizFiz helps growing businesses apply for loans digitally,
            understand their financial position, and receive data-driven
            lending decisions through one connected platform.
          </p>

          <div className="hero-actions">
            <button
              className="primary-button"
              onClick={() => navigate("/login")}
            >
              Apply for a Business Loan
              <span>→</span>
            </button>

            <button
              className="secondary-button"
              onClick={() => navigate("/admin-login")}
            >
              Bank Admin Login
            </button>
          </div>

          <div className="trust-row">
            <div>
              <strong>01</strong>
              <span>Digital Application</span>
            </div>

            <div>
              <strong>02</strong>
              <span>Risk Assessment</span>
            </div>

            <div>
              <strong>03</strong>
              <span>Bank Decision</span>
            </div>
          </div>

        </section>

        {/* RIGHT VISUAL */}
        <section className="hero-visual">

          <div className="visual-glow"></div>

          <div className="dashboard-card">

            <div className="dashboard-header">
              <div className="mini-brand">
                <span>BF</span>
                <div>
                  <strong>BIZFIZ</strong>
                  <small>BUSINESS LENDING</small>
                </div>
              </div>

              <span className="secure-label">
                ● Secure
              </span>
            </div>

            <div className="dashboard-title">
              <span>APPLICATION OVERVIEW</span>
              <h3>Loan Application</h3>
            </div>

            <div className="application-profile">

              <div className="profile-avatar">
                A
              </div>

              <div>
                <strong>Business Applicant</strong>
                <p>MSME / Small Business</p>
              </div>

              <span className="status-badge">
                Under Review
              </span>

            </div>

            <div className="score-card">

              <div>
                <span>Business Health</span>
                <strong>Good</strong>
              </div>

              <div className="score-circle">
                <span>78</span>
                <small>/100</small>
              </div>

            </div>

            <div className="progress-section">
              <div className="progress-label">
                <span>Application progress</span>
                <strong>75%</strong>
              </div>

              <div className="progress-bar">
                <div></div>
              </div>
            </div>

            <div className="dashboard-bottom">

              <div>
                <small>Requested Amount</small>
                <strong>₹5,00,000</strong>
              </div>

              <div>
                <small>Tenure</small>
                <strong>24 Months</strong>
              </div>

            </div>

          </div>

          {/* FLOATING CARD */}
          <div className="floating-card floating-card-top">
            <span className="floating-icon">✓</span>
            <div>
              <strong>Digital Process</strong>
              <small>Fast & structured</small>
            </div>
          </div>

          <div className="floating-card floating-card-bottom">
            <span className="floating-icon">₹</span>
            <div>
              <strong>Data Driven</strong>
              <small>Responsible lending</small>
            </div>
          </div>

        </section>

      </main>

      {/* FEATURES */}
      <section className="features-section">

        <div className="section-heading">
          <p>WHY BIZFIZ</p>
          <h2>Everything needed for smarter lending.</h2>
        </div>

        <div className="features-grid">

          <div className="feature-card">
            <div className="feature-number">01</div>
            <h3>Simple Application</h3>
            <p>
              Submit business, financial and loan information through
              a structured digital application.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-number">02</div>
            <h3>Smart Risk Assessment</h3>
            <p>
              Business information can be evaluated using structured
              financial and risk indicators.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-number">03</div>
            <h3>Transparent Review</h3>
            <p>
              Bank administrators can review applications and make
              informed lending decisions.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-number">04</div>
            <h3>Track Your Application</h3>
            <p>
              Applicants can follow their loan application and monitor
              its current status.
            </p>
          </div>

        </div>

      </section>

      {/* BOTTOM CTA */}
      <section className="bottom-cta">

        <div>
          <p>READY TO GET STARTED?</p>
          <h2>Turn your business plans into momentum.</h2>
        </div>

        <button
          className="primary-button"
          onClick={() => navigate("/login")}
        >
          Start Your Application
          <span>→</span>
        </button>

      </section>

    </div>
  );
};

export default LandingPage;