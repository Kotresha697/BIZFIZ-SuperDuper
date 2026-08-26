import React, { useState } from "react";
import { Link } from "react-router-dom";
import axios from "axios";

import "./index.scss";

const UserApplicationPage = () => {
  const [formData, setFormData] = useState({
    // Personal / Contact
    ownerName: "",
    dob: "",
    gender: "",
    nationalId: "",
    maritalStatus: "",
    mobileNumber: "",
    email: "",
    currentAddress: "",
    city: "",
    state: "",
    postalCode: "",
    // Business / Employment
    businessName: "",
    businessLocation: "",
    typeOfBusiness: "",
    employerName: "",
    jobTitle: "",
    experienceYears: "0",
    monthlyIncome: "",
    monthlyExpenses: "",
    // Loan
    loanType: "Personal",
    loanAmount: "",
    loanPurpose: "",
    tenure: "12",
    preferredEMIDate: "",
    // Collateral (optional)
    collateralType: "",
    collateralValue: "",
    collateralOwner: "",
    // Documents / Declaration
    uploadedDocuments: [],
    declarationSigned: false,
    signature: "",
  });

  const [submitted, setSubmitted] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const payload = {
      // Personal
      name: formData.ownerName,
      dob: formData.dob,
      gender: formData.gender,
      nationalId: formData.nationalId,
      maritalStatus: formData.maritalStatus,
      mobileNumber: formData.mobileNumber || "0000000000",
      email: formData.email,
      currentAddress: formData.currentAddress,
      city: formData.city,
      businessState: formData.state || "Unknown",
      businessDistrict: formData.postalCode || "Unknown",

      // Employment / Business
      typeOfBusiness: formData.typeOfBusiness || formData.businessName,
      businessName: formData.businessName,
      businessAddress: formData.businessLocation,
      businessPinCode: formData.postalCode || formData.businessLocation || "000000",
      businessDistrict: formData.city || formData.businessLocation || "Unknown",
      employerName: formData.employerName,
      jobTitle: formData.jobTitle,
      yearsInBusiness: parseInt(formData.experienceYears, 10) || 0,
      monthlyRevenue: parseInt((formData.monthlyIncome || "0").replace(/[^0-9]/g, ""), 10) || 0,
      monthlyExpenses: parseInt((formData.monthlyExpenses || "0").replace(/[^0-9]/g, ""), 10) || 0,

      // Loan details
      loanType: formData.loanType,
      amountApplied: parseInt((formData.loanAmount || "0").replace(/[^0-9]/g, ""), 10) || 0,
      purposeOfLoan: formData.loanPurpose,
      tenureMonths: parseInt(formData.tenure, 10) || 12,
      preferredEMIDate: formData.preferredEMIDate,

      // Financial
      existingLoan: !!formData.existingLoan,
      existingLoanAmount: parseInt((formData.existingLoanAmount || "0").replace(/[^0-9]/g, ""), 10) || 0,
      bankName: formData.bankName || "",
      bankAccountNumber: formData.accountNumber || "",

      // Collateral
      collateralType: formData.collateralType || "",
      collateralValue: parseFloat((formData.collateralValue || "0").replace(/[^0-9.]/g, "")) || 0,
      collateralOwner: formData.collateralOwner || "",

      // Documents / Declaration
      uploadedDocuments: formData.uploadedDocuments || [],
      declarationSigned: !!formData.declarationSigned,
      signature: formData.signature || "",

      applicationStatus: 0,
      applicationDate: new Date().toISOString(),
    };

    try {
      const response = await axios.post("http://127.0.0.1:8000/api/borrower/submit", payload, {
        headers: { "Content-Type": "application/json" },
      });

      setSubmitted(true);
      setFormData({
        businessName: "",
        ownerName: "",
        loanAmount: "",
        loanPurpose: "",
        businessLocation: "",
        tenure: "12",
      });

      setTimeout(() => setSubmitted(false), 3000);
    } catch (error) {
      console.error("Submit Error:", error);
      alert("Error submitting application. Please try again.");
    }
  };

  return (
    <div className="user-apply-page">
      <div className="page-header">
        <div>
          <p className="subtitle">User Application Portal</p>
          <h1>Apply for a business loan</h1>
          <p className="description">
            Fill in your details below to submit a loan request. Your application will appear in the admin panel.
          </p>
        </div>
        <Link className="back-link" to="/">
          ← Back to portal
        </Link>
      </div>

      {submitted && (
        <div className="success-message">
          ✓ Application submitted successfully! Check the admin panel to see your application.
        </div>
      )}

      <form className="application-form" onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            Business name
            <input
              type="text"
              name="businessName"
              placeholder="Enter your business name"
              value={formData.businessName}
              onChange={handleInputChange}
              required
            />
          </label>
          <label>
            Owner name
            <input
              type="text"
              name="ownerName"
              placeholder="Enter owner name"
              value={formData.ownerName}
              onChange={handleInputChange}
              required
            />
          </label>
        </div>

        <div className="form-row">
          <label>
            Loan amount
            <input
              type="text"
              name="loanAmount"
              placeholder="₹ 10,00,000"
              value={formData.loanAmount}
              onChange={handleInputChange}
              required
            />
          </label>
          <label>
            Loan purpose
            <input
              type="text"
              name="loanPurpose"
              placeholder="Inventory, equipment, payroll"
              value={formData.loanPurpose}
              onChange={handleInputChange}
              required
            />
          </label>
        </div>

        <div className="form-row">
          <label>
            Business location
            <input
              type="text"
              name="businessLocation"
              placeholder="City, state"
              value={formData.businessLocation}
              onChange={handleInputChange}
              required
            />
          </label>
          <label>
            Tenure
            <select name="tenure" value={formData.tenure} onChange={handleInputChange}>
              <option value="12">12 months</option>
              <option value="18">18 months</option>
              <option value="24">24 months</option>
              <option value="36">36 months</option>
            </select>
          </label>
        </div>

        <div className="form-info">
          <p>
            Your application data is submitted to the backend and displayed in the admin panel for review.
          </p>
        </div>

        <button className="submit-button" type="submit">
          Submit application
        </button>
      </form>
    </div>
  );
};

export default UserApplicationPage;
