import streamlit as st
from rag_engine import chat

st.set_page_config(
    page_title="Gwadar City Guide",
    page_icon="🌊",
    layout="centered"
)

if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

theme_icon = "☀️" if st.session_state.theme == "Light" else "🌙"
col1, col2 = st.columns([10, 1])
with col1:
    st.markdown("### Gwadar City Guide")
with col2:
    if st.button(theme_icon, key="theme_toggle"):
        st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"

if st.session_state.theme == "Dark":
    background_color = "#0f172a"
    surface_color = "#1e293b"
    text_color = "#e2e8f0"
    card_background = "#15233c"
    border_color = "#3b82f6"
    button_bg = "#2563eb"
    button_fg = "#f8fafc"
else:
    background_color = "#f8fafc"
    surface_color = "#ffffff"
    text_color = "#0f172a"
    card_background = "#f0fff4"
    border_color = "#3182ce"
    button_bg = "#3182ce"
    button_fg = "#ffffff"

st.markdown(f"""
<style>
html, body, .stApp, .block-container, .main, section.main, div[data-testid="stAppViewContainer"] {{
    background-color: {background_color} !important;
    color: {text_color} !important;
}}
body {{ background-color: {background_color} !important; color: {text_color} !important; }}
section.main {{ background-color: {surface_color} !important; }}
footer {{ background-color: {surface_color} !important; color: {text_color} !important; }}
.emergency-box {{
    background: #ffe4e4;
    border: 2px solid #fc8181;
    border-radius: 10px;
    padding: 16px;
    margin: 10px 0;
    color: {text_color};
}}
.emergency-number {{
    font-size: 22px;
    font-weight: bold;
    color: #c53030;
}}
.place-card {{
    background: {card_background};
    border: 1px solid {border_color};
    border-radius: 10px;
    padding: 14px;
    margin: 8px 0;
    color: {text_color};
}}
.suggestion-area {{
    margin-top: 16px;
}}
.stButton > button {{
    border-radius: 20px;
    border: 1px solid {button_bg};
    background: {button_bg};
    color: {button_fg};
    font-size: 13px;
    padding: 6px 16px;
    transition: all 0.2s;
}}
.stButton > button:hover {{
    opacity: 0.9;
}}
</style>
""", unsafe_allow_html=True)

st.caption("Your AI assistant for travel, transport, food & emergency in Gwadar, Balochistan")
st.markdown(f"**Current theme:** {st.session_state.theme}")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "suggestions" not in st.session_state:
    st.session_state.suggestions = [
        "Best places to visit in Gwadar",
        "Bus ticket price from Karachi to Gwadar",
        "Best hotels in Gwadar"
    ]
