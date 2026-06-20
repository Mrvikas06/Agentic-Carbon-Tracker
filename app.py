"""
app.py — Streamlit frontend for the Agentic Carbon Tracker.
Provides a premium, responsive, glassmorphic UI dashboard with gamification.
"""
from __future__ import annotations

import os
from typing import Optional

import pandas as pd
import requests
import streamlit as st

API_BASE: str = os.getenv("BACKEND_URL", "http://localhost:8000")

# Set Page Config with SEO elements & descriptive title
st.set_page_config(
    page_title="Carbon Tracker | AI-Powered Footprint Analyst",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── PREMIUM GLASSMORPHIC DESIGN SYSTEM ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --primary: #10b981;
    --primary-hover: #34d399;
    --primary-glow: rgba(16, 185, 129, 0.4);
    --bg-dark: #040905;
    --bg-gradient: radial-gradient(circle at 50% 50%, #081d11 0%, #030804 100%);
    --card-bg: rgba(13, 35, 20, 0.45);
    --border: rgba(16, 185, 129, 0.22);
    --text-main: #e2ede3;
    --text-muted: #8bbfa3;
    --accent-cyan: #06b6d4;
    --accent-amber: #f59e0b;
    --accent-rose: #f43f5e;
}

* { 
    font-family: 'Outfit', 'Inter', sans-serif; 
}

/* ── Hide Streamlit Deploy Button and Default Elements ── */
.stAppDeployButton, [data-testid="stAppDeployButton"] {
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
}
header[data-testid="stHeader"] {
    background: transparent !important;
}
[data-testid="stSidebarCollapsedControl"] {
    color: var(--text-main) !important;
    background: rgba(13, 35, 20, 0.45) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    margin-left: 10px !important;
}
#MainMenu, footer { 
    display: none !important; 
}
section[data-testid="stMain"] > div { 
    padding-top: 1.5rem !important; 
}

/* ── Base page gradient ── */
[data-testid="stAppViewContainer"] {
    background: var(--bg-gradient);
    color: var(--text-main);
}
[data-testid="stSidebar"] { 
    background: rgba(5, 14, 8, 0.9); 
    border-right: 1px solid var(--border); 
    backdrop-filter: blur(12px);
}

/* ── Custom Premium Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(10, 28, 16, 0.5);
    border-radius: 16px;
    padding: 6px;
    gap: 10px;
    border: 1px solid var(--border);
    backdrop-filter: blur(8px);
    margin-bottom: 2rem;
    box-shadow: inset 0 0 10px rgba(16, 185, 129, 0.05);
}
.stTabs [data-baseweb="tab"] {
    color: var(--text-muted);
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.6rem 1.8rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid transparent;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--primary-hover);
    background: rgba(16, 185, 129, 0.08);
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #064e3b 0%, #022c22 100%) !important;
    color: #ffffff !important;
    border: 1px solid rgba(16, 185, 129, 0.45) !important;
    border-bottom: 1px solid rgba(16, 185, 129, 0.45) !important;
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
    text-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
}

/* ── Glassmorphic Hero ── */
.hero {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.18) 0%, rgba(6, 78, 59, 0.25) 100%);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 24px;
    padding: 2.5rem 3rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 0 30px rgba(16, 185, 129, 0.08);
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -10%;
    width: 450px;
    height: 450px;
    background: radial-gradient(circle, rgba(16, 185, 129, 0.2) 0%, transparent 70%);
    pointer-events: none;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(90deg, #d1fae5, var(--primary-hover));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.5rem 0;
    letter-spacing: -0.8px;
    text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}
.hero-sub {
    font-size: 1.15rem;
    color: var(--text-muted);
    margin: 0;
    font-weight: 400;
}

/* ── Gamified Progress Badge ── */
.gamify-badge {
    position: absolute;
    top: 2rem;
    right: 3rem;
    background: rgba(16, 185, 129, 0.15);
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 30px;
    padding: 0.5rem 1.2rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-weight: 700;
    color: var(--primary-hover);
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.15);
}

/* ── Stat Cards ── */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.2rem;
    margin-bottom: 2rem;
}
.stat-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.5rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
}
.stat-card:hover { 
    border-color: var(--primary-hover); 
    transform: translateY(-4px); 
    box-shadow: 0 12px 24px rgba(0,0,0,0.3), 0 0 20px rgba(16, 185, 129, 0.15);
}
.stat-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #064e3b, var(--primary));
}
.stat-icon { 
    font-size: 2.2rem; 
    margin-bottom: 0.5rem; 
}
.stat-value {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    line-height: 1.1;
}
.stat-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.4rem;
}

/* ── Section Headers ── */
.section-header {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-muted);
    margin: 2.5rem 0 1.2rem 0;
    display: flex;
    align-items: center;
    gap: 0.6rem;
}
.section-header::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
    margin-left: 0.8rem;
}

