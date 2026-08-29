import React, { useState } from "react";
import api from "./api";
import { stateData } from "./util/stateData";
import "./Form.css";

// ---------------------------------------------------------------------------
// BizFiz enhanced loan application form.
//
// This is the SINGLE active loan form (section 11). It collects every field the
// backend / scoring engine needs, using the canonical names from section 12, and
// submits to the existing POST /api/borrower/submit endpoint. Values the user
// types are sent to the backend exactly (section 14) — no financial value is
// ever hardcoded or defaulted on the client.
// ---------------------------------------------------------------------------

// Business sectors the scoring engine understands (ratings.SECTOR_RATINGS). The
// value submitted is the canonical `businessSector`; the labels are display-only.
const SECTORS = [
  { value: "fashion", label: "Fashion" },
  { value: "hospitality", label: "Hospitality" },
  { value: "jewellery", label: "Diamond, Gems & Jewellery" },
  { value: "entertainment", label: "Entertainment" },
  { value: "daily-essentials", label: "Daily Essentials" }
];

const CATEGORIES = ["Retail", "Wholesale", "Manufacturing", "Services", "Trading", "Online / E-commerce", "Other"];
const PURPOSES = ["Working Capital", "Business Expansion", "Equipment Purchase", "Inventory Purchase", "Marketing", "Debt Consolidation", "Other"];
const TENURES = [6, 12, 18, 24, 36, 48, 60];

const STEPS = ["Personal", "Business", "Financial", "Loan", "Review"];

const INITIAL = {
  name: "",
  mobileNumber: "",
  email: "",
  businessName: "",
  businessSector: "",
  businessCategory: "",
  businessAddress: "",
  businessState: "",
  businessDistrict: "",
  businessPinCode: "",
  yearsInBusiness: "",
  monthlyRevenue: "",
  monthlyTransactionCount: "",
  averageTransactionValue: "",
  digitalPaymentPercentage: "",
  amountApplied: "",
  purposeOfLoan: "",
  tenureMonths: "",
  declaration: false,
  consent: false
};

const isBlank = (v) => v === null || v === undefined || String(v).trim() === "";

