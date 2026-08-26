import os
import json
from functools import lru_cache
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PULSE_DATA_DIR = os.path.join(BASE_DIR, "pulsedata")

@lru_cache(maxsize=512)
def _read_json_safe(filepath: str) -> Optional[Dict[str, Any]]:
    """Safely load JSON file from disk with caching."""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def normalize_state_name(state: str) -> str:
    """Normalize state name to match PhonePe Pulse folder structure."""
    if not state:
        return ""
    state_norm = state.strip().lower().replace(" ", "-").replace("&", "-")
    # Common variations
    replacements = {
        "gujrat": "gujarat",
        "orissa": "odisha",
        "pondicherry": "puducherry",
        "delhi-ncr": "delhi",
        "bangalore": "karnataka",
        "bengaluru": "karnataka",
    }
    return replacements.get(state_norm, state_norm)

def normalize_district_name(district: str) -> str:
    """Normalize district name for robust matching against hover dataset."""
    if not district:
        return ""
    d = district.strip().lower()
    d = d.replace(" district", "").replace(" urban", "").replace(" rural", "").strip()
    return d

def get_available_states_and_districts() -> Dict[str, List[str]]:
    """Scan the actual PhonePe Pulse dataset and return map of state -> districts."""
    states_map: Dict[str, List[str]] = {}
    map_user_state_dir = os.path.join(PULSE_DATA_DIR, "map", "user", "hover", "country", "india", "state")
    
    if not os.path.exists(map_user_state_dir):
        return {}

    for state_folder in sorted(os.listdir(map_user_state_dir)):
        state_path = os.path.join(map_user_state_dir, state_folder)
        if not os.path.isdir(state_path):
            continue
        
        # Look for latest data file, e.g. 2021/3.json or 2021/4.json
        districts = []
        for year in ["2021", "2020", "2019"]:
            year_path = os.path.join(state_path, year)
            if os.path.isdir(year_path):
                for q in ["4.json", "3.json", "2.json", "1.json"]:
                    q_file = os.path.join(year_path, q)
                    data = _read_json_safe(q_file)
                    if data and "data" in data and "hoverData" in data["data"]:
                        for d_key in data["data"]["hoverData"].keys():
                            clean_d = d_key.replace(" district", "").strip().title()
                            if clean_d and clean_d not in districts:
                                districts.append(clean_d)
                        break
            if districts:
                break
        
        display_state_name = state_folder.replace("-", " ").title()
        states_map[display_state_name] = sorted(districts)

    return states_map

def get_district_user_stats(state: str, district: str) -> Dict[str, Any]:
    """Retrieve district user adoption stats from PhonePe Pulse."""
    state_key = normalize_state_name(state)
    dist_norm = normalize_district_name(district)
    
    file_path = os.path.join(PULSE_DATA_DIR, "map", "user", "hover", "country", "india", "state", state_key, "2021", "3.json")
    data = _read_json_safe(file_path)
    
    if not data or "data" not in data or "hoverData" not in data["data"]:
        return {
            "registeredUsers": 0,
            "appOpens": 0,
            "engagementRatio": 0.0,
            "found": False
        }
    
    hover_data = data["data"]["hoverData"]
    for k, v in hover_data.items():
        if dist_norm in k.lower():
            users = v.get("registeredUsers", 0)
            opens = v.get("appOpens", 0)
            ratio = round(opens / max(users, 1), 2)
            return {
                "districtKey": k,
                "registeredUsers": users,
                "appOpens": opens,
                "engagementRatio": ratio,
                "found": True
            }
            
    return {
        "registeredUsers": 0,
        "appOpens": 0,
        "engagementRatio": 0.0,
        "found": False
    }

