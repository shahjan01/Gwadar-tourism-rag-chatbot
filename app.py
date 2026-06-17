import streamlit as st
from rag_engine import chat

st.set_page_config(
    page_title="Gwadar City Guide",
    page_icon="🌊",
    layout="centered"
)

if "theme" not in st.session_state:
    st.session_state.theme = "Light"
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

# ── theme colors ────────────────────────────────────────────────────────────
if st.session_state.theme == "Dark":
    bg          = "#0f172a"
    surface     = "#1e293b"
    card_bg     = "#1e3a5f"
    text        = "#f1f5f9"
    text_muted  = "#94a3b8"
    border      = "#3b82f6"
    btn_bg      = "#2563eb"
    btn_fg      = "#ffffff"
    emerg_bg    = "#3b0000"
    emerg_bdr   = "#fc8181"
    emerg_text  = "#fca5a5"
    link_color  = "#60a5fa"
else:
    bg          = "#f8fafc"
    surface     = "#ffffff"
    card_bg     = "#f0fff4"
    text        = "#0f172a"
    text_muted  = "#475569"
    border      = "#2563eb"
    btn_bg      = "#2563eb"
    btn_fg      = "#ffffff"
    emerg_bg    = "#fff5f5"
    emerg_bdr   = "#fc8181"
    emerg_text  = "#c53030"
    link_color  = "#1d4ed8"

st.markdown(f"""
<style>
/* ── global background & text ── */
html, body, .stApp, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], .main, section.main, .block-container {{
    background-color: {bg} !important;
    color: {text} !important;
}}

/* ── chat message bubbles ── */
[data-testid="stChatMessage"] {{
    background-color: {surface} !important;
    color: {text} !important;
}}
[data-testid="stChatMessage"] p,
[data-testid="stChatMessage"] span,
[data-testid="stChatMessage"] li,
[data-testid="stChatMessage"] strong,
[data-testid="stChatMessage"] em,
[data-testid="stChatMessage"] div {{
    color: {text} !important;
}}

/* ── markdown text everywhere ── */
.stMarkdown, .stMarkdown p, .stMarkdown li,
.stMarkdown span, .stMarkdown div {{
    color: {text} !important;
}}

/* ── expander ── */
[data-testid="stExpander"] {{
    background-color: {surface} !important;
    border: 0.5px solid {border} !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span,
[data-testid="stExpander"] p {{
    color: {text} !important;
}}

/* ── place / hotel / restaurant cards ── */
.gw-card {{
    background: {card_bg};
    border: 1px solid {border};
    border-radius: 10px;
    padding: 14px;
    margin: 8px 0;
    color: {text} !important;
}}
.gw-card b  {{ color: {text} !important; font-size: 15px; }}
.gw-card small {{ color: {text_muted} !important; font-size: 13px; }}
.gw-card a  {{ color: {link_color} !important; text-decoration: none; }}
.gw-card a:hover {{ text-decoration: underline; }}
.gw-label   {{ color: {text_muted} !important; font-size: 13px; }}

/* ── emergency box ── */
.emerg-box {{
    background: {emerg_bg};
    border: 2px solid {emerg_bdr};
    border-radius: 10px;
    padding: 16px;
    margin: 10px 0;
}}
.emerg-title {{ color: {text} !important; font-weight: 600; }}
.emerg-num   {{ font-size: 22px; font-weight: bold; color: {emerg_text} !important; }}

/* ── suggestion buttons ── */
.stButton > button {{
    border-radius: 20px !important;
    border: 1px solid {btn_bg} !important;
    background: {btn_bg} !important;
    color: {btn_fg} !important;
    font-size: 13px !important;
    padding: 6px 16px !important;
}}
.stButton > button:hover {{ opacity: 0.88 !important; }}

/* ── caption / small text ── */
.stCaption, [data-testid="stCaptionContainer"] {{
    color: {text_muted} !important;
}}

/* ── chat input ── */
[data-testid="stChatInputTextArea"] {{
    background-color: {surface} !important;
    color: {text} !important;
    border-color: {border} !important;
}}
</style>
""", unsafe_allow_html=True)

# ── header ───────────────────────────────────────────────────────────────────
col1, col2 = st.columns([10, 1])
with col1:
    st.markdown(f"<h3 style='color:{text};margin:0'>🌊 Gwadar City Guide</h3>", unsafe_allow_html=True)
with col2:
    icon = "☀️" if st.session_state.theme == "Dark" else "🌙"
    if st.button(icon, key="theme_toggle"):
        st.session_state.theme = "Light" if st.session_state.theme == "Dark" else "Dark"
        st.rerun()