export default function Form({ onSubmitSuccess, onSubmit }) {
  const [step, setStep] = useState(0);
  const [values, setValues] = useState(INITIAL);
  const [errors, setErrors] = useState({});
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  const setField = (name, value) => {
    setValues((prev) => Object.assign({}, prev, { [name]: value }));
    setErrors((prev) => (prev[name] ? Object.assign({}, prev, { [name]: "" }) : prev));
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setField(name, type === "checkbox" ? checked : value);
  };

  // Validate only the fields belonging to the current step. Returns an errors
  // object (empty === valid).
  const validateStep = (current) => {
    const e = {};
    if (current === 0) {
      if (isBlank(values.name)) e.name = "Please enter your full name.";
      if (!/^\d{10}$/.test(String(values.mobileNumber))) e.mobileNumber = "Enter a valid 10-digit mobile number.";
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(values.email))) e.email = "Enter a valid email address.";
    } else if (current === 1) {
      if (isBlank(values.businessName)) e.businessName = "Please enter your business name.";
      if (isBlank(values.businessSector)) e.businessSector = "Select your business sector.";
      if (isBlank(values.businessCategory)) e.businessCategory = "Select a business category.";
      if (isBlank(values.businessAddress)) e.businessAddress = "Please enter your business address.";
      if (isBlank(values.businessState)) e.businessState = "Select your state.";
      if (isBlank(values.businessDistrict)) e.businessDistrict = "Please enter your district.";
      if (!/^\d{6}$/.test(String(values.businessPinCode))) e.businessPinCode = "Pincode must be exactly 6 digits.";
      if (isBlank(values.yearsInBusiness) || Number(values.yearsInBusiness) < 0) e.yearsInBusiness = "Enter years in business.";
    } else if (current === 2) {
      if (isBlank(values.monthlyRevenue) || Number(values.monthlyRevenue) <= 0) e.monthlyRevenue = "Enter your average monthly revenue.";
      if (isBlank(values.monthlyTransactionCount) || Number(values.monthlyTransactionCount) < 0) e.monthlyTransactionCount = "Enter your monthly transaction count.";
      if (isBlank(values.averageTransactionValue) || Number(values.averageTransactionValue) < 0) e.averageTransactionValue = "Enter your average transaction value.";
      if (isBlank(values.digitalPaymentPercentage) || Number(values.digitalPaymentPercentage) < 0 || Number(values.digitalPaymentPercentage) > 100)
        e.digitalPaymentPercentage = "Enter a value between 0 and 100.";
    } else if (current === 3) {
      if (isBlank(values.amountApplied) || Number(values.amountApplied) <= 0) e.amountApplied = "Enter the loan amount (greater than 0).";
      if (isBlank(values.purposeOfLoan)) e.purposeOfLoan = "Select the purpose of the loan.";
      if (isBlank(values.tenureMonths) || Number(values.tenureMonths) <= 0) e.tenureMonths = "Select a loan tenure.";
    } else if (current === 4) {
      if (!values.declaration) e.declaration = "Please confirm the declaration.";
      if (!values.consent) e.consent = "Consent is required to process your application.";
    }
    return e;
  };

  const next = () => {
    const e = validateStep(step);
    setErrors(e);
    if (Object.keys(e).length === 0) setStep((s) => Math.min(s + 1, STEPS.length - 1));
  };

  const back = () => setStep((s) => Math.max(s - 1, 0));

  const submit = async () => {
    const e = validateStep(4);
    setErrors(e);
    if (Object.keys(e).length > 0) return;

    setSubmitting(true);
    setSubmitError("");

    // Canonical payload (section 12). Numbers are coerced from the controlled
    // state so the user's exact figures reach the backend. applicationStatus is
    // forced to Pending by the server, but sent for clarity/compatibility.
    const payload = {
      name: values.name.trim(),
      mobileNumber: String(values.mobileNumber).trim(),
      email: values.email.trim(),
      businessName: values.businessName.trim(),
      businessSector: values.businessSector,
      // Legacy alias so older backend readers never see a missing key.
      typeOfBusiness: values.businessSector,
      businessCategory: values.businessCategory,
      businessAddress: values.businessAddress.trim(),
      businessState: values.businessState,
      businessDistrict: values.businessDistrict.trim(),
      businessPinCode: String(values.businessPinCode).trim(),
      yearsInBusiness: Number(values.yearsInBusiness),
      monthlyRevenue: Number(values.monthlyRevenue),
      monthlyTransactionCount: Number(values.monthlyTransactionCount),
      averageTransactionValue: Number(values.averageTransactionValue),
      digitalPaymentPercentage: Number(values.digitalPaymentPercentage),
      amountApplied: Number(values.amountApplied),
      purposeOfLoan: values.purposeOfLoan,
      tenureMonths: Number(values.tenureMonths),
      applicationStatus: 0
    };

    try {
      const response = await api.post("/api/borrower/submit", payload);
      if (onSubmit) onSubmit(values);
      setResult(response.data || {});
    } catch (err) {
      console.error("Loan application submission failed:", err);
      let message = "Unable to submit your application. Please try again.";
      if (err && err.response && err.response.data && typeof err.response.data.detail === "string") {
        message = err.response.data.detail;
      } else if (!err || !err.response) {
        message = "Unable to connect to the server. Please ensure the backend is running.";
      }
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  // ---- Success screen -----------------------------------------------------
  // Business rule 12: the borrower must NOT see their BizFiz score or risk here.
  // Only the application id, the amount they requested, and the pending status.
  if (result) {
    const requested =
      result.amountApplied === null || result.amountApplied === undefined || result.amountApplied === ""
        ? values.amountApplied
        : result.amountApplied;
    const requestedText =
      requested === null || requested === undefined || requested === "" || Number(requested) === 0
        ? "N/A"
        : "₹" + Number(requested).toLocaleString("en-IN");
    return (
      <div className="loan-application form-success">
        <div className="success-mark">✓</div>
        <p className="eyebrow">Application submitted</p>
        <h1>Thank you, {values.name || "applicant"}.</h1>
        <p>Your loan application has been received and is now pending review by our bank partners.</p>
        <dl>
          <div>
            <dt>Application ID</dt>
            <dd>{result.userId || "N/A"}</dd>
          </div>
          <div>
            <dt>Requested Amount</dt>
            <dd>{requestedText}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>Pending</dd>
          </div>
        </dl>
        <div className="form-actions" style={{ justifyContent: "center" }}>
          <button type="button" onClick={() => (onSubmitSuccess ? onSubmitSuccess(result) : null)}>
            Go to Dashboard
          </button>
        </div>
      </div>
    );
  }

  const field = (name, label, opts = {}) => {
    const { type = "text", placeholder = "", min, max, inputMode } = opts;
    return (
      <div className="form-field">
        <label htmlFor={name}>{label}</label>
        <input
          id={name}
          name={name}
          type={type}
          inputMode={inputMode}
          min={min}
          max={max}
          placeholder={placeholder}
          value={values[name]}
          onChange={handleChange}
        />
        {errors[name] ? <p className="field-error">{errors[name]}</p> : null}
      </div>
    );
  };

  const select = (name, label, options) => (
    <div className="form-field">
      <label htmlFor={name}>{label}</label>
      <select id={name} name={name} value={values[name]} onChange={handleChange}>
        <option value="">Select {label.toLowerCase()}</option>
        {options.map((o) => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
      {errors[name] ? <p className="field-error">{errors[name]}</p> : null}
    </div>
  );

  return (
    <div className="loan-application">
      <div className="form-header">
        <div>
          <p className="eyebrow">BIZFIZ / Loan Application</p>
          <h1>Apply for a Business Loan</h1>
          <p>Tell us about your business. Your figures drive your BizFiz score — enter them accurately.</p>
        </div>
      </div>

      <div className="form-stepper">
        {STEPS.map((label, i) => (
          <div key={label} className={i <= step ? "step active" : "step"}>
            <span>{i + 1}</span>
            <small>{label}</small>
          </div>
        ))}
      </div>

      {submitError ? <div className="form-alert" role="alert">{submitError}</div> : null}

      <form onSubmit={(e) => e.preventDefault()}>
        {step === 0 ? (
          <div className="form-section">
            <div className="section-heading">
              <span>01</span>
              <div>
                <h2>Personal Information</h2>
                <p>How the bank can identify and reach you.</p>
              </div>
            </div>
            <div className="form-grid">
              {field("name", "Full Name", { placeholder: "e.g. Ramesh Patel" })}
              {field("mobileNumber", "Mobile Number", { type: "tel", inputMode: "numeric", placeholder: "10-digit mobile number" })}
              {field("email", "Email", { type: "email", placeholder: "ramesh@example.com" })}
            </div>
          </div>
        ) : null}

        {step === 1 ? (
          <div className="form-section">
            <div className="section-heading">
              <span>02</span>
              <div>
                <h2>Business Information</h2>
                <p>Details about your business and where it operates.</p>
              </div>
            </div>
            <div className="form-grid">
              {field("businessName", "Business Name", { placeholder: "e.g. Test Fashion Store" })}
              {select("businessSector", "Business Sector", SECTORS)}
              {select("businessCategory", "Business Category", CATEGORIES.map((c) => ({ value: c, label: c })))}
              {field("yearsInBusiness", "Years in Business", { type: "number", inputMode: "numeric", min: 0, placeholder: "e.g. 3" })}
              {field("businessAddress", "Business Address", { placeholder: "Shop / street / area" })}
              <div className="form-field">
                <label htmlFor="businessState">State</label>
                <select id="businessState" name="businessState" value={values.businessState} onChange={handleChange}>
                  <option value="">Select state</option>
                  {stateData.map((s) => (
                    <option key={s.value} value={s.value}>{s.text}</option>
                  ))}
                </select>
                {errors.businessState ? <p className="field-error">{errors.businessState}</p> : null}
              </div>
              {field("businessDistrict", "District", { placeholder: "e.g. Bengaluru Urban" })}
              {field("businessPinCode", "Pincode", { inputMode: "numeric", placeholder: "6-digit pincode" })}
            </div>
          </div>
        ) : null}

        {step === 2 ? (
          <div className="form-section">
            <div className="section-heading">
              <span>03</span>
              <div>
                <h2>Financial Information</h2>
                <p>These figures directly influence your BizFiz score.</p>
              </div>
            </div>
            <div className="form-grid">
              {field("monthlyRevenue", "Monthly Revenue (₹)", { type: "number", inputMode: "numeric", min: 0, placeholder: "e.g. 150000" })}
              {field("monthlyTransactionCount", "Monthly Transaction Count", { type: "number", inputMode: "numeric", min: 0, placeholder: "e.g. 800" })}
              {field("averageTransactionValue", "Average Transaction Value (₹)", { type: "number", inputMode: "numeric", min: 0, placeholder: "e.g. 400" })}
              {field("digitalPaymentPercentage", "Digital Payment %", { type: "number", inputMode: "numeric", min: 0, max: 100, placeholder: "0 - 100" })}
            </div>
          </div>
        ) : null}

        {step === 3 ? (
          <div className="form-section">
            <div className="section-heading">
              <span>04</span>
              <div>
                <h2>Loan Information</h2>
                <p>How much you need and what it is for.</p>
              </div>
            </div>
            <div className="form-grid">
              {field("amountApplied", "Requested Loan Amount (₹)", { type: "number", inputMode: "numeric", min: 1, placeholder: "e.g. 150000" })}
              {select("purposeOfLoan", "Purpose of Loan", PURPOSES.map((p) => ({ value: p, label: p })))}
              {select("tenureMonths", "Loan Tenure", TENURES.map((t) => ({ value: t, label: t + " months" })))}
            </div>
          </div>
        ) : null}

        {step === 4 ? (
          <div className="form-section">
            <div className="section-heading">
              <span>05</span>
              <div>
                <h2>Review & Declaration</h2>
                <p>Confirm the details below are accurate before submitting.</p>
              </div>
            </div>

            <div className="form-notice">
              <strong>{values.businessName || "Your business"}</strong> · {SECTORS.filter((s) => s.value === values.businessSector).map((s) => s.label)[0] || "—"}<br />
              Requested: ₹{values.amountApplied ? Number(values.amountApplied).toLocaleString("en-IN") : "0"} · Tenure: {values.tenureMonths || "—"} months · Monthly revenue: ₹{values.monthlyRevenue ? Number(values.monthlyRevenue).toLocaleString("en-IN") : "0"}
            </div>

            <label className="declaration">
              <input type="checkbox" name="declaration" checked={values.declaration} onChange={handleChange} />
              <span>I declare that the information provided in this application is true and correct to the best of my knowledge.</span>
            </label>
            {errors.declaration ? <p className="field-error">{errors.declaration}</p> : null}

            <label className="declaration" style={{ marginTop: "12px" }}>
              <input type="checkbox" name="consent" checked={values.consent} onChange={handleChange} />
              <span>I consent to BizFiz processing my business and financial information to assess this loan application.</span>
            </label>
            {errors.consent ? <p className="field-error">{errors.consent}</p> : null}
          </div>
        ) : null}

        <div className="form-actions">
          <button type="button" className="secondary-button" onClick={back} disabled={step === 0 || submitting}>
            Back
          </button>
          {step < STEPS.length - 1 ? (
            <button type="button" onClick={next}>Continue</button>
          ) : (
            <button type="button" onClick={submit} disabled={submitting}>
              {submitting ? "Submitting..." : "Submit Application"}
            </button>
          )}
        </div>
      </form>
    </div>
  );
}
