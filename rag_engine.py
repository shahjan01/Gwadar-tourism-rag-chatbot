import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Get API key — works both locally and on Streamlit Cloud
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    try:
        import streamlit as st
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass
if not api_key:
    raise RuntimeError("Missing GROQ_API_KEY. Add it to .env or Streamlit Secrets.")

client = Groq(api_key=api_key)

DATA_DIR = Path(__file__).parent / "data"

def load_all_data():
    data = {}
    for f in DATA_DIR.glob("*.json"):
        with open(f, encoding="utf-8") as fh:
            try:
                content = json.load(fh)
            except json.JSONDecodeError:
                continue
        key = f.stem
        # strip number prefix e.g. "1781461241233_gwadar_places" -> "gwadar_places"
        if "_gwadar_" in key:
            key = "gwadar_" + key.split("_gwadar_")[1]
        data[key] = content
    return data

ALL_DATA = load_all_data()

# gwadar_places.json is a LIST directly
raw_places = ALL_DATA.get("gwadar_places", [])
PLACES = raw_places if isinstance(raw_places, list) else raw_places.get("places", [])

# gwadar_restaurants.json has a "restaurants" key
raw_restaurants = ALL_DATA.get("gwadar_restaurants", {})
RESTAURANTS = raw_restaurants.get("restaurants", []) if isinstance(raw_restaurants, dict) else raw_restaurants

# gwadar_hotels.json has a "hotels" key
raw_hotels = ALL_DATA.get("gwadar_hotels", {})
HOTELS = raw_hotels.get("hotels", []) if isinstance(raw_hotels, dict) else raw_hotels

# transport and emergency are dicts
TRANSPORT = ALL_DATA.get("gwadar_transport_services", {})
EMERGENCY = ALL_DATA.get("gwadar_emergency_numbers", {})

def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

def detect_intent(user_msg: str) -> str:
    msg = user_msg.lower()
    if any(w in msg for w in ["hotel", "hotels", "stay", "accommodation", "resort",
                               "guest house", "guesthouse", "inn", "lodge", "room",
                               "lodging", "sea view hotel", "best hotel", "luxury hotel",
                               "budget hotel", "cheap hotel", "5 star"]):
        return "hotel"
    if any(w in msg for w in ["place", "places", "beach", "visit", "see", "view", "island",
                               "park", "spot", "tourist", "attraction", "beautiful",
                               "nature", "koh", "hammerhead", "marine", "jiwani",
                               "ormara", "pasni", "hingol", "astola", "best places",
                               "top places", "where to go", "what to see"]):
        return "places"
    if any(w in msg for w in ["bus", "car", "rent", "transport", "ticket", "travel",
                               "coach", "drive", "hire", "vehicle", "suv", "van",
                               "coaster", "al mumtaz", "fare", "karachi to gwadar",
                               "taxi", "cab", "ride", "how to reach", "how to go"]):
        return "transport"
    if any(w in msg for w in ["emergency", "police", "ambulance", "hospital", "fire",
                               "accident", "help", "doctor", "injured", "rescue",
                               "blood", "edhi", "1122", "urgent", "danger", "hurt",
                               "safe", "safety", "number"]):
        return "emergency"
    if any(w in msg for w in ["restaurant", "food", "eat", "cafe", "dine", "lunch",
                               "dinner", "breakfast", "biryani", "bbq", "karahi",
                               "seafood", "hungry", "meal", "dish", "cuisine"]):
        return "restaurant"
    return "general"

def search_places(query: str) -> list:
    q = query.lower()
    results = []
    for p in PLACES:
        score = 0
        name = p.get("name", "").lower()
        desc = p.get("description", "").lower()
        for token in q.split():
            if token in name: score += 4
            if token in desc: score += 2
        if "beach" in q and "beach" in desc: score += 3
        if "park" in q and "park" in desc: score += 3
        if "view" in q and "view" in name: score += 3
        if score > 0:
            results.append((score, p))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:5]] if results else PLACES[:5]

