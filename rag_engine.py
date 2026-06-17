import json
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    try:
        import streamlit as st
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
if not api_key:
    raise RuntimeError("Missing GROQ_API_KEY in .env file. Get a free key at console.groq.com")

client = Groq(api_key=api_key)

DATA_DIR = Path(__file__).parent / "data"

def load_all_data():
    data = {}
    for f in DATA_DIR.glob("*.json"):
        with open(f, encoding="utf-8") as fh:
            try:
                data[f.stem] = json.load(fh)
            except json.JSONDecodeError:
                data[f.stem] = []
    return data

ALL_DATA = load_all_data()

def _parse_list(root, key=None):
    if isinstance(root, dict):
        return root.get(key, []) if key else []
    if isinstance(root, list):
        return root
    return []

def _parse_price_field(value):
    if isinstance(value, (int, float)):
        return int(value), int(value)
    if not value:
        return None, None
    nums = re.findall(r"\d+", str(value))
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return int(nums[0]), int(nums[0])
    return None, None


def _parse_price_range_text(text: str):
    if not text:
        return None, None
    text = text.lower()
    between = re.search(r"between\s+(\d+)\s*(?:and|\-|to)\s*(\d+)", text)
    if between:
        return int(between.group(1)), int(between.group(2))
    under = re.search(r"(?:under|below|less than|up to)\s+(\d+)", text)
    if under:
        return None, int(under.group(1))
    above = re.search(r"(?:over|above|more than)\s+(\d+)", text)
    if above:
        return int(above.group(1)), None
    dash = re.search(r"(\d+)\s*-\s*(\d+)", text)
    if dash:
        return int(dash.group(1)), int(dash.group(2))
    if any(word in text for word in ["pkr", "rupee", "rs", "pakistani rupees"]):
        single = re.search(r"(\d{3,})", text)
        if single:
            return None, int(single.group(1))
    return None, None


def _price_matches(price_value, min_price, max_price):
    low, high = _parse_price_field(price_value)
    if low is None and high is None:
        return False
    if min_price is not None and high is not None and high < min_price:
        return False
    if max_price is not None and low is not None and low > max_price:
        return False
    return True


def build_suggestion_fallback(intent: str, user_msg: str) -> list:
    msg = user_msg.lower()
    if intent == "hotel":
        suggestions = [
            "Show more hotels in Gwadar",
            "Find sea view hotels in Gwadar",
            "Which hotel is best for families?"
        ]
        if any(w in msg for w in ["cheap", "budget", "under", "below", "affordable"]):
            suggestions[0] = "Show hotels under your budget"
            suggestions[1] = "Find budget-friendly hotels with good ratings"
        if any(w in msg for w in ["rating", "best", "top"]):
            suggestions[2] = "Show top-rated hotels in Gwadar"
        return suggestions
    if intent == "restaurant":
        suggestions = [
            "Show more restaurants in Gwadar",
            "Find top-rated seafood restaurants",
            "Which restaurant is best for local food?"
        ]
        if any(w in msg for w in ["cheap", "budget", "under", "below", "affordable"]):
            suggestions[0] = "Show restaurants under your budget"
        if any(w in msg for w in ["rating", "best", "top", "popular"]):
            suggestions[1] = "Show the best-rated restaurants"
        return suggestions
    if intent == "places":
        suggestions = [
            "What is the best beach in Gwadar?",
            "Which place is best for families?",
            "Where can I see the best sunset?"
        ]
        if any(w in msg for w in ["family", "kids", "children"]):
            suggestions[1] = "Which places are family-friendly in Gwadar?"
        if any(w in msg for w in ["sunset", "view", "picture", "photography"]):
            suggestions[2] = "Where is the best sunset spot in Gwadar?"
        return suggestions
    if intent == "transport":
        return [
            "Find bus ticket prices to Gwadar",
            "Show car rentals by budget",
            "What is the travel time from Karachi to Gwadar?"
        ]
    if intent == "emergency":
        return [
            "What is the emergency ambulance number?",
            "Where is the nearest hospital in Gwadar?",
            "How do I contact the police in Gwadar?"
        ]
    return [
        "What are the top places to visit in Gwadar?",
        "How do I travel to Gwadar?",
        "Is Gwadar safe for tourists?"
    ]


