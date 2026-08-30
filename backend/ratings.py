import os
import math
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

from . import pulse_service


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "").strip()

GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"
GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"

REQUEST_TIMEOUT = 10


# ============================================================
# GENERAL HELPERS
# ============================================================

def _clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    """Keep score between minimum and maximum."""
    return round(max(minimum, min(maximum, float(value))), 2)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


# ============================================================
# GEOAPIFY
# ============================================================

def _geoapify_enabled() -> bool:
    return bool(GEOAPIFY_API_KEY)


def _geocode_location(
    pincode: str,
    state: str = "",
    district: str = ""
) -> Optional[Dict[str, float]]:
    """
    Convert Indian PIN code/location into latitude and longitude.

    Geoapify Geocoding API:
    https://api.geoapify.com/v1/geocode/search
    """

    if not _geoapify_enabled():
        return None

    pincode = str(pincode or "").strip()
    state = str(state or "").strip()
    district = str(district or "").strip()

    search_text = ", ".join(
        x for x in [pincode, district, state, "India"] if x
    )

    params = {
        "text": search_text,
        "filter": "countrycode:in",
        "limit": 1,
        "format": "json",
        "apiKey": GEOAPIFY_API_KEY,
    }

    try:
        response = requests.get(
            GEOAPIFY_GEOCODE_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            return None

        result = results[0]

        lat = result.get("lat")
        lon = result.get("lon")

        if lat is None or lon is None:
            return None

        return {
            "lat": float(lat),
            "lon": float(lon),
        }

    except Exception as exc:
        print(f"[Geoapify] Geocoding failed: {exc}")
        return None


def _search_nearby_businesses(
    lat: float,
    lon: float,
    category: str,
    radius: int = 3000,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Search nearby businesses using Geoapify Places API.
    """

    if not _geoapify_enabled():
        return {
            "enabled": False,
            "found": False,
            "count": 0,
            "places": [],
            "error": "GEOAPIFY_API_KEY is not configured",
        }

    params = {
        "categories": category,
        "filter": f"circle:{lon},{lat},{radius}",
        "limit": limit,
        "apiKey": GEOAPIFY_API_KEY,
    }

    try:
        response = requests.get(
            GEOAPIFY_PLACES_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()
        features = data.get("features", [])

        places = []

        for feature in features:
            properties = feature.get("properties", {})

            places.append(
                {
                    "name": (
                        properties.get("name")
                        or properties.get("address_line1")
                        or "Unnamed business"
                    ),
                    "category": properties.get("categories", []),
                    "distance": properties.get("distance"),
                    "lat": properties.get("lat"),
                    "lon": properties.get("lon"),
                }
            )

        return {
            "enabled": True,
            "found": True,
            "count": len(places),
            "places": places,
            "error": None,
        }

    except Exception as exc:
        print(f"[Geoapify] Places API failed: {exc}")

        return {
            "enabled": True,
            "found": False,
            "count": 0,
            "places": [],
            "error": str(exc),
        }


# ============================================================
# BUSINESS SECTOR → GEOAPIFY CATEGORY
# ============================================================

SECTOR_CATEGORIES = {
    "daily-essentials": "commercial.supermarket",
    "daily essentials": "commercial.supermarket",
    "grocery": "commercial.supermarket",
    "supermarket": "commercial.supermarket",

    "fashion": "commercial.clothing",
    "clothing": "commercial.clothing",
    "apparel": "commercial.clothing",

    "jewellery": "commercial.jewelry",
    "jewelry": "commercial.jewelry",

    "hospitality": "accommodation",
    "hotel": "accommodation.hotel",

    "restaurant": "catering.restaurant",
    "food": "catering.restaurant",

    "entertainment": "entertainment",

    "pharmacy": "healthcare.pharmacy",

    "electronics": "commercial.electronics",

    "furniture": "commercial.furniture",

    "automobile": "commercial.vehicle",

    "beauty": "commercial",
    "salon": "commercial",

    "education": "education",

    "healthcare": "healthcare",

    "retail": "commercial",
    "shop": "commercial",
}


def _get_sector_category(sector: str) -> str:
    normalized = _normalize_text(sector)

    if normalized in SECTOR_CATEGORIES:
        return SECTOR_CATEGORIES[normalized]

    # Partial matching
    if "grocery" in normalized or "supermarket" in normalized:
        return "commercial.supermarket"

    if "jewel" in normalized:
        return "commercial.jewelry"

    if "fashion" in normalized or "cloth" in normalized:
        return "commercial.clothing"

    if "restaurant" in normalized or "food" in normalized:
        return "catering.restaurant"

    if "hotel" in normalized or "hospitality" in normalized:
        return "accommodation"

    if "pharmacy" in normalized:
        return "healthcare.pharmacy"

    return "commercial"


# ============================================================
# 1. COMPETITOR ANALYSIS
# ============================================================

def competitor_analysis(
    pincode: str,
    sector: str = "daily-essentials"
) -> Dict[str, Any]:
    """
    Calculate competition score using Geoapify.

    Important:
        More competitors = MORE competition = LOWER score.

    Score interpretation:

        0-30   Very High Competition
        31-50  High Competition
        51-70  Moderate Competition
        71-85  Low Competition
        86-100 Very Low Competition

    This function intentionally returns a COMPETITION QUALITY SCORE,
    where a higher number means a better environment for the applicant.
    """

    pincode = str(pincode or "").strip()
    sector = sector or "daily-essentials"

    # Without API key, return neutral score.
    if not _geoapify_enabled():
        return {
            "name": "Competition Score",
            "rating": 50.0,
            "score": 50.0,
            "competitorCount": None,
            "competitionLevel": "Unknown",
            "source": "Geoapify unavailable",
            "message": "Geoapify API key is not configured.",
            "sector": sector,
            "pincode": pincode,
        }

    # Geocode the PIN.
    location = _geocode_location(
        pincode=pincode,
        state="",
        district="",
    )

    if not location:
        return {
            "name": "Competition Score",
            "rating": 50.0,
            "score": 50.0,
            "competitorCount": None,
            "competitionLevel": "Unknown",
            "source": "Geoapify",
            "message": "Unable to geocode the supplied PIN code.",
            "sector": sector,
            "pincode": pincode,
        }

    category = _get_sector_category(sector)

    places_data = _search_nearby_businesses(
        lat=location["lat"],
        lon=location["lon"],
        category=category,
        radius=3000,
        limit=100,
    )

    if not places_data.get("found"):
        return {
            "name": "Competition Score",
            "rating": 50.0,
            "score": 50.0,
            "competitorCount": None,
            "competitionLevel": "Unknown",
            "source": "Geoapify",
            "message": places_data.get(
                "error",
                "No competitor data available."
            ),
            "sector": sector,
            "category": category,
            "pincode": pincode,
        }

    competitor_count = places_data.get("count", 0)

    # --------------------------------------------------------
    # Competition scoring
    #
    # 0 competitors       = 95
    # 1-5 competitors     = 90-80
    # 6-15 competitors    = 79-65
    # 16-30 competitors   = 64-45
    # 31-50 competitors   = 44-30
    # 50+ competitors     = 30 or below
    # --------------------------------------------------------

    if competitor_count == 0:
        score = 95.0
    elif competitor_count <= 5:
        score = 90.0 - (competitor_count * 2.0)
    elif competitor_count <= 15:
        score = 80.0 - ((competitor_count - 5) * 1.5)
    elif competitor_count <= 30:
        score = 65.0 - ((competitor_count - 15) * 1.33)
    elif competitor_count <= 50:
        score = 45.0 - ((competitor_count - 30) * 0.75)
    else:
        score = 30.0 - min((competitor_count - 50) * 0.20, 25.0)

    score = _clamp(score)

    if competitor_count <= 5:
        competition_level = "Very Low"
    elif competitor_count <= 15:
        competition_level = "Low"
    elif competitor_count <= 30:
        competition_level = "Moderate"
    elif competitor_count <= 50:
        competition_level = "High"
    else:
        competition_level = "Very High"

    return {
        "name": "Competition Score",
        "rating": score,
        "score": score,
        "competitorCount": competitor_count,
        "competitionLevel": competition_level,
        "source": "Geoapify Places API",
        "sector": sector,
        "category": category,
        "pincode": pincode,
        "searchRadiusMeters": 3000,
        "latitude": location["lat"],
        "longitude": location["lon"],
        "message": (
            f"{competitor_count} nearby businesses found "
            f"for the selected sector."
        ),
    }


# ============================================================
# 2. OPPORTUNITY RATING
# ============================================================

def opportunity_rating(
    state: str,
    district: str
) -> Dict[str, Any]:
    """
    Estimate business opportunity using PhonePe Pulse data.

    Higher payment activity + stronger user adoption
    = higher opportunity.
    """

    tx = pulse_service.get_district_transaction_stats(
        state,
        district
    )

    users = pulse_service.get_district_user_stats(
        state,
        district
    )

    if tx.get("found"):
        total_districts = max(
            _safe_int(tx.get("totalDistricts"), 1),
            1
        )

        rank = max(
            _safe_int(tx.get("districtRank"), total_districts),
            1
        )

        rank_score = 100 - (
            ((rank - 1) / total_districts) * 100
        )

        rank_score = _clamp(rank_score)
    else:
        rank_score = 68.0

    engagement_ratio = _safe_float(
        users.get("engagementRatio"),
        0.0
    )

    # Normalize engagement.
    engagement_score = _clamp(
        min(engagement_ratio / 10.0 * 100.0, 100.0)
    )

    if not users.get("found"):
        engagement_score = 60.0

    rating = round(
        (rank_score * 0.65) +
        (engagement_score * 0.35),
        2
    )

    if rating >= 75:
        category = "Strong Opportunity"
    elif rating >= 55:
        category = "Moderate Opportunity"
    else:
        category = "Developing Opportunity"

    return {
        "name": "Opportunity Score",
        "rating": _clamp(rating),
        "score": _clamp(rating),
        "category": category,
        "state": state,
        "district": district,
        "districtRank": tx.get("districtRank", 0),
        "totalDistricts": tx.get("totalDistricts", 0),
        "engagementRatio": engagement_ratio,
        "source": "PhonePe Pulse",
    }


# Backward-compatible alias.
# If old code still calls oppurtunity_rating, it will work.
oppurtunity_rating = opportunity_rating


# ============================================================
# 3. SECTORAL ANALYSIS
# ============================================================

SECTOR_BASE_SCORES = {
    "daily-essentials": 82,
    "daily essentials": 82,
    "grocery": 82,
    "supermarket": 84,

    "hospitality": 72,
    "hotel": 72,

    "jewellery": 68,
    "jewelry": 68,

    "fashion": 76,
    "clothing": 76,

    "entertainment": 70,

    "restaurant": 75,
    "food": 76,

    "pharmacy": 86,
    "healthcare": 84,

    "electronics": 74,

    "furniture": 70,

    "automobile": 73,

    "education": 80,

    "retail": 78,
}


def sectoral_analysis(sector: str) -> Dict[str, Any]:
    """Return baseline sector attractiveness score."""

    normalized = _normalize_text(sector)

    base_score = SECTOR_BASE_SCORES.get(
        normalized,
        75
    )

    # Partial matching.
    if normalized not in SECTOR_BASE_SCORES:

        if "grocery" in normalized:
            base_score = 82

        elif "food" in normalized:
            base_score = 76

        elif "hotel" in normalized:
            base_score = 72

        elif "jewel" in normalized:
            base_score = 68

        elif "pharmacy" in normalized:
            base_score = 86

        elif "fashion" in normalized:
            base_score = 76

        elif "education" in normalized:
            base_score = 80

    return {
        "name": "Sectoral Score",
        "rating": float(base_score),
        "score": float(base_score),
        "sector": sector,
        "category": (
            "Strong"
            if base_score >= 80
            else "Moderate"
            if base_score >= 65
            else "Weak"
        ),
        "source": "BizFiz sector baseline",
    }


# ============================================================
# 4. RELATIVE PROSPERITY
# ============================================================

def relative_prosperity(
    state: str,
    district: str
) -> Dict[str, Any]:
    """
    Calculate relative district prosperity from PhonePe
    transaction activity and user adoption.
    """

    tx = pulse_service.get_district_transaction_stats(
        state,
        district
    )

    users = pulse_service.get_district_user_stats(
        state,
        district
    )

    if tx.get("found"):
        total_districts = max(
            _safe_int(tx.get("totalDistricts"), 1),
            1
        )

        rank = max(
            _safe_int(tx.get("districtRank"), total_districts),
            1
        )

        rank_score = 100 - (
            ((rank - 1) / total_districts) * 100
        )

    else:
        rank_score = 65.0

    if users.get("found"):
        registered_users = _safe_float(
            users.get("registeredUsers")
        )

        app_opens = _safe_float(
            users.get("appOpens")
        )

        if registered_users > 0:
            engagement = app_opens / registered_users
        else:
            engagement = 0

        engagement_score = _clamp(
            engagement * 100
        )

        if engagement_score == 0:
            engagement_score = 60.0
    else:
        engagement_score = 60.0

    rating = (
        (rank_score * 0.70) +
        (engagement_score * 0.30)
    )

    return {
        "name": "Location Strength",
        "rating": _clamp(rating),
        "score": _clamp(rating),
        "state": state,
        "district": district,
        "districtRank": tx.get("districtRank", 0),
        "totalDistricts": tx.get("totalDistricts", 0),
        "source": "PhonePe Pulse",
    }


# ============================================================
# 5. EASE OF BUSINESS
# ============================================================

STATE_EASE_SCORES = {
    "andhra pradesh": 72,
    "arunachal pradesh": 55,
    "assam": 64,
    "bihar": 58,
    "chhattisgarh": 67,
    "goa": 82,
    "gujarat": 88,
    "haryana": 84,
    "himachal pradesh": 74,
    "jharkhand": 62,
    "karnataka": 86,
    "kerala": 78,
    "madhya pradesh": 75,
    "maharashtra": 87,
    "manipur": 55,
    "meghalaya": 58,
    "mizoram": 55,
    "nagaland": 56,
    "odisha": 72,
    "punjab": 78,
    "rajasthan": 75,
    "sikkim": 65,
    "tamil nadu": 85,
    "telangana": 84,
    "tripura": 56,
    "uttar pradesh": 70,
    "uttarakhand": 73,
    "west bengal": 68,
    "delhi": 88,
}


def ease_of_business(
    pincode: str,
    state: str
) -> Dict[str, Any]:
    """
    Estimate ease of doing business.

    Uses a state-level baseline with a neutral PIN adjustment.
    """

    normalized_state = _normalize_text(state)

    state_score = STATE_EASE_SCORES.get(
        normalized_state,
        68
    )

    # Valid Indian PIN codes generally begin 1-8.
    pincode_text = str(pincode or "").strip()

    if len(pincode_text) == 6 and pincode_text.isdigit():
        pincode_score = 5.0
    else:
        pincode_score = -5.0

    score = _clamp(
        state_score + pincode_score
    )

    return {
        "name": "Ease of Business Score",
        "rating": score,
        "score": score,
        "state": state,
        "pincode": pincode,
        "source": "State-level business environment proxy",
        "message": (
            "State-level proxy used because a reliable district-level "
            "ease-of-business dataset is not available."
        ),
    }