def search_hotels(query: str = None) -> list:
    if not HOTELS:
        return []
    if not query:
        return sorted(HOTELS, key=lambda h: h.get("rating") or 0, reverse=True)[:5]

    q = query.lower()
    price_filter = None
    if any(w in q for w in ["cheap", "budget", "affordable", "low"]):
        price_filter = "low"
    elif any(w in q for w in ["luxury", "5 star", "premium", "expensive", "high"]):
        price_filter = "high"
    elif any(w in q for w in ["mid", "medium", "moderate"]):
        price_filter = "medium"

    results = []
    for h in HOTELS:
        pr = (h.get("price_range") or "").lower()
        if price_filter == "low" and "low" not in pr:
            continue
        if price_filter == "high" and "high" not in pr:
            continue
        if price_filter == "medium" and "medium" not in pr:
            continue

        score = float(h.get("rating") or 0)
        name = h.get("name", "").lower()
        desc = h.get("description", "").lower()
        loc  = h.get("location", "").lower()
        for token in q.split():
            if token in name: score += 3
            if token in desc: score += 1
            if token in loc:  score += 1
        results.append((score, h))

    if not results:
        return HOTELS[:5]
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:6]]

def search_buses() -> list:
    return TRANSPORT.get("buses", [])

def search_cars(budget: int = None) -> list:
    cars = TRANSPORT.get("car_rentals", [])
    if not budget:
        return cars
    filtered = []
    for car in cars:
        for v in car.get("vehicles_available", []):
            nums = re.findall(r'\d+', str(v.get("price_per_day", "")).replace(",", ""))
            if nums and int(nums[0]) <= budget:
                filtered.append(car)
                break
    return filtered if filtered else cars

def get_emergency_numbers(situation: str = None) -> dict:
    numbers    = EMERGENCY.get("national_emergency_numbers", {}).get("emergency_numbers", [])
    hospitals  = EMERGENCY.get("hospitals_and_medical_facilities", {}).get("major_hospitals", [])
    procedures = EMERGENCY.get("emergency_response_procedures", {}).get("what_to_do_in_emergency", [])
    if situation:
        s = situation.lower()
        relevant = [p for p in procedures
                    if any(w in p.get("situation", "").lower() for w in s.split())]
        return {"numbers": numbers, "hospitals": hospitals, "relevant_procedure": relevant}
    return {"numbers": numbers, "hospitals": hospitals, "relevant_procedure": []}

def search_restaurants(cuisine: str = None) -> list:
    if not cuisine:
        return RESTAURANTS
    q = cuisine.lower()
    results = [r for r in RESTAURANTS
               if q in r.get("cuisine_type", "").lower()
               or q in r.get("description", "").lower()
               or q in " ".join(r.get("best_dishes", [])).lower()]
    return results if results else RESTAURANTS

def build_context(intent: str, user_msg: str) -> tuple:
    context_data = {}
    msg_lower = user_msg.lower()

    if intent == "places":
        context_data = {"places": search_places(user_msg)}

    elif intent == "hotel":
        context_data = {"hotels": search_hotels(user_msg)}

    elif intent == "transport":
        if any(w in msg_lower for w in ["bus", "coach", "ticket"]):
            context_data = {"buses": search_buses(),
                            "general_info": TRANSPORT.get("general_travel_information", {})}
        else:
            budget = None
            nums = re.findall(r'\d{4,}', user_msg.replace(",", ""))
            if nums:
                try: budget = int(nums[0])
                except ValueError: pass
            context_data = {
                "car_rentals":  search_cars(budget),
                "pricing":      TRANSPORT.get("pricing_comparison", {}),
                "general_info": TRANSPORT.get("general_travel_information", {})
            }

    elif intent == "emergency":
        context_data = get_emergency_numbers(user_msg)

    elif intent == "restaurant":
        cuisine = None
        for word in ["bbq", "fast food", "pakistani", "afghani", "biryani",
                     "karahi", "seafood", "local", "cafe"]:
            if word in msg_lower:
                cuisine = word
                break
        context_data = {"restaurants": search_restaurants(cuisine)}

    return intent, context_data