PLACES = _parse_list(ALL_DATA.get("gwadar_places", {}), "places")
TRANSPORT = ALL_DATA.get("gwadar_transport_services", {}) if isinstance(ALL_DATA.get("gwadar_transport_services"), dict) else {}
EMERGENCY = ALL_DATA.get("gwadar_emergency_numbers", {}) if isinstance(ALL_DATA.get("gwadar_emergency_numbers"), dict) else {}
RESTAURANTS = _parse_list(ALL_DATA.get("gwadar_restaurants", {}), "restaurants")
HOTELS = _parse_list(ALL_DATA.get("gwadar_hotels", {}), "hotels")

def call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content.strip()

# keyword-only intent — zero API calls for classification
def detect_intent(user_msg: str) -> str:
    msg = user_msg.lower()
    if any(w in msg for w in ["hotel", "hotels", "stay", "accommodation", "resort",
                               "guest house", "guesthouse", "inn", "motel", "room",
                               "suite", "lodging", "staycation", "sea view", "best hotel"]):
        return "hotel"
    if any(w in msg for w in ["place", "places", "beach", "visit", "see", "view", "island",
                               "park", "where", "spot", "tourist", "attraction",
                               "beautiful", "nature", "koh", "hammerhead", "marine",
                               "jiwani", "ormara", "pasni", "hingol", "astola"]):
        return "places"
    if any(w in msg for w in ["bus", "car", "rent", "transport", "ticket", "travel",
                               "coach", "drive", "hire", "vehicle", "suv", "van",
                               "coaster", "al mumtaz", "fare", "how much", "budget",
                               "karachi to gwadar", "price", "taxi", "cab", "ride"]):
        return "transport"
    if any(w in msg for w in ["emergency", "police", "ambulance", "hospital", "fire",
                               "accident", "help", "doctor", "injured", "rescue",
                               "blood", "edhi", "1122", "urgent", "danger", "hurt"]):
        return "emergency"
    if any(w in msg for w in ["restaurant", "restaurants", "food", "eat", "cafe", "dine", "lunch",
                               "dinner", "breakfast", "biryani", "bbq", "karahi",
                               "seafood", "hungry", "meal", "dish", "cuisine"]):
        return "restaurant"
    return "general"

def search_places(query: str) -> list:
    q = query.lower()
    results = []
    preference_bonus = 0
    if any(w in q for w in ["family", "kids", "children", "family-friendly"]):
        preference_bonus += 2
    if any(w in q for w in ["adventure", "hike", "camp", "explore"]):
        preference_bonus += 2
    if any(w in q for w in ["quiet", "relax", "peace", "scenic"]):
        preference_bonus += 2

    for p in PLACES:
        name = p.get("name", "").lower()
        desc = p.get("description", "").lower()
        score = 0
        tokens = q.split()
        if any(token in name for token in tokens):
            score += 4
        if any(token in desc for token in tokens):
            score += 2
        if "beach" in q and "beach" in desc:
            score += 3
        if "national park" in q and "national park" in desc:
            score += 3
        if "view" in q and any(term in name for term in ["view", "viewpoint", "sunset"]):
            score += 3
        if preference_bonus and any(w in desc for w in ["family", "kids", "camp", "scenic", "relax"]):
            score += preference_bonus
        if score > 0:
            results.append((score, p))
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:5]] if results else PLACES[:5]

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

def search_buses() -> list:
    return TRANSPORT.get("buses", [])

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

def search_hotels(query: str = None) -> list:
    if not HOTELS:
        return []
    if not query:
        scored = []
        for hotel in HOTELS:
            rating = hotel.get("rating") or 0
            scored.append((rating, hotel))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:5]]

    q = query.lower()
    min_price, max_price = _parse_price_range_text(q)
    results = []
    for hotel in HOTELS:
        if min_price is not None or max_price is not None:
            if not _price_matches(hotel.get("price_range") or hotel.get("pricing_range"), min_price, max_price):
                continue

        score = 0
        fields = [
            ("name", 6),
            ("description", 4),
            ("location", 4),
            ("address", 3),
            ("amenities", 2),
            ("rating_note", 1),
            ("price_range", 1),
            ("pricing_range", 1),
        ]
        for field, weight in fields:
            value = hotel.get(field, "")
            if isinstance(value, list):
                value = " ".join(str(v) for v in value)
            if any(token in str(value).lower() for token in q.split()):
                score += weight

        if any(w in q for w in ["best", "top", "recommended", "highest", "popular"]):
            try:
                score += float(hotel.get("rating", 0)) * 2
            except (TypeError, ValueError):
                score += 0
            if hotel.get("pricing_range"):
                score += 1

        results.append((score, hotel))

    if not results:
        return HOTELS[:5]

    results.sort(key=lambda x: (-(x[0] or 0), -((x[1].get("rating") or 0))))
    return [item[1] for item in results[:5]]