def get_district_transaction_stats(state: str, district: str) -> Dict[str, Any]:
    """Retrieve district transaction volume & value from PhonePe Pulse."""
    state_key = normalize_state_name(state)
    dist_norm = normalize_district_name(district)
    
    file_path = os.path.join(PULSE_DATA_DIR, "map", "transaction", "hover", "country", "india", "state", state_key, "2021", "4.json")
    data = _read_json_safe(file_path)
    
    if not data or "data" not in data or "hoverdatalist" not in data["data"]:
        return {
            "transactionCount": 0,
            "transactionAmount": 0.0,
            "districtRank": 0,
            "totalDistricts": 0,
            "found": False
        }
    
    hover_list = data["data"]["hoverdatalist"]
    sorted_list = []
    
    for item in hover_list:
        name = item.get("name", "")
        metric = item.get("metric", [{}])[0]
        cnt = metric.get("count", 0)
        amt = metric.get("amount", 0.0)
        sorted_list.append({
            "name": name,
            "count": cnt,
            "amount": amt
        })
        
    sorted_list.sort(key=lambda x: x["amount"], reverse=True)
    total_districts = len(sorted_list)
    
    for idx, item in enumerate(sorted_list):
        if dist_norm in item["name"].lower():
            return {
                "transactionCount": item["count"],
                "transactionAmount": item["amount"],
                "districtRank": idx + 1,
                "totalDistricts": total_districts,
                "found": True
            }
            
    return {
        "transactionCount": 0,
        "transactionAmount": 0.0,
        "districtRank": 0,
        "totalDistricts": total_districts,
        "found": False
    }

def get_state_sector_trends(state: str, sector: str) -> Dict[str, Any]:
    """Analyze transaction trend for state and sector using aggregated transaction datasets."""
    state_key = normalize_state_name(state)
    
    # Check years 2019 to 2021 Q4 for growth comparison
    history = []
    for year in ["2019", "2020", "2021"]:
        file_path = os.path.join(PULSE_DATA_DIR, "aggregated", "transaction", "country", "india", "state", state_key, year, "4.json")
        data = _read_json_safe(file_path)
        if data and "data" in data and "transactionData" in data["data"]:
            tx_data = data["data"]["transactionData"]
            merchant_tx = next((item for item in tx_data if "merchant" in item.get("name", "").lower()), None)
            total_amt = sum(item.get("paymentInstruments", [{}])[0].get("amount", 0.0) for item in tx_data)
            merchant_amt = merchant_tx.get("paymentInstruments", [{}])[0].get("amount", 0.0) if merchant_tx else 0.0
            
            history.append({
                "year": int(year),
                "totalAmount": total_amt,
                "merchantAmount": merchant_amt
            })
            
    growth_rate = 15.0 # default moderate growth
    if len(history) >= 2:
        prev = history[0]["merchantAmount"]
        curr = history[-1]["merchantAmount"]
        if prev > 0:
            growth_rate = round(((curr - prev) / prev) * 100 / max(len(history) - 1, 1), 2)
            
    trend_category = "Growing" if growth_rate > 10 else ("Stable" if growth_rate >= 0 else "Declining")
    
    return {
        "state": state,
        "sector": sector,
        "historicalMerchantVolume": history,
        "annualMerchantGrowthRate": growth_rate,
        "trendCategory": trend_category
    }

def get_national_pulse_trends() -> List[Dict[str, Any]]:
    """Retrieve national aggregate quarterly time-series directly from PhonePe Pulse datasets."""
    trends = []
    for year in ["2019", "2020", "2021"]:
        for q in [1, 2, 3, 4]:
            q_str = f"{q}.json"
            file_path = os.path.join(PULSE_DATA_DIR, "aggregated", "transaction", "country", "india", year, q_str)
            data = _read_json_safe(file_path)
            if data and "data" in data and "transactionData" in data["data"]:
                tx_data = data["data"]["transactionData"]
                total_cnt = sum(item.get("paymentInstruments", [{}])[0].get("count", 0) for item in tx_data)
                total_amt = sum(item.get("paymentInstruments", [{}])[0].get("amount", 0.0) for item in tx_data)
                merchant_item = next((item for item in tx_data if "merchant" in item.get("name", "").lower()), None)
                merchant_cnt = merchant_item.get("paymentInstruments", [{}])[0].get("count", 0) if merchant_item else 0
                
                trends.append({
                    "name": f"{year} Q{q}",
                    "transactions": total_cnt,
                    "amount": round(total_amt, 2),
                    "merchantTransactions": merchant_cnt
                })
    return trends