def format_answer(intent: str, context_data: dict, user_msg: str) -> dict:
    context_json = json.dumps(context_data, ensure_ascii=False, indent=2)

    instructions = {
        "places": """You are a friendly Gwadar tour guide.
- List best matching places with name and short description
- Include the Google Maps link from location_url for each place
- Be enthusiastic and welcoming""",

        "hotel": """You are a Gwadar hotel assistant.
- List hotels with: name, type, price range, rating, location, phone
- Group as Budget / Mid-Range / Luxury if multiple types shown
- Show verified phone numbers prominently (phone_verified: true)
- Mention key amenities""",

        "transport": """You are a Gwadar transport assistant.
- For buses: ticket price, timings, booking method
- For cars: vehicle types, price per day in PKR, contact
- Mention verified contacts only""",

        "emergency": """You are a Gwadar emergency assistant. Be calm and clear.
- Show numbers FIRST: Police=15, Ambulance=1122, Fire=16, Edhi=115
- List nearest hospitals
- Add step-by-step procedure if relevant""",

        "restaurant": """You are a Gwadar food guide.
- List restaurants with cuisine, address, phone, popular dishes
- Note Gwadar is famous for fresh seafood""",

        "general": """You are a helpful Gwadar city assistant.
- Answer from your knowledge about Gwadar, Pakistan
- Gwadar is a CPEC port city in Balochistan with beautiful beaches"""
    }

    prompt = f"""{instructions.get(intent, instructions['general'])}

GWADAR DATABASE:
{context_json}

Tourist question: "{user_msg}"

Give a clear friendly answer using ONLY the data above.
Do NOT make up phone numbers or details not in the data.
Use bullet points where helpful.

End with exactly 3 follow-up suggestions in this format:
SUGGESTIONS:
1. ...
2. ...
3. ..."""

    full_text = call_llm(prompt)

    suggestions = []
    answer = full_text
    if "SUGGESTIONS:" in full_text:
        parts = full_text.split("SUGGESTIONS:")
        answer = parts[0].strip()
        for line in parts[1].strip().split("\n"):
            line = re.sub(r'^[\d\.\-\*\s]+', '', line).strip()
            if line:
                suggestions.append(line)
        suggestions = suggestions[:3]

    defaults = {
        "places":     ["Show me beaches in Gwadar", "What is Koh-e-Batil viewpoint?", "How to reach Hingol National Park?"],
        "hotel":      ["Show budget hotels in Gwadar", "Which is the best luxury hotel?", "Hotels near the beach?"],
        "transport":  ["Bus ticket price to Gwadar?", "Best car for family travel?", "How long is Karachi to Gwadar?"],
        "emergency":  ["Nearest hospital in Gwadar?", "Documents needed at checkpoints?", "Is Gwadar safe?"],
        "restaurant": ["Seafood restaurants in Gwadar?", "Are there cafes in Gwadar?", "Local Balochi food?"],
        "general":    ["Top places in Gwadar?", "Best hotels in Gwadar?", "How to travel to Gwadar?"]
    }
    if len(suggestions) < 3:
        suggestions = defaults.get(intent, defaults["general"])

    places_with_maps = []
    if intent == "places":
        places_with_maps = [
            {"name": p.get("name",""), "map_url": p.get("location_url",""), "description": p.get("description","")}
            for p in context_data.get("places", [])
        ]

    emergency_numbers = []
    if intent == "emergency":
        for n in context_data.get("numbers", []):
            emergency_numbers.append({
                "service":        n.get("service", ""),
                "number":         n.get("numbers", [""])[0],
                "available_24_7": n.get("available_24_7", False)
            })

    return {
        "answer":            answer,
        "suggestions":       suggestions,
        "intent":            intent,
        "places_with_maps":  places_with_maps,
        "emergency_numbers": emergency_numbers
    }

def chat(user_msg: str) -> dict:
    intent, context_data = build_context(detect_intent(user_msg), user_msg)
    return format_answer(intent, context_data, user_msg)