def search_restaurants(cuisine: str = None, query: str = None) -> list:
    results = RESTAURANTS
    if cuisine:
        q = cuisine.lower()
        results = [r for r in results
                   if q in r.get("cuisine_type", "").lower() or q in r.get("description", "").lower() or q in " ".join(r.get("best_dishes", [])).lower()]

    q = (query or "").lower()
    min_price, max_price = _parse_price_range_text(q)
    if min_price is not None or max_price is not None:
        results = [r for r in results if _price_matches(r.get("pricing_range") or r.get("price_range"), min_price, max_price)]

    if q:
        scored = []
        for restaurant in results:
            score = 0
            for field in ["name", "description", "address", "cuisine_type", "best_dishes", "menu_items", "rating_note", "pricing_range"]:
                value = restaurant.get(field, "")
                if isinstance(value, list):
                    value = " ".join(str(v) for v in value)
                if any(token in str(value).lower() for token in q.split()):
                    score += 2
            if any(w in q for w in ["best", "top", "recommended", "popular"]):
                try:
                    score += float(restaurant.get("rating", 0)) * 2
                except (TypeError, ValueError):
                    score += 0
            scored.append((score, restaurant))
        scored.sort(key=lambda x: (-(x[0] or 0), -((x[1].get("rating") or 0))))
        results = [item[1] for item in scored if item[0] > 0]

    if not results:
        return RESTAURANTS[:5]
    return results[:5]


def build_context(intent: str, user_msg: str) -> tuple:
    context_data = {}
    msg_lower = user_msg.lower()

    if intent == "places":
        context_data = {"places": search_places(user_msg)}

    elif intent == "transport":
        if any(w in msg_lower for w in ["bus", "coach", "ticket"]):
            context_data = {"buses": search_buses(),
                            "general_info": TRANSPORT.get("general_travel_information", {})}
        else:
            budget = None
            nums = re.findall(r'\d{3,}', user_msg.replace(",", ""))
            if nums:
                try:
                    budget = int(nums[0])
                except ValueError:
                    budget = None
            context_data = {
                "car_rentals":  search_cars(budget),
                "pricing":      TRANSPORT.get("pricing_comparison", {}),
                "general_info": TRANSPORT.get("general_travel_information", {})
            }

    elif intent == "emergency":
        context_data = get_emergency_numbers(user_msg)

    elif intent == "hotel":
        context_data = {"hotels": search_hotels(user_msg)}

    elif intent == "restaurant":
        cuisine = None
        for word in ["bbq", "fast food", "pakistani", "afghani", "biryani", "karahi", "seafood", "local", "coffee", "cafe"]:
            if word in msg_lower:
                cuisine = word
                break
        context_data = {"restaurants": search_restaurants(cuisine=cuisine, query=user_msg)}

    return intent, context_data

