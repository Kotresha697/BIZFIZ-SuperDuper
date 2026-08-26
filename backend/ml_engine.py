import re
from .ratings import competitor_analysis, oppurtunity_rating, sectoral_analysis, relative_prosperity, ease_of_business

def verify_pan(pan: str) -> dict:
    """Validate PAN format and simulate a KYC check."""
    if not pan:
        return {"status": "FAILED", "remarks": "PAN is missing"}
    
    pan = pan.strip().upper()
    pattern = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"
    if re.match(pattern, pan):
        # Simulation: PAN starts with P means Individual, C means Company, F means Firm, etc.
        holder_type = "Individual" if pan[3] == "P" else "Business/Firm"
        return {
            "status": "VERIFIED",
            "pan": pan,
            "holderType": holder_type,
            "remarks": "PAN format verified via NSDL Registry sandbox simulation."
        }
    return {"status": "INVALID_FORMAT", "remarks": "Invalid PAN format structure."}

def verify_aadhaar(aadhaar: str) -> dict:
    """Validate Aadhaar format and simulate a verification check."""
    if not aadhaar:
        return {"status": "NOT_PROVIDED", "remarks": "Aadhaar number not provided (optional)"}
    
    aadhaar = aadhaar.strip()
    if len(aadhaar) == 12 and aadhaar.isdigit():
        return {
            "status": "VERIFIED",
            "remarks": "Aadhaar UIDAI verification success via simulated OTP sandbox."
        }
    return {"status": "INVALID_FORMAT", "remarks": "Aadhaar must be exactly 12 digits."}

def run_fraud_check(application: dict) -> dict:
    """Evaluate business application for anomalous behavior and inconsistencies."""
    flags = []
    
    revenue = float(application.get("monthlyRevenue", 0))
    tx_count = float(application.get("monthlyTransactionCount", 0))
    avg_tx_val = float(application.get("averageTransactionValue", 0))
    digital_pct = float(application.get("digitalPaymentPercentage", 0))
    requested_amount = float(application.get("amountApplied", 0))
    years_in_biz = int(application.get("yearsInBusiness", 0))
    
    # Rule 1: Revenue discrepancy
    expected_revenue_lower = tx_count * avg_tx_val * 0.7
    expected_revenue_upper = tx_count * avg_tx_val * 1.3
    if tx_count > 0 and avg_tx_val > 0:
        if revenue < expected_revenue_lower or revenue > expected_revenue_upper:
            flags.append("MONTHLY_REVENUE_INCONSISTENCY: Declared revenue deviates significantly from transaction metrics.")
            
    # Rule 2: Overleveraging
    annual_revenue = revenue * 12
    if annual_revenue > 0 and requested_amount > annual_revenue * 0.7:
        flags.append("HIGH_DEBT_TO_REVENUE_RATIO: Requested loan amount exceeds 70% of annual revenue.")
        
    # Rule 3: Extreme digital payment percentages
    if digital_pct < 0 or digital_pct > 100:
        flags.append("INVALID_DIGITAL_PCT: Digital payment percentage out of bounds.")
        
    # Rule 4: Short-lived high-volume business (high fraud risk)
    if years_in_biz <= 0 and revenue > 500000:
        flags.append("NEW_BUSINESS_HIGH_REVENUE: New business (< 1 year) reporting unusually high monthly revenues.")
        
    is_fraud_suspected = len(flags) > 0
    risk_score = len(flags) * 25 # Scale fraud risk indicator
    
    return {
        "isSuspicious": is_fraud_suspected,
        "fraudScore": min(risk_score, 100),
        "flags": flags,
        "remarks": "Fraud risk clear." if not is_fraud_suspected else f"Suspicious flags raised: {len(flags)} items detected."
    }

