from typing import Dict, Any, List
from . import pulse_service
from .ratings import competitor_analysis, oppurtunity_rating, sectoral_analysis, relative_prosperity, ease_of_business

# Configurable Weights for BizFiz Business Sensitive Scoring Engine
SCORING_WEIGHTS = {
    "location_strength": 0.25,        # 25% PhonePe pulse district economic prosperity & opportunity
    "sector_trend": 0.20,            # 20% Sectoral resilience & digital merchant adoption
    "regional_payment_activity": 0.15, # 15% District transaction velocity & user density
    "merchant_financials": 0.25,      # 25% Revenue stability, ticket size & debt-to-income ratio
    "digital_adoption": 0.15          # 15% Percentage of digital transaction volume
}

def calculate_bizfiz_score(application: Dict[str, Any]) -> Dict[str, Any]:
    """
    BizFiz Business Sensitive Score Engine (0 - 100 Scale).
    Combines:
    1. Location Strength (from PhonePe Pulse Relative Prosperity & Opportunity)
    2. Sector Trend (from Sectoral Growth Analysis)
    3. Regional Payment Activity (from District Pulse transaction volume)
    4. Merchant Financial Health (Revenue, years in business, debt-to-revenue ratio)
    5. Digital Adoption (Digital payment percentage)
    """
    state = application.get("businessState", "Karnataka")
    district = application.get("businessDistrict", "Bangalore Urban")
    pincode = application.get("businessPinCode", "560001")
    sector = application.get("businessSector", application.get("typeOfBusiness", "daily-essentials"))
    
    # 1. Location & Pulse Metrics
    comp_data = competitor_analysis(pincode, sector)
    opp_data = oppurtunity_rating(state, district)
    sec_data = sectoral_analysis(sector)
    rel_prosperity_data = relative_prosperity(state, district)
    eob_data = ease_of_business(pincode, state)
    
    district_tx_stats = pulse_service.get_district_transaction_stats(state, district)
    district_user_stats = pulse_service.get_district_user_stats(state, district)
    state_trends = pulse_service.get_state_sector_trends(state, sector)
    
    # Component Sub-scores (0 - 100)
    # Location Strength: Combine opportunity score (40%) and prosperity rating (60%)
    location_strength = round(
        (opp_data.get("rating", 70) * 0.4) + (rel_prosperity_data.get("rating", 70) * 0.6), 2
    )
    
    # Sector Trend: Combine static baseline sector score with dynamic regional merchant growth
    base_sector_score = sec_data.get("rating", 70)
    growth_boost = min(max(state_trends.get("annualMerchantGrowthRate", 10), -20), 30)
    sector_trend = round(min(max(base_sector_score + (growth_boost * 0.3), 30.0), 98.0), 2)
    
    # Regional Payment Activity: District transaction rank & user engagement
    if district_tx_stats.get("found"):
        total_d = max(district_tx_stats.get("totalDistricts", 1), 1)
        rank = district_tx_stats.get("districtRank", total_d)
        regional_activity = round(100.0 - ((rank - 1) / total_d * 60.0), 2)
    else:
        regional_activity = 68.0
        
    # Merchant Financial Health
    revenue = float(application.get("monthlyRevenue", 100000))
    requested_amount = float(application.get("amountApplied", 500000))
    years_in_biz = int(application.get("yearsInBusiness", 2))
    digital_pct = float(application.get("digitalPaymentPercentage", 50.0))
    
    financial_score = 55.0
    annual_revenue = revenue * 12
    
    if annual_revenue > 0:
        dti_ratio = requested_amount / annual_revenue
        if dti_ratio <= 0.20:
            financial_score += 25
        elif dti_ratio <= 0.40:
            financial_score += 15
        elif dti_ratio <= 0.60:
            financial_score += 0
        else:
            financial_score -= 20
    else:
        financial_score -= 25
        
    if years_in_biz >= 5:
        financial_score += 15
    elif years_in_biz >= 2:
        financial_score += 8
    elif years_in_biz < 1:
        financial_score -= 10
        
    merchant_financials = round(min(max(financial_score, 10.0), 98.0), 2)
    
    # Digital Adoption Score
    digital_adoption = round(min(max(digital_pct, 0.0), 100.0), 2)
    
    # Calculate Final Weighted BizFiz Business Sensitive Score
    final_score = round(
        (location_strength * SCORING_WEIGHTS["location_strength"]) +
        (sector_trend * SCORING_WEIGHTS["sector_trend"]) +
        (regional_activity * SCORING_WEIGHTS["regional_payment_activity"]) +
        (merchant_financials * SCORING_WEIGHTS["merchant_financials"]) +
        (digital_adoption * SCORING_WEIGHTS["digital_adoption"]),
        2
    )
    
    # Determine Risk Category & Loan Decision Recommendation
    if final_score >= 75.0:
        risk_category = "Low"
        recommendation = "Approved"
        eligible_ratio = min(0.95, final_score / 100.0)
    elif final_score >= 55.0:
        risk_category = "Moderate"
        recommendation = "Conditionally Approved"
        eligible_ratio = min(0.75, (final_score - 10) / 100.0)
    elif final_score >= 40.0:
        risk_category = "High"
        recommendation = "Under Review"
        eligible_ratio = min(0.40, final_score / 150.0)
    else:
        risk_category = "High"
        recommendation = "Rejected"
        eligible_ratio = 0.0
        
    eligible_amount = int(requested_amount * eligible_ratio)
    
    # Explainable AI Insights
    positive_factors = []
    risk_factors = []
    
    if location_strength >= 70:
        positive_factors.append(f"Strong regional economic footprint in {district.title()} (Location Score: {location_strength}/100).")
    else:
        risk_factors.append(f"District transaction velocity is developing ({district.title()} Score: {location_strength}/100).")
        
    if digital_adoption >= 60:
        positive_factors.append(f"High digital transaction penetration ({digital_adoption}% of sales via digital payment modes).")
    else:
        risk_factors.append(f"High reliance on cash transactions ({100 - digital_adoption}% cash), reducing financial visibility.")
        
    if sector_trend >= 75:
        positive_factors.append(f"Resilient merchant growth in the {sector.title()} sector across {state.title()}.")
        
    if years_in_biz >= 3:
        positive_factors.append(f"Established track record with {years_in_biz} years of continuous business operations.")
    else:
        risk_factors.append(f"Early-stage operating history ({years_in_biz} years in business).")
        
    if annual_revenue > 0 and (requested_amount / annual_revenue) > 0.5:
        risk_factors.append(f"High leverage: Requested loan is over 50% of annual projected turnover.")
    elif annual_revenue > 0 and (requested_amount / annual_revenue) <= 0.25:
        positive_factors.append("Conservative loan sizing well within business debt service capacity.")
        
    if not positive_factors:
        positive_factors.append("Standard business baseline met.")
    if not risk_factors:
        risk_factors.append("No critical credit anomalies detected.")
        
    return {
        "bizfizScore": final_score,
        "scoreBreakdown": {
            "locationStrength": location_strength,
            "sectorTrend": sector_trend,
            "regionalPaymentActivity": regional_activity,
            "merchantFinancials": merchant_financials,
            "digitalAdoption": digital_adoption
        },
        "riskCategory": risk_category,
        "recommendation": recommendation,
        "disclaimer": "BizFiz Recommendation — Final approval subject to bank verification.",
        "requestedAmount": int(requested_amount),
        "eligibleAmount": eligible_amount,
        "positiveFactors": positive_factors,
        "riskFactors": risk_factors,
        "regionalIntelligence": {
            "state": state,
            "district": district,
            "sector": sector,
            "districtTransactionStats": district_tx_stats,
            "districtUserStats": district_user_stats,
            "sectorGrowthTrend": state_trends
        },
        "indicators": [
            comp_data,
            opp_data,
            sec_data,
            rel_prosperity_data,
            eob_data
        ]
    }