st.markdown(f"<p style='color:{text_muted};font-size:13px;margin-top:4px'>Your AI assistant for travel, transport, food & emergency in Gwadar, Balochistan</p>", unsafe_allow_html=True)

# ── helper to render cards ───────────────────────────────────────────────────
def place_card(p):
    return f"""<div class="gw-card">
<b>{p.get('name','')}</b><br>
<small>{p.get('description','')}</small><br>
<a href="{p.get('map_url','')}" target="_blank">📍 View on Google Maps</a>
</div>"""

def hotel_card(h):
    rating = f"⭐ {h.get('rating')}" if h.get('rating') else "Rating: N/A"
    price  = h.get('pricing_range') or h.get('price_range') or "N/A"
    phone  = h.get('phone_number','')
    phone_html = f"<br><span class='gw-label'>📞 {phone}</span>" if phone else ""
    loc_url = h.get('location_url','')
    map_html = f"<br><a href='{loc_url}' target='_blank'>📍 View location</a>" if loc_url else ""
    return f"""<div class="gw-card">
<b>{h.get('name','')}</b><br>
<small>{h.get('location', h.get('address',''))}</small><br>
<span class="gw-label">{rating} &nbsp;|&nbsp; Price: {price}</span><br>
<small>{h.get('description','')}</small>{phone_html}{map_html}
</div>"""

def restaurant_card(r):
    rating = f"⭐ {r.get('rating')}" if r.get('rating') else "Rating: N/A"
    phone  = r.get('phone_number','')
    phone_html = f"<br><span class='gw-label'>📞 {phone}</span>" if phone else ""
    return f"""<div class="gw-card">
<b>{r.get('name','')}</b><br>
<small>{r.get('address','')}</small><br>
<span class="gw-label">🍽 {r.get('cuisine_type','')} &nbsp;|&nbsp; {rating}</span><br>
<small>{r.get('description','')}</small>{phone_html}
</div>"""

def render_assistant_extras(msg, expanded=False):
    if msg.get("places"):
        with st.expander("📍 Place details", expanded=expanded):
            for p in msg["places"]:
                st.markdown(place_card(p), unsafe_allow_html=True)
    if msg.get("hotels"):
        with st.expander("🏨 Hotel details", expanded=expanded):
            for h in msg["hotels"]:
                st.markdown(hotel_card(h), unsafe_allow_html=True)
    if msg.get("restaurants"):
        with st.expander("🍽 Restaurant details", expanded=expanded):
            for r in msg["restaurants"]:
                st.markdown(restaurant_card(r), unsafe_allow_html=True)
    if msg.get("emergency_numbers"):
        with st.expander("🚨 Emergency numbers", expanded=True):
            st.markdown('<div class="emerg-box">', unsafe_allow_html=True)
            st.markdown(f'<p class="emerg-title">Emergency Numbers — Call immediately:</p>', unsafe_allow_html=True)
            for n in msg["emergency_numbers"]:
                avail = "24/7" if n.get("available_24_7") else ""
                st.markdown(f'<p><span class="emerg-num">📞 {n["number"]}</span> &nbsp;— {n["service"]} {avail}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ── chat history ─────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_assistant_extras(msg)

# ── suggestion buttons ────────────────────────────────────────────────────────
if st.session_state.suggestions:
    st.markdown(f"<p style='color:{text_muted};font-size:13px;margin-bottom:6px'><b>You might ask:</b></p>", unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.suggestions))
    for i, sug in enumerate(st.session_state.suggestions):
        if cols[i].button(sug, key=f"sug_{i}_{sug[:8]}"):
            st.session_state.pending = sug
            st.rerun()

# ── handle input ──────────────────────────────────────────────────────────────
user_input = st.session_state.pending or st.chat_input("Ask anything about Gwadar...")
if st.session_state.pending:
    st.session_state.pending = None

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    show_expanded = any(w in user_input.lower() for w in
                        ["location", "map", "photo", "picture", "address", "details", "where"])

    with st.chat_message("assistant"):
        with st.spinner("Finding the best answer for you..."):
            result = chat(user_input)
        st.markdown(result["answer"])

        extras = {
            "places":           result.get("places_with_maps", []),
            "hotels":           result.get("hotels_with_details", []),
            "restaurants":      result.get("restaurants_with_details", []),
            "emergency_numbers":result.get("emergency_numbers", [])
        }
        render_assistant_extras(extras, expanded=show_expanded)

    st.session_state.messages.append({
        "role":            "assistant",
        "content":         result["answer"],
        "places":          result.get("places_with_maps", []),
        "hotels":          result.get("hotels_with_details", []),
        "restaurants":     result.get("restaurants_with_details", []),
        "emergency_numbers":result.get("emergency_numbers", [])
    })
    st.session_state.suggestions = result.get("suggestions", [])
    st.rerun()