/* ── Interactive Item Breakdown Rows ── */
.item-row {
    display: flex;
    align-items: center;
    background: rgba(10, 28, 16, 0.2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 0.9rem 1.4rem;
    margin-bottom: 0.6rem;
    gap: 1.2rem;
    transition: all 0.2s ease;
}
.item-row:hover { 
    border-color: var(--primary-hover);
    background: rgba(10, 28, 16, 0.4);
    box-shadow: 0 0 10px rgba(16, 185, 129, 0.08);
}
.item-name { 
    flex: 1.5; 
    font-weight: 600; 
    color: #ffffff; 
    font-size: 1.05rem; 
}
.item-category {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.cat-food { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.3); }
.cat-transport { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
.cat-energy { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.cat-shopping { background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
.cat-other { background: rgba(107, 114, 128, 0.15); color: #9ca3af; border: 1px solid rgba(107, 114, 128, 0.3); }

.item-qty { 
    color: var(--text-muted); 
    font-size: 0.9rem; 
    min-width: 90px; 
}
.impact-bar-wrap { 
    flex: 2; 
    display: flex; 
    align-items: center; 
    gap: 0.8rem; 
}
.impact-bar-bg { 
    flex: 1; 
    height: 8px; 
    background: rgba(16, 185, 129, 0.12); 
    border-radius: 4px; 
    overflow: hidden; 
}
.impact-bar-fill { 
    height: 100%; 
    border-radius: 4px; 
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); 
}
.impact-low  { background: var(--primary); }
.impact-med  { background: var(--accent-amber); }
.impact-high { background: var(--accent-rose); }
.impact-val  { 
    font-size: 0.95rem; 
    font-weight: 700; 
    color: var(--text-muted); 
    min-width: 80px; 
    text-align: right; 
}

/* ── Gamified Quest Cards ── */
.quest-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    backdrop-filter: blur(10px);
}
.quest-card:hover { 
    border-color: var(--primary-hover); 
    transform: translateX(4px); 
    box-shadow: 0 4px 15px rgba(16, 185, 129, 0.1);
}
.quest-card.accepted { 
    border-color: var(--primary); 
    background: rgba(16, 185, 129, 0.08); 
    box-shadow: 0 0 15px rgba(16, 185, 129, 0.12);
}
.quest-card.completed { 
    border-color: rgba(107, 114, 128, 0.2); 
    background: rgba(20, 25, 22, 0.15); 
    opacity: 0.75;
}
.quest-icon { 
    font-size: 2.2rem; 
    min-width: 56px; 
    height: 56px;
    background: rgba(16, 185, 129, 0.12);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
}
.quest-body { 
    flex: 1; 
}
.quest-title { 
    font-weight: 700; 
    color: #ffffff; 
    font-size: 1.15rem; 
    margin-bottom: 0.3rem; 
}
.quest-desc  { 
    color: var(--text-muted); 
    font-size: 0.95rem; 
    margin-bottom: 0.6rem; 
}
.quest-tags  { 
    display: flex; 
    gap: 0.6rem; 
    flex-wrap: wrap; 
}
.qtag {
    font-size: 0.78rem; 
    font-weight: 600; 
    padding: 3px 12px;
    border-radius: 20px; 
    border: 1px solid;
}
.qtag-easy   { color: var(--primary); border-color: rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.08); }
.qtag-medium { color: var(--accent-amber); border-color: rgba(245, 158, 11, 0.3); background: rgba(245, 158, 11, 0.08); }
.qtag-hard   { color: var(--accent-rose); border-color: rgba(244, 63, 94, 0.3); background: rgba(244, 63, 94, 0.08); }
.qtag-saving { color: #ffffff; border-color: rgba(255, 255, 255, 0.15); background: rgba(255, 255, 255, 0.05); }

/* ── Confidence Pill ── */
.conf-pill {
    display: inline-flex; 
    align-items: center; 
    gap: 0.4rem;
    padding: 4px 12px; 
    border-radius: 20px;
    font-size: 0.8rem; 
    font-weight: 600;
}
.conf-high { background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: var(--primary-hover); }
.conf-med  { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: var(--accent-amber); }
.conf-low  { background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); color: var(--accent-rose); }

/* ── Empty State ── */
.empty-state {
    text-align: center;
    padding: 5rem 2rem;
    color: var(--text-muted);
}
.empty-icon { 
    font-size: 4.5rem; 
    margin-bottom: 1.2rem; 
    opacity: 0.6; 
}
.empty-title { 
    font-size: 1.4rem; 
    font-weight: 700; 
    color: var(--text-main); 
    margin-bottom: 0.6rem; 
}
.empty-sub { 
    font-size: 0.95rem; 
}

/* ── Info Banners & Warnings ── */
.info-banner {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-left: 4px solid var(--primary);
    border-radius: 12px;
    padding: 1rem 1.4rem;
    color: var(--text-main);
    font-size: 0.95rem;
    margin-bottom: 1.2rem;
    backdrop-filter: blur(6px);
}

/* ── Premium Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #064e3b 0%, #022c22 100%);
    color: #ffffff;
    border: 1px solid rgba(16, 185, 129, 0.45);
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.95rem;
    padding: 0.65rem 1.6rem;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.stButton > button:hover {
    background: linear-gradient(135deg, #047857 0%, #064e3b 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 18px rgba(16, 185, 129, 0.3);
    border-color: var(--primary-hover);
}
.stButton > button:active {
    transform: translateY(0);
}
.stButton > button:disabled { 
    background: rgba(10, 20, 12, 0.6); 
    color: rgba(255, 255, 255, 0.25); 
    border-color: rgba(255, 255, 255, 0.05); 
    box-shadow: none; 
}

/* ── Glassmorphic Card Container ── */
.glass-container {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(10px);
}

/* ── About Cards ── */
.about-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 1.8rem;
    height: 100%;
    backdrop-filter: blur(10px);
}
.about-card-title { 
    font-size: 0.9rem; 
    font-weight: 700; 
    color: var(--primary-hover); 
    text-transform: uppercase; 
    letter-spacing: 1.2px; 
    margin-bottom: 1.2rem; 
}
.about-card ul { 
    padding-left: 1.2rem; 
    color: var(--text-muted); 
    line-height: 2; 
}
.about-card li span { 
    color: #ffffff; 
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE INITIALIZATION ─────────────────────────────────────────────
INITIAL_HISTORY = [
    {"item": "Beef mince", "category": "food", "kg_co2": 30.0, "quantity": 0.5, "unit": "kg"},
    {"item": "Whole milk", "category": "food", "kg_co2": 3.2, "quantity": 1.0, "unit": "litre"},
    {"item": "White bread", "category": "food", "kg_co2": 0.7, "quantity": 0.5, "unit": "kg"},
    {"item": "Apples", "category": "food", "kg_co2": 1.1, "quantity": 1.0, "unit": "kg"},
]

for key, val in {
    "analysis_result": None,
    "quests": [],
    "accepted_quests": set(),
    "completed_quests": set(),
    "footprint_history": INITIAL_HISTORY.copy(),
    "points": 100,  # Starting green points for active users
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── EMISSION FACTOR DICT FOR MANUAL USER CO2 ESTIMATION ───────────────────────
FOOD_CO2_MAP = {
    "beef": 60.0, "lamb": 24.0, "pork": 7.6, "chicken": 6.9,
    "fish": 6.1, "shrimp": 12.0, "cheese": 21.0, "milk": 3.2,
    "eggs": 4.5, "tofu": 3.0, "rice": 4.0, "wheat": 1.4,
    "vegetables": 2.0, "fruit": 1.1, "nuts": 2.3, "coffee": 17.0,
    "chocolate": 19.0, "beer": 0.5, "wine": 1.8,
}
FALLBACK_FOOD_CO2 = 3.0

def quick_estimate_co2(name: str, qty: float, unit: str) -> float:
    """Frontend-side local calculation for instant form feedback."""
    name_lower = name.lower()
    qty_kg = qty if unit in ("kg", "g") else 0.5
    if unit == "g":
        qty_kg = qty / 1000
    
    # lookup matches
    for key, factor in FOOD_CO2_MAP.items():
        if key in name_lower:
            return round(factor * qty_kg, 2)
    return round(FALLBACK_FOOD_CO2 * qty_kg, 2)

# ── HELPER CALCULATORS ────────────────────────────────────────────────────────
def co2_to_trees(kg: float) -> float:
    return round(kg / 21.0, 2)

def co2_to_km(kg: float) -> float:
    return round(kg / 0.21, 1)

def co2_to_charges(kg: float) -> int:
    return int(kg / 0.005)

def impact_class(kg: float, max_kg: float) -> str:
    ratio = kg / max_kg if max_kg else 0
    if ratio > 0.5: return "high"
    if ratio > 0.2: return "med"
    return "low"

# ── API ENDPOINT WRAPPERS ─────────────────────────────────────────────────────
def post_receipt(image_bytes: bytes, mime: str, context: str) -> Optional[dict]:
    try:
        resp = requests.post(
            f"{API_BASE}/analyse-receipt",
            files={"file": ("receipt.jpg", image_bytes, mime)},
            data={"extra_context": context},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.ConnectionError:
        st.error("🔌 Cannot reach the backend API. Please check if the FastAPI server is running on port 8000.")
    except requests.exceptions.HTTPError as exc:
        body = exc.response.json() if exc.response else {}
        st.error(f"❌ API Error: {body.get('detail', str(exc))}")
    return None

def post_generate_quests(summary: dict) -> list[dict]:
    try:
        resp = requests.post(f"{API_BASE}/generate-quests", json=summary, timeout=60)
        resp.raise_for_status()
        return resp.json().get("quests", [])
    except Exception as exc:
        st.warning(f"⚠️ Quest generation failed: {exc}")
    return []

def patch_accept_quest(quest_id: str) -> bool:
    try:
        resp = requests.patch(f"{API_BASE}/quests/{quest_id}/accept", timeout=10)
        return resp.status_code == 200
    except Exception:
        # If API key is empty/not set in local dev, simulate successful acceptance
        return True

# ── FOREST TIER PROGRESS HELPER ──────────────────────────────────────────────
def get_forest_tier(points: int) -> tuple[str, str]:
    if points >= 500: return "Ancient Oak 🌳", "#4ade80"
    if points >= 300: return "Thriving Sapling 🌿", "#68d391"
    if points >= 150: return "Young Sprout 🌱", "#a7f3d0"
    return "Forest Seed 🌰", "#c8e6c9"

# ── SIDEBAR METRICS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🌿 Agentic Carbon Tracker")
    st.caption("AI-Powered Carbon Offset Dashboard")
    st.divider()
    
    # Render user points and rank
    tier_name, tier_color = get_forest_tier(st.session_state.points)
    st.markdown(f"🏆 **Your Level**: <span style='color:{tier_color}; font-weight:700'>{tier_name}</span>", unsafe_allow_html=True)
    st.markdown(f"🌟 **Green Points**: `{st.session_state.points}`")
    
    st.divider()
    if st.session_state.footprint_history:
        total_co2 = sum(e["kg_co2"] for e in st.session_state.footprint_history)
        st.metric("Total Active Footprint", f"{total_co2:.1f} kg CO₂e")
        st.metric("🌳 Required Trees (Yearly)", f"{co2_to_trees(total_co2):.2f}")
        st.metric("🚗 Equiv. Car Mileage", f"{co2_to_km(total_co2):.0f} km")
        st.divider()
        
        # Weekly Carbon Budget Slider
        budget = st.slider("Weekly Carbon Budget (kg)", min_value=10, max_value=200, value=75, step=5)
        ratio = min(total_co2 / budget, 2.0)
        pct = int(ratio * 100)
        bar_color = "var(--primary)" if ratio <= 0.8 else "var(--accent-amber)" if ratio <= 1.0 else "var(--accent-rose)"
        
        st.markdown(f"""
        <div style="background: rgba(16, 185, 129, 0.05); padding: 0.8rem; border-radius:12px; border: 1px solid var(--border); margin-bottom: 1rem;">
            <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--text-muted); margin-bottom:6px;">
                <span><b>Weekly Budget</b></span>
                <span>{total_co2:.1f} / {budget} kg</span>
            </div>
            <div style="height:6px; background:rgba(255,255,255,0.05); border-radius:3px; overflow:hidden;">
                <div style="width:{min(pct, 100)}%; height:100%; background:{bar_color}; border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if total_co2 > budget:
            st.error(f"⚠️ Exceeded budget by {total_co2 - budget:.1f} kg!")
        else:
            st.success(f"✅ {budget - total_co2:.1f} kg remaining")
        st.divider()
    
    st.caption("Developed using Google Gemini 1.5 & Streamlit")
    st.caption("Emission Factors: Poore & Nemecek 2018")

# ── NAVIGATION TABS ──────────────────────────────────────────────────────────
tab_dash, tab_scan, tab_quests, tab_about = st.tabs(
    ["  📊  Carbon Dashboard  ", "  📸  Log Emissions  ", "  🎯  Weekly Quests  ", "  ℹ️  About System  "]
)

# ════════════════════════════════════════════════════════════════════════════
# 📊 CARBON DASHBOARD TAB
# ════════════════════════════════════════════════════════════════════════════
with tab_dash:
    # Gamification Banner in Hero
    tier_name, _ = get_forest_tier(st.session_state.points)
    st.markdown(f"""
    <div class="hero">
        <div class="hero-title">🌿 Carbon footprint dashboard</div>
        <div class="hero-sub">Track, analyze, and offset your personal shopping emissions instantly.</div>
        <div class="gamify-badge">
            🌟 {st.session_state.points} GP &nbsp;·&nbsp; {tier_name}
        </div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.footprint_history:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📊</div>
            <div class="empty-title">Your carbon log is currently empty</div>
            <div class="empty-sub">Go to <b>Log Emissions</b> to upload a receipt or add items manually!</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Calculate dynamic metrics based on full logged footprint history
        history_df = pd.DataFrame(st.session_state.footprint_history)
        total_co2 = history_df["kg_co2"].sum()
        trees = co2_to_trees(total_co2)
        km = co2_to_km(total_co2)
        chgs = co2_to_charges(total_co2)

        # ── Stat Cards Grid ──
        st.markdown(f"""
        <div class="stat-grid">
            <div class="stat-card">
                <div class="stat-icon">💨</div>
                <div class="stat-value">{total_co2:.2f}</div>
                <div class="stat-label">kg CO₂e Total Impact</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🌳</div>
                <div class="stat-value">{trees:.2f}</div>
                <div class="stat-label">Annual Trees Needed</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🚗</div>
                <div class="stat-value">{km:.0f}</div>
                <div class="stat-label">Car km Equivalent</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">📱</div>
                <div class="stat-value">{chgs:,}</div>
                <div class="stat-label">Phone Charges Offset</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Graphical Visualizations ──
        col_bar, col_donut = st.columns([3, 2], gap="large")

        with col_bar:
            st.markdown('<div class="section-header">📦 Emissions Breakdown by Item</div>', unsafe_allow_html=True)
            df_sorted = history_df.groupby("item")["kg_co2"].sum().reset_index().sort_values("kg_co2", ascending=True)
            
            fig_bar = go.Figure(go.Bar(
                x=df_sorted["kg_co2"],
                y=df_sorted["item"],
                orientation="h",
                marker=dict(
                    color=df_sorted["kg_co2"],
                    colorscale=[[0, "#22c55e"], [0.5, "#fbbf24"], [1, "#ef4444"]],
                    showscale=False,
                    line_width=0,
                ),
                hovertemplate="<b>%{y}</b><br>%{x:.2f} kg CO₂e<extra></extra>",
            ))
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", 
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#a8d5b0", 
                font_family="Outfit",
                margin=dict(l=0, r=0, t=0, b=0),
                xaxis=dict(gridcolor="rgba(46, 125, 50, 0.15)", title="kg CO₂e"),
                yaxis=dict(showgrid=False),
                height=max(280, len(df_sorted) * 35),
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_donut:
            st.markdown('<div class="section-header">🗂️ Emissions by Category</div>', unsafe_allow_html=True)
            cat_df = history_df.groupby("category")["kg_co2"].sum().reset_index()
            
            # Map category labels to friendly presentation names
            cat_df["cat_label"] = cat_df["category"].apply(lambda x: str(x).capitalize())

            fig_pie = go.Figure(go.Pie(
                labels=cat_df["cat_label"],
                values=cat_df["kg_co2"],
                hole=0.6,
                marker=dict(
                    colors=["#10b981", "#3b82f6", "#f59e0b", "#8b5cf6", "#6b7280"],
                    line=dict(color="#061109", width=2)
                ),
                textinfo="percent",
                textfont=dict(color="#ffffff", size=12, family="Outfit"),
                hovertemplate="<b>%{label}</b><br>%{value:.2f} kg CO₂e (%{percent})<extra></extra>",
            ))
            fig_pie.add_annotation(
                text=f"<b>{total_co2:.1f}</b><br><span style='font-size:11px; color:#8bbfa3'>kg CO₂e</span>",
                x=0.5, y=0.5, showarrow=False, font=dict(color="#ffffff", size=18, family="Outfit"),
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font_color="#a8d5b0", 
                font_family="Outfit",
                margin=dict(l=0, r=0, t=0, b=0),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=-0.1,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=11)
                ),
                height=320,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # ── Interactive Item Breakdown Table ──
        st.markdown('<div class="section-header">🔍 Interactive Footprint History Log</div>', unsafe_allow_html=True)
        max_co2 = history_df["kg_co2"].max()
        
        # Display row items with action buttons
        for idx, row in history_df.sort_values("kg_co2", ascending=False).iterrows():
            pct = min(int(row["kg_co2"] / max_co2 * 100), 100) if max_co2 > 0 else 0
            cls = impact_class(row["kg_co2"], max_co2)
            cat_cls = f"cat-{row['category']}"
            
            c_row, c_btn = st.columns([12, 1], gap="small")
            with c_row:
                st.markdown(f"""
                <div class="item-row">
                    <span class="item-name">{row['item']}</span>
                    <span class="item-category {cat_cls}">{row['category']}</span>
                    <span class="item-qty">{row.get('quantity','—')} {row.get('unit','')}</span>
                    <div class="impact-bar-wrap">
                        <div class="impact-bar-bg">
                            <div class="impact-bar-fill impact-{cls}" style="width:{pct}%"></div>
                        </div>
                    </div>
                    <span class="impact-val">{row['kg_co2']:.2f} kg</span>
                </div>
                """, unsafe_allow_html=True)
            with c_btn:
                # Vertical aligned delete button
                st.write("")
                if st.button("🗑️", key=f"del_{idx}", help=f"Remove '{row['item']}' from history"):
                    st.session_state.footprint_history.pop(idx)
                    st.toast(f"Deleted '{row['item']}' from log")
                    st.rerun()

        # Actions Row: Export & Clear
        st.write("")
        c_export, c_clear, _ = st.columns([3, 3, 6])
        with c_export:
            if st.session_state.footprint_history:
                csv_df = pd.DataFrame(st.session_state.footprint_history)
                csv_data = csv_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Logs to CSV",
                    data=csv_data,
                    file_name="carbon_tracker_history.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        with c_clear:
            if st.button("🚨 Clear All Logs", use_container_width=True):
                st.session_state.footprint_history = []
                st.toast("Cleared footprint history")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# 📸 LOG EMISSIONS TAB
# ════════════════════════════════════════════════════════════════════════════
with tab_scan:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">📸 Add Emission Records</div>
        <div class="hero-sub">Upload a grocery receipt for AI analysis, or log individual items manually.</div>
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio("Choose Input Method", ["📸 Scan Receipt Image", "✍️ Log Manually"], horizontal=True, label_visibility="collapsed")

    if mode == "📸 Scan Receipt Image":
        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.markdown("""
            <div class="glass-container" style="padding: 1.5rem;">
                <h4 style="margin-top:0; color:var(--primary-hover);">📷 How Vision AI Tracking Works</h4>
                <ol style="color:var(--text-muted); line-height: 1.8; font-size:0.95rem; padding-left:1.2rem;">
                    <li>Drop a JPEG, PNG, or WebP photo of your receipt (max 5 MB).</li>
                    <li>Google Gemini Vision reads each item, quantity, and unit.</li>
                    <li>Carbon footprints are calculated using global IPCC lifecycle data.</li>
                    <li>Personalized challenges are automatically generated.</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('<div class="section-header">Upload Receipt File</div>', unsafe_allow_html=True)
            uploaded = st.file_uploader(
                "Drop receipt image here",
                type=["jpg", "jpeg", "png", "webp"],
                label_visibility="collapsed",
            )
            context = st.text_input(
                "Add contextual clues (optional)",
                placeholder="e.g. 'family of 4', 'weekly grocery shop'",
                max_chars=500,
            )
            
            # File validation helper on the frontend
            file_valid = True
            if uploaded:
                size_mb = uploaded.size / (1024 * 1024)
                if size_mb > 5:
                    st.error("⚠️ File exceeds the maximum 5 MB limit. Please compress the image.")
                    file_valid = False

            analyse_btn = st.button(
                "🔍  Analyze Receipt with AI",
                disabled=uploaded is None or not file_valid,
                use_container_width=True,
            )

        with col_right:
            st.markdown('<div class="section-header">Image Preview</div>', unsafe_allow_html=True)
            if uploaded:
                image = Image.open(uploaded)
                st.image(image, use_container_width=True)
                st.markdown(
                    f"<div style='text-align:center; color:#8bbfa3; font-size:0.85rem; margin-top:5px;'>📄 {uploaded.name} ({uploaded.size / 1024:.1f} KB)</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown("""
                <div style="
                    border: 2px dashed var(--border);
                    border-radius: 20px;
                    height: 320px;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    color: var(--text-muted);
                    background: rgba(16, 185, 129, 0.05);
                    gap: 0.8rem;
                ">
                    <div style="font-size:3.5rem; opacity:0.4">🧾</div>
                    <div style="font-size:0.95rem; font-weight:600">Receipt image preview will show here</div>
                </div>
                """, unsafe_allow_html=True)

        if analyse_btn and uploaded:
            st.toast("Initiating AI receipt parser...")
            with st.spinner("🧠 Gemini Vision is reading your receipt items..."):
                uploaded.seek(0)
                result_data = post_receipt(uploaded.read(), uploaded.type or "image/jpeg", context)

            if result_data:
                st.session_state.analysis_result = result_data
                parsed_entries = result_data["summary"]["entries"]
                
                # Append parsed items to history list
                for ent in parsed_entries:
                    st.session_state.footprint_history.append({
                        "item": ent["item"],
                        "category": ent["category"],
                        "kg_co2": ent["kg_co2"],
                        "quantity": ent["quantity"],
                        "unit": ent["unit"]
                    })
                
                st.success(f"Successfully processed {len(parsed_entries)} items!")
                st.toast("Generating quests based on recent purchases...")
                
                with st.spinner("🎯 Creating Weekly Quests..."):
                    quests = post_generate_quests(result_data["summary"])
                    st.session_state.quests = quests
                
                # Award points for scanning receipts
                st.session_state.points += 50
                st.toast("🌟 +50 Green Points awarded for receipt scan!")
                time.sleep(1)
                st.rerun()

    else:
        # ✍️ Log Manually Mode
        st.markdown('<div class="section-header">Log Custom Carbon Entry</div>', unsafe_allow_html=True)
        
        with st.form("manual_entry_form", clear_on_submit=True):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                item_name = st.text_input("Item Name / Description", placeholder="e.g. Grass-fed Beef, Organic Soy Milk", help="Type item name to lookup database factors").strip()
                category = st.selectbox("Category", ["food", "transport", "energy", "shopping", "other"])
            
            with col_m2:
                quantity = st.number_input("Quantity", min_value=0.01, value=1.0, step=0.1)
                unit = st.selectbox("Measurement Unit", ["kg", "g", "litre", "km", "kWh", "units"])
            
            # Live UI Feedback
            estimated_co2 = 0.0
            if item_name:
                estimated_co2 = quick_estimate_co2(item_name, quantity, unit)
                st.info(f"💡 Estimated CO₂e impact: **{estimated_co2:.2f} kg** (Calculated based on '{item_name}')")

            submit_manual = st.form_submit_button("➕ Log Active Footprint")
            
            if submit_manual:
                if not item_name:
                    st.error("Please enter a valid item name.")
                else:
                    final_co2 = quick_estimate_co2(item_name, quantity, unit)
                    
                    st.session_state.footprint_history.append({
                        "item": item_name,
                        "category": category,
                        "kg_co2": final_co2,
                        "quantity": quantity,
                        "unit": unit
                    })
                    
                    # Small points reward for logging manually
                    st.session_state.points += 10
                    st.toast(f"Added '{item_name}' ({final_co2:.2f} kg CO₂) to your tracker! 🌟 +10 GP")
                    time.sleep(0.5)
                    st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# 🎯 WEEKLY QUESTS TAB
# ════════════════════════════════════════════════════════════════════════════
with tab_quests:
    quests = st.session_state.quests

    st.markdown("""
    <div class="hero">
        <div class="hero-title">🎯 Carbon Reduction Quests</div>
        <div class="hero-sub">AI-tailored micro-goals designed to help you reduce your weekly CO₂e footprint.</div>
    </div>
    """, unsafe_allow_html=True)

    if not quests:
        # Check if user has active log items to generate quests from
        if st.session_state.footprint_history:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🎯</div>
                <div class="empty-title">Ready to challenge yourself?</div>
                <div class="empty-sub">Click below to generate personalized quests based on your current carbon logs.</div>
            </div>
            """, unsafe_allow_html=True)
            
            c_gen, _ = st.columns([3, 7])
            with c_gen:
                if st.button("♻️  Generate Quests via AI", use_container_width=True):
                    with st.spinner("Analyzing log categories to tailor quests..."):
                        # Synthesize a temporary summary structure matching API request
                        history_df = pd.DataFrame(st.session_state.footprint_history)
                        total_co2 = history_df["kg_co2"].sum()
                        entries = [
                            {"item": row["item"], "category": row["category"], "kg_co2": row["kg_co2"], "quantity": row["quantity"], "unit": row["unit"]}
                            for _, row in history_df.iterrows()
                        ]
                        summary_payload = {
                            "entries": entries,
                            "total_kg_co2": total_co2,
                            "trees_equivalent": co2_to_trees(total_co2),
                            "km_driven_equivalent": co2_to_km(total_co2),
                            "source_description": f"Personal log ({len(entries)} items)"
                        }
                        quests = post_generate_quests(summary_payload)
                        st.session_state.quests = quests
                    st.toast("Quests successfully generated!")
                    st.rerun()
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-icon">🔒</div>
                <div class="empty-title">Log some items first</div>
                <div class="empty-sub">Quests are dynamically optimized based on your carbon metrics. Add items to unlock!</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        total_saving = sum(q["co2_saving_kg"] for q in quests)
        accepted_ids = st.session_state.accepted_quests
        completed_ids = st.session_state.completed_quests
        committed_kg = sum(q["co2_saving_kg"] for q in quests if q["id"] in accepted_ids)
        offsetted_kg = sum(q["co2_saving_kg"] for q in quests if q["id"] in completed_ids)

        # Gamified metrics header
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Available Quests", len(quests) - len(completed_ids))
        m2.metric("Accepted", len(accepted_ids))
        m3.metric("Completed", len(completed_ids))
        m4.metric("Off-set Achieved", f"{offsetted_kg:.1f} kg CO₂")

        # Gamified Goal Bar
        pct = int(committed_kg / total_saving * 100) if total_saving > 0 else 0
        st.markdown(f"""
        <div style="margin: 1.5rem 0 2rem 0; background: rgba(16, 185, 129, 0.05); padding: 1.2rem; border-radius:16px; border: 1px solid rgba(16, 185, 129, 0.2);">
            <div style="display:flex; justify-content:space-between; font-size:0.88rem; color:var(--text-muted); margin-bottom:8px;">
                <span><b>Committed savings</b>: {committed_kg:.1f} / {total_saving:.1f} kg CO₂</span>
                <span>{pct}% Target</span>
            </div>
            <div style="height:10px; background:rgba(16, 185, 129, 0.12); border-radius:5px; overflow:hidden;">
                <div style="width:{pct}%; height:100%; background:linear-gradient(90deg, #10b981, #064e3b); border-radius:5px; transition:width 0.6s ease;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        DIFF_ICON = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}
        st.markdown('<div class="section-header">Active Quests & Weekly Challenges</div>', unsafe_allow_html=True)

        for quest in quests:
            qid = quest["id"]
            is_accepted = qid in accepted_ids
            is_completed = qid in completed_ids
            
            # Setup dynamic card CSS class
            if is_completed:
                card_cls = "quest-card completed"
                btn_lbl = "✓ Completed"
            elif is_accepted:
                card_cls = "quest-card accepted"
                btn_lbl = "Complete Quest"
            else:
                card_cls = "quest-card"
                btn_lbl = "Accept Quest"

            diff = quest.get("difficulty", "medium")
            diff_icon = DIFF_ICON.get(diff, "⚪")
            saving = quest["co2_saving_kg"]

            col_card, col_btn = st.columns([5, 1], gap="small")
            with col_card:
                st.markdown(f"""
                <div class="{card_cls}">
                    <div class="quest-icon">{diff_icon}</div>
                    <div class="quest-body">
                        <div class="quest-title">{quest['title']}</div>
                        <div class="quest-desc">{quest['description']}</div>
                        <div class="quest-tags">
                            <span class="qtag qtag-{diff}">{diff.capitalize()}</span>
                            <span class="qtag qtag-saving">💚 Saves {saving:.1f} kg CO₂/week</span>
                            <span class="qtag qtag-saving">🌳 {co2_to_trees(saving):.2f} Tree-years</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_btn:
                st.write("")
                st.write("")
                
                # Render interactive action buttons for Quests
                if is_completed:
                    st.markdown("<div style='color:#a8d5b0; font-weight:600; text-align:center; padding-top:0.8rem;'>✨ +100 GP Awarded</div>", unsafe_allow_html=True)
                elif is_accepted:
                    # User completes accepted quest
                    if st.button("Complete", key=f"comp_{qid}", use_container_width=True):
                        st.session_state.accepted_quests.remove(qid)
                        st.session_state.completed_quests.add(qid)
                        
                        # Award green points for completion
                        st.session_state.points += 100
                        st.balloons()
                        st.toast(f"🎉 Awesome! Completed '{quest['title']}'! Awarded 100 GP.")
                        time.sleep(1)
                        st.rerun()
                else:
                    # User accepts quest
                    if st.button("Accept", key=f"q_{qid}", use_container_width=True):
                        if patch_accept_quest(qid):
                            st.session_state.accepted_quests.add(qid)
                            st.toast(f"Quest '{quest['title']}' accepted! Good luck 🌱")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("API error during quest acceptance.")

        # Re-generate quests
        st.write("")
        c_regen, _ = st.columns([3, 7])
        with c_regen:
            if st.button("🔄 Generate New Set of Quests", use_container_width=True):
                st.session_state.quests = []
                st.session_state.accepted_quests = set()
                st.toast("Reset quests list")
                st.rerun()

# ════════════════════════════════════════════════════════════════════════════
# ℹ️ ABOUT SYSTEM TAB
# ════════════════════════════════════════════════════════════════════════════
with tab_about:
    st.markdown("""
    <div class="hero">
        <div class="hero-title">ℹ️ Technical Specifications</div>
        <div class="hero-sub">Learn more about the technology stack, data sources, and calculations powering the tracker.</div>
    </div>
    """, unsafe_allow_html=True)

    a1, a2, a3 = st.columns(3, gap="large")

    with a1:
        st.markdown("""
        <div class="about-card">
            <div class="about-card-title">⚙️ Processing Flow</div>
            <ul>
                <li><span>Upload / Log</span>: Capture receipts or add custom entries.</li>
                <li><span>Gemini Vision</span>: AI parses raw image details structured to JSON.</li>
                <li><span>IPCC Emission Data</span>: Estimates CO₂e footprint dynamically.</li>
                <li><span>Personalized Quests</span>: Generates reduction targets dynamically.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with a2:
        st.markdown("""
        <div class="about-card">
            <div class="about-card-title">📚 Conversion Standards</div>
            <ul>
                <li><span>Food Emission Factors</span> — Poore & Nemecek (2018)</li>
                <li><span>Tree Absorption Rate</span> — 21.0 kg CO₂e/year (IPCC AR6)</li>
                <li><span>Petrol Car Emission</span> — 0.21 kg CO₂e/km (EU standard)</li>
                <li><span>Mobile Charge Footprint</span> — 0.005 kg CO₂e/charge</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with a3:
        st.markdown("""
        <div class="about-card">
            <div class="about-card-title">🛠️ Modern Tech Stack</div>
            <ul>
                <li><span>Frontend Design</span> — Streamlit Custom CSS</li>
                <li><span>Visualizations</span> — Plotly Express & Plotly Graph Objects</li>
                <li><span>Async Backend</span> — FastAPI (asyncio)</li>
                <li><span>AI Orchestration</span> — Google Gemini GenAI SDK</li>
                <li><span>JSON Serialization</span> — Pydantic v2</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-banner" style="margin-top:1.5rem;">
        🔒 <b>Data & Privacy Compliance</b> — Images and contexts are processed strictly in-memory during execution and are never written to disk or shared with third parties.
    </div>
    """, unsafe_allow_html=True)