def format_answer(intent: str, context_data: dict, user_msg: str) -> dict:
    context_json = json.dumps(context_data, ensure_ascii=False, indent=2)

    intent_instructions = {
        "places": """You are a friendly Gwadar tour guide chatbot.
Based on the JSON data provided:
- List the best matching places with name and short description
- Include the Google Maps link from location_url for each place
- Be enthusiastic and welcoming to tourists""",

        "transport": """You are a helpful Gwadar transport assistant chatbot.
Based on the JSON data:
- For car rentals: show vehicle types, prices per day, contact methods
- For buses: show ticket prices, departure timings, booking methods
- Format prices clearly in PKR
- Mention which services have verified phone numbers""",

        "emergency": """You are an emergency assistant for Gwadar. Be calm and very clear.
Based on the JSON data:
- Put critical phone numbers FIRST: Police=15, Ambulance=1122, Fire=16, Edhi=115
- Mention nearest hospitals with details
- Add step-by-step procedure if relevant to the situation""",

        "restaurant": """You are a Gwadar food guide chatbot.
Based on the JSON data:
- List restaurants with cuisine type and address
- Show verified phone numbers if available
- Mention popular dishes for each restaurant
- Show rating and pricing range when available
- Note that Gwadar is a coastal city famous for fresh seafood""",

        "hotel": """You are a Gwadar hotel guide chatbot.
Based on the JSON data:
- List hotels with name, location, pricing range, and rating
- Highlight the best hotel options by rating and value
- Mention proximity to key Gwadar attractions when possible
- Be clear about any missing or unverified fields""",

        "general": """You are a knowledgeable and friendly Gwadar city assistant chatbot.
Answer the tourist's question helpfully.
Gwadar is a CPEC port city in Balochistan, Pakistan with beautiful beaches and a growing port."""
    }

    prompt = f"""{intent_instructions.get(intent, intent_instructions['general'])}

DATA FROM OUR GWADAR DATABASE:
{context_json}

Tourist's question: "{user_msg}"

Write a clear, friendly, well-formatted answer. Use bullet points where helpful.
Keep the answer concise but complete.
End with exactly 3 short follow-up question suggestions the tourist might want to ask.

Format the suggestions exactly like this at the very end:
SUGGESTIONS:
1. [suggestion 1]
2. [suggestion 2]
3. [suggestion 3]"""

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

    if len(suggestions) < 3:
        suggestions = build_suggestion_fallback(intent, user_msg)
    if len(suggestions) < 3:
        defaults = {
            "places":     ["Show me beaches in Gwadar", "What is Koh-e-Batil viewpoint?", "How do I reach Hingol National Park?"],
            "transport":  ["What is the bus ticket price to Gwadar?", "Which car is best for family travel?", "How long is Karachi to Gwadar?"],
            "emergency":  ["Where is the nearest hospital in Gwadar?", "What documents do I need at checkpoints?", "Is Gwadar safe for tourists?"],
            "restaurant": ["What seafood is available in Gwadar?", "Are there cafes in Gwadar?", "What is the local Balochi food?"],
            "hotel":      ["What are the best hotels in Gwadar?", "Which hotels have sea view rooms?", "What is the pricing range for hotels in Gwadar?"],
            "general":    ["Top places to visit in Gwadar?", "How do I travel to Gwadar?", "Is Gwadar safe for tourists?"]
        }
        suggestions = defaults.get(intent, defaults["general"])

    places_with_maps = []
    if intent == "places" and "places" in context_data:
        places_with_maps = [
            {"name": p["name"], "map_url": p.get("location_url", ""), "description": p.get("description", "")}
            for p in context_data["places"]
        ]

    hotels_with_details = []
    if intent == "hotel" and "hotels" in context_data:
        hotels_with_details = [
            {
                "name":          h.get("name", ""),
                "address":       h.get("address", ""),
                "rating":        h.get("rating", None),
                "pricing_range": h.get("pricing_range", ""),
                "description":   h.get("description", ""),
                "location_url":  h.get("location_url", "")
            }
            for h in context_data["hotels"]
        ]

    restaurants_with_details = []
    if intent == "restaurant" and "restaurants" in context_data:
        restaurants_with_details = [
            {
                "name":          r.get("name", ""),
                "address":       r.get("address", ""),
                "cuisine_type":  r.get("cuisine_type", ""),
                "rating":        r.get("rating", None),
                "pricing_range": r.get("pricing_range", ""),
                "description":   r.get("description", "")
            }
            for r in context_data["restaurants"]
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
        "answer":                answer,
        "suggestions":           suggestions,
        "intent":                intent,
        "places_with_maps":      places_with_maps,
        "hotels_with_details":   hotels_with_details,
        "restaurants_with_details": restaurants_with_details,
        "emergency_numbers":     emergency_numbers
    }

def chat(user_msg: str) -> dict:
    intent, context_data = build_context(detect_intent(user_msg), user_msg)
    return format_answer(intent, context_data, user_msg)