def evaluate_loan_decision(application: dict) -> dict:
    """
    Loan Decision Engine
    Combines PhonePe pulse location trends, sectoral growth rates, and merchant financials.
    """
    pincode = application.get("businessPinCode", "")
    state = application.get("businessState", "")
    district = application.get("businessDistrict", "")
    type_of_biz = application.get("businessSector", application.get("typeOfBusiness", "daily-essentials"))
    
    # 1. Pulse Data Indicators
    comp_analysis = competitor_analysis(pincode, type_of_biz)
    opp_rating = oppurtunity_rating(state, district)
    sec_analysis = sectoral_analysis(type_of_biz)
    rel_prosperity = relative_prosperity(state, district)
    eob_rating = ease_of_business(pincode, state)
    
    # Average of location indicators (range 0 - 100)
    pulse_score = (
        comp_analysis["rating"] +
        opp_rating["rating"] +
        sec_analysis["rating"] +
        rel_prosperity["rating"] +
        eob_rating["rating"]
    ) / 5.0
    
    # 2. Financial Metrics Score
    revenue = float(application.get("monthlyRevenue", 0))
    requested_amount = float(application.get("amountApplied", 0))
    years_in_biz = int(application.get("yearsInBusiness", 0))
    digital_pct = float(application.get("digitalPaymentPercentage", 0))
    
    # Financial Stability Subscore (0 - 100)
    financial_score = 50.0  # Base subscore
    
    # Digital payment percentage reward
    financial_score += (digital_pct - 50) * 0.4
    
    # Years in business reward
    if years_in_biz >= 5:
        financial_score += 15
    elif years_in_biz >= 2:
        financial_score += 5
    else:
        financial_score -= 10
        
    # Debt-to-Revenue penalty/reward
    annual_revenue = revenue * 12
    if annual_revenue > 0:
        ratio = requested_amount / annual_revenue
        if ratio < 0.1:
            financial_score += 15
        elif ratio > 0.5:
            financial_score -= 20
        elif ratio > 0.3:
            financial_score -= 5
    else:
        financial_score -= 20
        
    financial_score = max(0.0, min(100.0, financial_score))
    
    # 3. Overall Weighted Score (60% Financials & Business metrics, 40% PhonePe Pulse/Location trends)
    business_score = (financial_score * 0.6) + (pulse_score * 0.4)
    business_score = round(business_score, 2)
    
    # 4. Determine Approval Probability & Risk Level
    approval_prob = round(business_score, 2)
    fraud_report = run_fraud_check(application)
    
    # If fraud is highly suspected, force a REVIEW or REJECT and reduce approval probability
    if fraud_report["isSuspicious"] and fraud_report["fraudScore"] >= 50:
        approval_prob = max(10.0, approval_prob - 30.0)
    
    if approval_prob >= 75.0:
        recommendation = "APPROVE"
        risk_level = "Low"
    elif approval_prob >= 50.0:
        recommendation = "REVIEW"
        risk_level = "Medium"
    else:
        recommendation = "REJECT"
        risk_level = "High"
        
    # 5. Explainable AI Highlights (Pros and Cons)
    pros = []
    cons = []
    
    if digital_pct >= 70:
        pros.append(f"High digital payment usage ({digital_pct}%). Reduces dependency on cash books.")
    if years_in_biz >= 3:
        pros.append(f"Established business longevity ({years_in_biz} years) indicates operational stability.")
    else:
        cons.append(f"Short operating tenure ({years_in_biz} years) represents higher startup risk.")
        
    if rel_prosperity["rating"] >= 70:
        pros.append(f"Business located in a highly prosperous economic district (Score: {rel_prosperity['rating']}).")
    elif rel_prosperity["rating"] < 45:
        cons.append(f"Local district transaction velocity is low (Prosperity Score: {rel_prosperity['rating']}).")
        
    if comp_analysis["rating"] >= 80:
        pros.append("Low competitor density in immediate pincode area.")
    elif comp_analysis["rating"] < 50:
        cons.append("High local supermarket/retail competitor density in vicinity.")
        
    if annual_revenue > 0 and requested_amount < annual_revenue * 0.2:
        pros.append("Conservative loan request relative to annual top-line revenue.")
    elif annual_revenue > 0 and requested_amount > annual_revenue * 0.5:
        cons.append("Aggressive loan request exceeds 50% of annual revenue bounds.")
        
    if fraud_report["isSuspicious"]:
        cons.append("Fraud Risk Alert: Discrepancy identified between declared revenue and transaction aggregates.")
        
    # Handle empty lists
    if not pros:
        pros.append("Moderate stability across key standard baseline variables.")
    if not cons:
        cons.append("No critical negative flags identified.")
        
    # Limit allowed credit based on score and requested amount
    allowed_credit = int(requested_amount * (business_score / 100.0))
    if recommendation == "REJECT":
        allowed_credit = 0

    return {
        "businessScore": business_score,
        "approvalProbability": approval_prob,
        "riskLevel": risk_level,
        "recommendation": recommendation,
        "allowedCredit": allowed_credit,
        "explainableAI": {
            "pros": pros,
            "cons": cons
        },
        "fraudCheck": fraud_report,
        "kyc": {
            "pan": {"status": "NOT_PROVIDED"},
            "aadhaar": {"status": "NOT_PROVIDED"}
        },
        "indicators": [
            comp_analysis,
            opp_rating,
            sec_analysis,
            rel_prosperity,
            eob_rating
        ]
    }
