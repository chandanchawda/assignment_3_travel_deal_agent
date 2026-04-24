"""
Travel Deal Investigator — 3 Custom Tool Functions
Each tool is a pure Python function that the agent calls during its reasoning loop.
"""

import json
import re
import random


def analyze_deal(deal_text: str) -> str:
    """
    Parses travel deal text and extracts structured data:
    destination, origin, price, dates, airline/hotel, deal type.
    """
    result = {
        "raw_text": deal_text[:500],
        "extracted": {}
    }

    # Extract price
    price_match = re.search(r'[\$€£₹][\d,]+\.?\d*', deal_text)
    if not price_match:
        price_match = re.search(r'([\d,]+\.?\d*)\s*(USD|EUR|GBP|INR|dollars?)', deal_text, re.IGNORECASE)
    if price_match:
        result["extracted"]["price"] = price_match.group(0)

    # Extract route (from X to Y)
    route_match = re.search(
        r'from\s+([A-Za-z\s,]+?)\s+to\s+([A-Za-z\s,]+?)[\s,.\d$€£]',
        deal_text, re.IGNORECASE
    )
    if route_match:
        result["extracted"]["origin"] = route_match.group(1).strip()
        result["extracted"]["destination"] = route_match.group(2).strip()

    # Extract dates
    date_matches = re.findall(
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s*\d{0,2},?\s*\d{4}',
        deal_text, re.IGNORECASE
    )
    if date_matches:
        result["extracted"]["dates"] = date_matches

    # Extract airline
    airlines = [
        "Delta", "United", "American", "Southwest", "JetBlue", "Spirit",
        "Alaska", "Emirates", "Qatar", "Lufthansa", "British Airways",
        "Air India", "IndiGo", "Singapore Airlines", "ANA", "JAL",
        "Ryanair", "EasyJet", "Air France", "KLM", "Turkish Airlines",
        "Etihad", "Cathay Pacific", "Thai Airways", "Vistara"
    ]
    for airline in airlines:
        if airline.lower() in deal_text.lower():
            result["extracted"]["airline"] = airline
            break

    # Detect deal type
    text_lower = deal_text.lower()
    if any(w in text_lower for w in ["hotel", "resort", "stay", "accommodation", "airbnb"]):
        result["extracted"]["deal_type"] = "Hotel/Accommodation"
    elif any(w in text_lower for w in ["flight", "round trip", "one way", "airline", "roundtrip"]):
        result["extracted"]["deal_type"] = "Flight"
    elif any(w in text_lower for w in ["package", "bundle", "all inclusive", "flight + hotel"]):
        result["extracted"]["deal_type"] = "Travel Package"
    else:
        result["extracted"]["deal_type"] = "General Travel Deal"

    return json.dumps(result, indent=2)


def check_price_history(destination: str, origin: str = "", deal_type: str = "") -> str:
    """
    Checks historical price data for a travel route.
    Returns lowest, average, highest prices and a 6-month trend.
    In production, this would call a real flight/hotel price API.
    """
    # Realistic price ranges by destination
    price_ranges = {
        "tokyo":     {"low": 550, "avg": 850,  "high": 1400},
        "paris":     {"low": 380, "avg": 650,  "high": 1100},
        "london":    {"low": 350, "avg": 600,  "high": 950},
        "bali":      {"low": 600, "avg": 900,  "high": 1500},
        "dubai":     {"low": 450, "avg": 750,  "high": 1200},
        "new york":  {"low": 200, "avg": 400,  "high": 700},
        "goa":       {"low": 50,  "avg": 120,  "high": 250},
        "bangkok":   {"low": 400, "avg": 650,  "high": 1000},
        "rome":      {"low": 400, "avg": 700,  "high": 1150},
        "cancun":    {"low": 250, "avg": 450,  "high": 750},
        "singapore": {"low": 400, "avg": 700,  "high": 1100},
        "maldives":  {"low": 700, "avg": 1100, "high": 1800},
        "mumbai":    {"low": 100, "avg": 250,  "high": 500},
    }

    # Find matching destination
    dest_key = "default"
    for key in price_ranges:
        if key in destination.lower():
            dest_key = key
            break

    if dest_key == "default":
        prices = {"low": 300, "avg": 550, "high": 900}
    else:
        prices = price_ranges[dest_key]

    # Generate 6-month price trend
    months = ["Nov 2025", "Dec 2025", "Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"]
    trend = []
    for month in months:
        variation = random.uniform(-0.15, 0.15)
        month_price = round(prices["avg"] * (1 + variation))
        trend.append({"month": month, "avg_price": f"${month_price}"})

    result = {
        "route": f"{origin or 'Various'} → {destination}",
        "deal_type": deal_type or "Flight",
        "price_range": {
            "lowest_seen": f"${prices['low']}",
            "average": f"${prices['avg']}",
            "highest_seen": f"${prices['high']}"
        },
        "six_month_trend": trend,
        "best_booking_window": "6-8 weeks before travel for best prices",
        "data_source": "Aggregated from historical fare data"
    }

    return json.dumps(result, indent=2)


