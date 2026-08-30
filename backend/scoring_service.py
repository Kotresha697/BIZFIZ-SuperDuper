from typing import Dict, Any

from . import pulse_service

from .ratings import (
    competitor_analysis,
    opportunity_rating,
    sectoral_analysis,
    relative_prosperity,
    ease_of_business,
)


# ============================================================
# BIZFIZ WEIGHTS
# ============================================================

SCORING_WEIGHTS = {
    "location_strength": 0.25,
    "sector_trend": 0.20,
    "regional_payment_activity": 0.15,
    "merchant_financials": 0.20,
    "digital_adoption": 0.20,
}


# ============================================================
# HELPERS
# ============================================================

def _clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 100.0
) -> float:
    return round(
        max(
            minimum,
            min(maximum, float(value))
        ),
        2
    )


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ============================================================
# MAIN SCORE
# ============================================================

def calculate_bizfiz_score(
    application: Dict[str, Any]
) -> Dict[str, Any]:

    """
    BizFiz Business Sensitive Score Engine.

    Score range: 0 - 100.

    Components:

    1. Location Strength              25%
    2. Sector Trend                   20%
    3. Regional Payment Activity      15%
    4. Merchant Financial Health      20%
    5. Digital Adoption               20%
    """

    # --------------------------------------------------------
    # INPUTS
    # --------------------------------------------------------

    state = application.get(
        "businessState",
        "Karnataka"
    )

    district = application.get(
        "businessDistrict",
        "Bangalore Urban"
    )

    pincode = application.get(
        "businessPinCode",
        "560001"
    )

    sector = application.get(
        "businessSector",
        application.get(
            "typeOfBusiness",
            "daily-essentials"
        )
    )

    revenue = _float(
        application.get(
            "monthlyRevenue",
            100000
        ),
        100000
    )

    requested_amount = _float(
        application.get(
            "amountApplied",
            application.get(
                "requestedAmount",
                500000
            )
        ),
        500000
    )

    years_in_biz = _int(
        application.get(
            "yearsInBusiness",
            2
        ),
        2
    )

    digital_pct = _float(
        application.get(
            "digitalPaymentPercentage",
            50
        ),
        50
    )

    digital_pct = _clamp(
        digital_pct
    )

    # --------------------------------------------------------
    # ANALYTICS
    # --------------------------------------------------------

    competition_data = competitor_analysis(
        pincode,
        sector
    )

    opportunity_data = opportunity_rating(
        state,
        district
    )

    sector_data = sectoral_analysis(
        sector
    )

    prosperity_data = relative_prosperity(
        state,
        district
    )

    ease_data = ease_of_business(
        pincode,
        state
    )

    # --------------------------------------------------------
    # PHONEPE DATA
    # --------------------------------------------------------

    district_tx_stats = (
        pulse_service
        .get_district_transaction_stats(
            state,
            district
        )
    )

    district_user_stats = (
        pulse_service
        .get_district_user_stats(
            state,
            district
        )
    )

    state_trends = (
        pulse_service
        .get_state_sector_trends(
            state,
            sector
        )
    )

    # ========================================================
    # 1. LOCATION STRENGTH
    # ========================================================

    opportunity_score = _float(
        opportunity_data.get(
            "rating",
            68
        ),
        68
    )

    prosperity_score = _float(
        prosperity_data.get(
            "rating",
            68
        ),
        68
    )

    location_strength = _clamp(
        (opportunity_score * 0.40)
        +
        (prosperity_score * 0.60)
    )

    # ========================================================
    # 2. SECTOR TREND
    # ========================================================

    base_sector_score = _float(
        sector_data.get(
            "rating",
            70
        ),
        70
    )

    growth_rate = _float(
        state_trends.get(
            "annualMerchantGrowthRate",
            10
        ),
        10
    )

    growth_rate = max(
        -20,
        min(
            30,
            growth_rate
        )
    )

    sector_trend = _clamp(
        base_sector_score
        +
        (growth_rate * 0.30),
        30,
        98
    )

    # ========================================================
    # 3. REGIONAL PAYMENT ACTIVITY
    # ========================================================

    if district_tx_stats.get("found"):

        total_districts = max(
            _int(
                district_tx_stats.get(
                    "totalDistricts",
                    1
                ),
                1
            ),
            1
        )

        rank = max(
            _int(
                district_tx_stats.get(
                    "districtRank",
                    total_districts
                ),
                total_districts
            ),
            1
        )

        # Top district ≈ 100
        # Bottom district ≈ 40
        regional_activity = (
            100
            -
            (
                ((rank - 1) / total_districts)
                * 60
            )
        )

    else:
        regional_activity = 68

    regional_activity = _clamp(
        regional_activity
    )

    # ========================================================
    # 4. MERCHANT FINANCIAL HEALTH
    # ========================================================

    annual_revenue = revenue * 12

    financial_score = 55.0

    if annual_revenue > 0:

        loan_to_revenue = (
            requested_amount /
            annual_revenue
        )

        if loan_to_revenue <= 0.20:
            financial_score += 25

        elif loan_to_revenue <= 0.40:
            financial_score += 15

        elif loan_to_revenue <= 0.60:
            financial_score += 0

        elif loan_to_revenue <= 1.00:
            financial_score -= 10

        else:
            financial_score -= 25

    else:
        financial_score -= 25

    # Business age.

    if years_in_biz >= 5:
        financial_score += 15

    elif years_in_biz >= 3:
        financial_score += 10

    elif years_in_biz >= 2:
        financial_score += 5

    elif years_in_biz < 1:
        financial_score -= 10

    merchant_financials = _clamp(
        financial_score,
        10,
        98
    )

    # ========================================================
    # 5. DIGITAL ADOPTION
    # ========================================================

    digital_adoption = _clamp(
        digital_pct
    )

    # ========================================================
    # FINAL SCORE
    # ========================================================

    final_score = round(

        (
            location_strength
            *
            SCORING_WEIGHTS[
                "location_strength"
            ]
        )

        +

        (
            sector_trend
            *
            SCORING_WEIGHTS[
                "sector_trend"
            ]
        )

        +

        (
            regional_activity
            *
            SCORING_WEIGHTS[
                "regional_payment_activity"
            ]
        )

        +

        (
            merchant_financials
            *
            SCORING_WEIGHTS[
                "merchant_financials"
            ]
        )

        +

        (
            digital_adoption
            *
            SCORING_WEIGHTS[
                "digital_adoption"
            ]
        ),

        2
    )

    # ========================================================
    # RISK / DECISION
    # ========================================================

    if final_score >= 75:

        risk_category = "Low"
        recommendation = "Approved"

        eligible_ratio = min(
            0.95,
            final_score / 100
        )

    elif final_score >= 55:

        risk_category = "Moderate"
        recommendation = "Conditionally Approved"

        eligible_ratio = min(
            0.75,
            max(
                0,
                (final_score - 10) / 100
            )
        )

    elif final_score >= 40:

        risk_category = "High"
        recommendation = "Under Review"

        eligible_ratio = min(
            0.40,
            final_score / 150
        )

    else:

        risk_category = "High"
        recommendation = "Rejected"

        eligible_ratio = 0

    eligible_amount = int(
        requested_amount
        *
        eligible_ratio
    )

    # ========================================================
    # EXPLAINABLE FACTORS
    # ========================================================

    positive_factors = []
    risk_factors = []

    # Location.

    if location_strength >= 75:

        positive_factors.append(
            f"Strong regional economic footprint "
            f"in {str(district).title()} "
            f"(Location Score: "
            f"{location_strength}/100)."
        )

    elif location_strength >= 55:

        positive_factors.append(
            f"Moderate regional opportunity "
            f"in {str(district).title()} "
            f"(Location Score: "
            f"{location_strength}/100)."
        )

    else:

        risk_factors.append(
            f"Developing regional opportunity "
            f"in {str(district).title()} "
            f"(Location Score: "
            f"{location_strength}/100)."
        )

    # Competition.

    competition_score = _float(
        competition_data.get(
            "rating",
            50
        ),
        50
    )

    competitor_count = (
        competition_data.get(
            "competitorCount"
        )
    )

    if competition_score >= 75:

        positive_factors.append(
            "Competition conditions are favorable "
            "for the selected business sector."
        )

    elif competition_score <= 40:

        if competitor_count is not None:

            risk_factors.append(
                f"High local competition detected "
                f"({competitor_count} nearby businesses)."
            )

        else:

            risk_factors.append(
                "Competition data indicates a "
                "challenging local market."
            )

    # Digital adoption.

    if digital_adoption >= 70:

        positive_factors.append(
            f"Strong digital transaction penetration "
            f"({digital_adoption}% of sales)."
        )

    elif digital_adoption >= 50:

        positive_factors.append(
            f"Moderate digital payment adoption "
            f"({digital_adoption}% of sales)."
        )

    else:

        risk_factors.append(
            f"High reliance on cash transactions "
            f"({round(100 - digital_adoption, 2)}% cash)."
        )

    # Sector.

    if sector_trend >= 75:

        positive_factors.append(
            f"Resilient business trend in the "
            f"{str(sector).title()} sector."
        )

    elif sector_trend < 55:

        risk_factors.append(
            f"Weaker sector trend for "
            f"{str(sector).title()}."
        )

    # Business age.

    if years_in_biz >= 5:

        positive_factors.append(
            f"Established operating history "
            f"of {years_in_biz} years."
        )

    elif years_in_biz >= 3:

        positive_factors.append(
            f"Established operating history "
            f"of {years_in_biz} years."
        )

    elif years_in_biz < 1:

        risk_factors.append(
            "Very limited operating history."
        )

    else:

        risk_factors.append(
            f"Early-stage operating history "
            f"({years_in_biz} years)."
        )

    # Loan sizing.

    if annual_revenue > 0:

        loan_ratio = (
            requested_amount /
            annual_revenue
        )

        if loan_ratio <= 0.25:

            positive_factors.append(
                "Conservative loan sizing relative "
                "to annual business turnover."
            )

        elif loan_ratio > 0.50:

            risk_factors.append(
                "Requested loan is relatively high "
                "compared with annual projected turnover."
            )

    # Fallback.

    if not positive_factors:

        positive_factors.append(
            "Standard business baseline met."
        )

    if not risk_factors:

        risk_factors.append(
            "No critical credit anomalies detected."
        )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "bizfizScore": final_score,

        "scoreBreakdown": {

            "locationStrength":
                location_strength,

            "sectorTrend":
                sector_trend,

            "regionalPaymentActivity":
                regional_activity,

            "merchantFinancials":
                merchant_financials,

            "digitalAdoption":
                digital_adoption,
        },

        "riskCategory":
            risk_category,

        "recommendation":
            recommendation,

        "disclaimer":
            "BizFiz Recommendation — Final approval "
            "subject to bank verification.",

        "requestedAmount":
            int(requested_amount),

        "eligibleAmount":
            eligible_amount,

        "positiveFactors":
            positive_factors,

        "riskFactors":
            risk_factors,

        "regionalIntelligence": {

            "state":
                state,

            "district":
                district,

            "sector":
                sector,

            "districtTransactionStats":
                district_tx_stats,

            "districtUserStats":
                district_user_stats,

            "sectorGrowthTrend":
                state_trends,
        },

        "indicators": [

            competition_data,

            opportunity_data,

            sector_data,

            prosperity_data,

            ease_data,
        ],
    }