if "pending" not in st.session_state:
    st.session_state.pending = None

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

        if msg["role"] == "assistant":
            if msg.get("places"):
                with st.expander("Show place details"):
                    for p in msg["places"]:
                        st.markdown(f"""
<div class="place-card">
<b>{p['name']}</b><br>
<small>{p['description']}</small><br>
<a href="{p['map_url']}" target="_blank">📍 View on Google Maps</a>
</div>""", unsafe_allow_html=True)

            if msg.get("hotels"):
                with st.expander("Show hotel details"):
                    for h in msg["hotels"]:
                        hotel_url = h.get("location_url", "")
                        hotel_rating = f"Rating: {h.get('rating')}" if h.get('rating') else "Rating: N/A"
                        hotel_price = f"Price range: {h.get('pricing_range') or h.get('price_range')}" if (h.get('pricing_range') or h.get('price_range')) else "Price range: N/A"
                        hotel_link = f"<br><a href=\"{hotel_url}\" target=\"_blank\">📍 View location</a>" if hotel_url else ""
                        st.markdown(f"""
<div class="place-card">
<b>{h['name']}</b><br>
<small>{h.get('address', 'Address not available')}</small><br>
{hotel_rating}<br>
{hotel_price}<br>
<small>{h.get('description', 'No description available')}</small>{hotel_link}
</div>""", unsafe_allow_html=True)

            if msg.get("restaurants"):
                with st.expander("Show restaurant details"):
                    for r in msg["restaurants"]:
                        restaurant_rating = f"Rating: {r.get('rating')}" if r.get('rating') else "Rating: N/A"
                        restaurant_price = f"Price range: {r.get('pricing_range')}" if r.get('pricing_range') else "Price range: N/A"
                        st.markdown(f"""
<div class="place-card">
<b>{r['name']}</b><br>
<small>{r['address']}</small><br>
Cuisine: {r.get('cuisine_type', 'Cuisine not available')}<br>
{restaurant_rating}<br>
{restaurant_price}<br>
<small>{r.get('description', 'No description available')}</small>
</div>""", unsafe_allow_html=True)

            if msg.get("emergency_numbers"):
                with st.expander("Show emergency contact details"):
                    st.markdown('<div class="emergency-box">', unsafe_allow_html=True)
                    st.markdown("**Emergency Numbers:**")
                    for n in msg["emergency_numbers"]:
                        avail = "24/7" if n.get("available_24_7") else ""
                        st.markdown(f'<span class="emergency-number">📞 {n["number"]}</span> — {n["service"]} {avail}', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.suggestions:
    st.markdown("**You might ask:**")
    cols = st.columns(len(st.session_state.suggestions))
    for i, sug in enumerate(st.session_state.suggestions):
        if cols[i].button(sug, key=f"sug_{i}_{sug[:10]}"):
            st.session_state.pending = sug
            st.rerun()

user_input = st.session_state.pending or st.chat_input("Ask anything about Gwadar...")

if st.session_state.pending:
    st.session_state.pending = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    show_details = any(term in user_input.lower() for term in ["location", "picture", "photo", "map", "details", "image", "view", "address"])

    with st.chat_message("assistant"):
        with st.spinner("Finding the best answer for you..."):
            result = chat(user_input)

        st.markdown(result["answer"])

        if result.get("places_with_maps"):
            with st.expander("Show place details", expanded=show_details):
                for p in result["places_with_maps"]:
                    st.markdown(f"""
<div class="place-card">
<b>{p['name']}</b><br>
<small>{p['description']}</small><br>
<a href="{p['map_url']}" target="_blank">📍 View on Google Maps</a>
</div>""", unsafe_allow_html=True)

        if result.get("hotels_with_details"):
            with st.expander("Show hotel details", expanded=show_details):
                for h in result["hotels_with_details"]:
                    hotel_url = h.get("location_url", "")
                    hotel_rating = f"Rating: {h.get('rating')}" if h.get("rating") else "Rating: N/A"
                    hotel_price = f"Price range: {h.get('pricing_range') or h.get('price_range')}" if (h.get('pricing_range') or h.get('price_range')) else "Price range: N/A"
                    hotel_link = f"<br><a href=\"{hotel_url}\" target=\"_blank\">📍 View location</a>" if hotel_url else ""
                    st.markdown(f"""
<div class="place-card">
<b>{h['name']}</b><br>
<small>{h.get('address', 'Address not available')}</small><br>
{hotel_rating}<br>
{hotel_price}<br>
<small>{h.get('description', 'No description available')}</small>{hotel_link}
</div>""", unsafe_allow_html=True)

        if result.get("restaurants_with_details"):
            with st.expander("Show restaurant details", expanded=show_details):
                for r in result["restaurants_with_details"]:
                    restaurant_rating = f"Rating: {r.get('rating')}" if r.get("rating") else "Rating: N/A"
                    restaurant_price = f"Price range: {r.get('pricing_range')}" if r.get("pricing_range") else "Price range: N/A"
                    st.markdown(f"""
<div class="place-card">
<b>{r['name']}</b><br>
<small>{r.get('address', 'Address not available')}</small><br>
Cuisine: {r.get('cuisine_type', 'Cuisine not available')}<br>
{restaurant_rating}<br>
{restaurant_price}<br>
<small>{r.get('description', 'No description available')}</small>
</div>""", unsafe_allow_html=True)

        if result.get("emergency_numbers"):
            with st.expander("Show emergency contact details", expanded=show_details):
                st.markdown('<div class="emergency-box">', unsafe_allow_html=True)
                st.markdown("**Emergency Numbers:**")
                for n in result["emergency_numbers"]:
                    avail = "24/7" if n.get("available_24_7") else ""
                    st.markdown(f'<span class="emergency-number">📞 {n["number"]}</span> — {n["service"]} {avail}', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

    assistant_msg = {
        "role": "assistant",
        "content": result["answer"],
        "places": result.get("places_with_maps", []),
        "hotels": result.get("hotels_with_details", []),
        "restaurants": result.get("restaurants_with_details", []),
        "emergency_numbers": result.get("emergency_numbers", [])
    }
    st.session_state.messages.append(assistant_msg)
    st.session_state.suggestions = result.get("suggestions", [])
    st.rerun()