def get_destination_info(destination: str) -> str:
    """
    Returns travel information: visa requirements, weather by season,
    safety rating, travel tips, and average daily budget.
    """
    destination_db = {
        "tokyo": {
            "country": "Japan",
            "visa": "Visa-free for 68 countries (up to 90 days). US, UK, EU citizens exempt. Indian citizens need e-Visa.",
            "weather": {"spring": "12-20°C", "summer": "25-35°C", "autumn": "15-25°C", "winter": "2-12°C"},
            "safety": "Very Safe — Japan ranks among the safest countries globally.",
            "tips": [
                "Get a Suica/Pasmo card for transit",
                "Many places are cash-only",
                "Visit during cherry blossom season (late March-April)",
                "JR Pass saves money on bullet trains"
            ],
            "avg_daily_budget": "$100-150/day mid-range"
        },
        "paris": {
            "country": "France",
            "visa": "Schengen visa rules. Visa-free for US/UK/AU/CA up to 90 days. Indian citizens need Schengen visa.",
            "weather": {"spring": "8-18°C", "summer": "15-28°C", "autumn": "8-18°C", "winter": "2-8°C"},
            "safety": "Generally Safe — beware of pickpockets at tourist spots and metro.",
            "tips": [
                "Paris Museum Pass saves money on attractions",
                "Metro is the fastest transport",
                "Book Eiffel Tower tickets well in advance",
                "Many restaurants close between lunch and dinner service"
            ],
            "avg_daily_budget": "$120-180/day mid-range"
        },
        "bali": {
            "country": "Indonesia",
            "visa": "Visa on arrival for many nationalities ($35 USD, 30 days).",
            "weather": {"dry_season": "Apr-Oct, 27-30°C", "wet_season": "Nov-Mar, 27-30°C with rain"},
            "safety": "Safe for tourists — watch for bag snatching on motorbikes.",
            "tips": [
                "Rent a scooter for flexibility",
                "Negotiate taxi fares in advance",
                "Visit Ubud for culture, Seminyak for beaches",
                "Avoid drinking tap water"
            ],
            "avg_daily_budget": "$40-80/day mid-range"
        },
        "london": {
            "country": "United Kingdom",
            "visa": "Visa-free for US/EU/AU/CA up to 6 months. Indian citizens need visa.",
            "weather": {"spring": "8-15°C", "summer": "14-25°C", "autumn": "8-15°C", "winter": "2-8°C"},
            "safety": "Safe — standard city precautions apply.",
            "tips": [
                "Get an Oyster card for transport",
                "Many world-class museums are free",
                "Book West End shows last-minute for discounts",
                "Carry an umbrella always"
            ],
            "avg_daily_budget": "$130-200/day mid-range"
        },
        "dubai": {
            "country": "UAE",
            "visa": "Visa-free or visa on arrival for many countries (30-90 days).",
            "weather": {"winter": "18-26°C (best time to visit)", "summer": "35-45°C (extreme heat)"},
            "safety": "Very Safe — strict laws, very low crime rate.",
            "tips": [
                "Visit Oct-Mar to avoid extreme heat",
                "Friday brunch is a cultural institution",
                "Dress modestly in non-resort areas",
                "The metro is clean and efficient"
            ],
            "avg_daily_budget": "$100-200/day mid-range"
        },
        "goa": {
            "country": "India",
            "visa": "Indian citizens: no visa needed. Others: e-Visa available for most nationalities.",
            "weather": {"peak_season": "Nov-Feb, 25-32°C, dry", "monsoon": "Jun-Sep, 25-30°C, heavy rain"},
            "safety": "Generally Safe — avoid isolated beaches at night.",
            "tips": [
                "North Goa for parties, South Goa for peace",
                "Rent a scooter for beach hopping",
                "Bargain at flea markets",
                "November-February is the best time to visit"
            ],
            "avg_daily_budget": "$30-60/day mid-range"
        },
        "singapore": {
            "country": "Singapore",
            "visa": "Visa-free for most nationalities (30-90 days). Indian citizens need visa but e-Visa available.",
            "weather": {"year_round": "27-33°C, tropical, frequent rain showers"},
            "safety": "Extremely Safe — one of the safest cities in the world.",
            "tips": [
                "Eat at hawker centres for amazing cheap food",
                "MRT is excellent for getting around",
                "Gardens by the Bay is a must-see",
                "Chewing gum is banned — don't bring it in"
            ],
            "avg_daily_budget": "$80-150/day mid-range"
        },
    }

    # Find matching destination
    dest_key = None
    for key in destination_db:
        if key in destination.lower():
            dest_key = key
            break

    if dest_key:
        info = destination_db[dest_key]
    else:
        info = {
            "country": "Unknown",
            "visa": "Check your country's visa requirements at the destination's embassy website.",
            "weather": {"note": "Look up seasonal weather for your specific travel dates."},
            "safety": "Check latest travel advisories on your government's travel website.",
            "tips": [
                "Get travel insurance",
                "Register with your embassy",
                "Keep digital copies of all documents",
                "Research local customs and laws"
            ],
            "avg_daily_budget": "Varies by destination"
        }

    info["destination_query"] = destination
    return json.dumps(info, indent=2)


TOOL_FUNCTIONS = {
    "analyze_deal": lambda args: analyze_deal(args.get("deal_text", "")),
    "check_price_history": lambda args: check_price_history(
        args.get("destination", ""),
        args.get("origin", ""),
        args.get("deal_type", "")
    ),
    "get_destination_info": lambda args: get_destination_info(
        args.get("destination", "")
    ),
}
