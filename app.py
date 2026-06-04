# =============================================================
# app.py  —  CareerBot AI  |  Streamlit UI
# =============================================================
"""
Run with:
    streamlit run app.py

Requires GEMINI_API_KEY in environment or .env file.
"""

import os
import sys
import pathlib

# ------------------------------------------------------------------
# FIX: Load .env BEFORE anything else (even before streamlit import)
# ------------------------------------------------------------------
# We do this manually here because:
#   1. Streamlit reruns the script from top to bottom on every user action
#   2. load_dotenv() must run before os.getenv() is ever called
#   3. We look for .env in the same folder as this script, not wherever
#      the terminal was launched from (common mistake!)
#
from dotenv import load_dotenv

# Find the folder this script lives in and look for a local env file there
_THIS_DIR = pathlib.Path(__file__).parent.resolve()
_POSSIBLE_ENV_PATHS = [_THIS_DIR / ".env", _THIS_DIR / ".env.local", _THIS_DIR / ",env"]
_ENV_PATH = next((path for path in _POSSIBLE_ENV_PATHS if path.exists()), _THIS_DIR / ".env")

# override=True means the loaded env file always wins over stale shell env vars
load_dotenv(dotenv_path=_ENV_PATH, override=True)

# Quick sanity-check (visible in your terminal, not in the UI)
if os.getenv("GEMINI_API_KEY"):
    print(f"[CareerBot] ✅ GEMINI_API_KEY loaded from: {_ENV_PATH}", file=sys.stderr)
else:
    print(f"[CareerBot] ⚠️  GEMINI_API_KEY not found. Looked at: {_ENV_PATH}", file=sys.stderr)

# ------------------------------------------------------------------
# NOW import streamlit and everything else
# ------------------------------------------------------------------
import streamlit as st
from gemini_client import GeminiClient


# ------------------------------------------------------------------
# PAGE CONFIG  (must be the very first Streamlit call)
# ------------------------------------------------------------------
st.set_page_config(
    page_title="CareerBot AI",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://aistudio.google.com/app/apikey",
        "About": "CareerBot AI — Powered by Google Gemini",
    },
)


# ------------------------------------------------------------------
# CUSTOM CSS  —  Clean dark-navy + gold accent design
# ------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Serif+Display&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0f1117;
    color: #e8eaf0;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.5rem !important; max-width: 900px; }

/* ── Hero banner ── */
.hero {
    background: linear-gradient(135deg, #1b2a4a 0%, #0f1823 100%);
    border: 1px solid #2a3f6f;
    border-radius: 16px;
    padding: 1.6rem 2rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
}
.hero-icon { font-size: 2.8rem; line-height: 1; }
.hero h1 {
    font-family: 'DM Serif Display', serif;
    font-size: 1.9rem;
    margin: 0;
    color: #f0c060;
    letter-spacing: -0.3px;
}
.hero p { margin: 0.25rem 0 0; color: #8fa0c0; font-size: 0.9rem; }

/* ── Chat messages ── */
.msg-row { display: flex; gap: 0.6rem; margin: 0.7rem 0; align-items: flex-start; }
.msg-row.user  { flex-direction: row-reverse; }

.avatar {
    width: 34px; height: 34px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; flex-shrink: 0; margin-top: 2px;
}
.avatar.bot  { background: #1b2a4a; border: 1px solid #2a3f6f; }
.avatar.user { background: #f0c06022; border: 1px solid #f0c06055; }

.bubble {
    border-radius: 14px;
    padding: 0.75rem 1rem;
    font-size: 0.92rem;
    line-height: 1.65;
    max-width: 80%;
}
.bubble.user {
    background: #1b2a4a;
    border: 1px solid #2a3f6f;
    border-top-right-radius: 4px;
    color: #dce8ff;
}
.bubble.bot {
    background: #141c2e;
    border: 1px solid #1e2d4a;
    border-top-left-radius: 4px;
    color: #e0e8f8;
}
.bubble.bot strong { color: #f0c060; }
.bubble.bot code   { background: #1b2a4a; padding: 1px 5px; border-radius: 4px; font-size: 0.85em; }

/* ── Name label above bubble ── */
.sender { font-size: 0.72rem; color: #5a7090; margin-bottom: 3px; font-weight: 500; }
.sender.right { text-align: right; }

/* ── Welcome card ── */
.welcome {
    text-align: center;
    padding: 3rem 1.5rem;
    border: 1px dashed #2a3f6f;
    border-radius: 16px;
    margin: 1rem 0;
    background: #0d1420;
}
.welcome h2 {
    font-family: 'DM Serif Display', serif;
    color: #f0c060;
    margin: 0.8rem 0 0.4rem;
    font-size: 1.5rem;
}
.welcome p { color: #607090; font-size: 0.9rem; max-width: 460px; margin: 0 auto; }

/* ── Input row ── */
.stTextArea textarea {
    background: #141c2e !important;
    border: 1.5px solid #2a3f6f !important;
    border-radius: 12px !important;
    color: #dce8ff !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.93rem !important;
    resize: none !important;
}
.stTextArea textarea:focus { border-color: #f0c060 !important; box-shadow: 0 0 0 2px #f0c06030 !important; }

.stButton > button {
    border-radius: 12px !important;
    background: linear-gradient(135deg, #c9a030, #f0c060) !important;
    color: #0f1117 !important;
    border: none !important;
    font-weight: 700 !important;
    font-family: 'DM Sans', sans-serif !important;
    letter-spacing: 0.2px !important;
    width: 100% !important;
    padding: 0.55rem 1.2rem !important;
    transition: opacity .2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0d1420 !important;
    border-right: 1px solid #1e2d4a !important;
}
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox select {
    background: #141c2e !important;
    border-color: #2a3f6f !important;
    color: #dce8ff !important;
    border-radius: 8px !important;
}

.sidebar-card {
    background: #141c2e;
    border: 1px solid #1e2d4a;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    margin-bottom: 0.9rem;
}
.sidebar-card h4 {
    color: #f0c060;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 0 0 0.6rem;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}

/* ── Status pill ── */
.status-pill {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 12px; border-radius: 20px;
    font-size: 0.78rem; font-weight: 600;
}
.status-pill.on  { background: #0d2a1a; border: 1px solid #1a6030; color: #4cde80; }
.status-pill.off { background: #2a0d0d; border: 1px solid #601a1a; color: #de4c4c; }
.dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.dot.on  { background: #4cde80; box-shadow: 0 0 6px #4cde80; }
.dot.off { background: #de4c4c; box-shadow: 0 0 6px #de4c4c; }

/* ── Metric numbers ── */
[data-testid="metric-container"] label { color: #607090 !important; font-size: 0.72rem !important; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f0c060 !important; font-size: 1.1rem !important; }

/* ── Quick topic chips ── */
div[data-testid="column"] .stButton > button {
    background: #141c2e !important;
    color: #8fa0c0 !important;
    border: 1px solid #2a3f6f !important;
    border-radius: 20px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 0.28rem 0.6rem !important;
}
div[data-testid="column"] .stButton > button:hover {
    border-color: #f0c060 !important;
    color: #f0c060 !important;
}

/* ── Divider ── */
hr { border-color: #1e2d4a !important; }

/* ── Warning / info boxes ── */
.stAlert { border-radius: 10px !important; font-size: 0.88rem !important; }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------
# SESSION STATE INITIALISATION
# ------------------------------------------------------------------
def init_session_state():
    defaults = {
        "chat_history":  [],
        "gemini_client": None,
        "user_context":  {},
        "total_calls":   0,
        "pending_input": "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()


# ------------------------------------------------------------------
# GEMINI CLIENT  (cached per session so it isn't recreated on reruns)
# ------------------------------------------------------------------
@st.cache_resource
def get_gemini_client(api_key: str) -> GeminiClient:
    os.environ["GEMINI_API_KEY"] = api_key
    return GeminiClient()


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="padding:0.6rem 0 0.4rem">'
        '<span style="font-family:\'DM Serif Display\',serif;font-size:1.3rem;color:#f0c060;">💼 CareerBot AI</span>'
        '<br><span style="font-size:0.78rem;color:#607090;">Powered by Google Gemini</span>'
        '</div>',
        unsafe_allow_html=True
    )
    st.divider()

    # ── API Key ──────────────────────────────────────────────────
    st.markdown('<div class="sidebar-card"><h4>🔑 API Key</h4>', unsafe_allow_html=True)

    env_key = os.getenv("GEMINI_API_KEY", "").strip()

    if env_key and env_key not in ("your_gemini_api_key_here", ""):
        source = ".env" if _ENV_PATH.name == ".env" else _ENV_PATH.name
        st.success(f"Loaded from {source}", icon="🔒")
        active_key = env_key
    else:
        if not _ENV_PATH.exists():
            st.info(
                "Upload a `.env` file with `GEMINI_API_KEY=...` into the app folder. "
                "The app loads it automatically on startup.",
                icon="ℹ️",
            )
        active_key = st.text_input(
            "Gemini API Key",
            type="password",
            placeholder="AIza…",
            help="Free key at aistudio.google.com/app/apikey",
            label_visibility="collapsed",
        ).strip()
        if not active_key:
            st.caption("🔗 [Get a free key →](https://aistudio.google.com/app/apikey)")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Initialise client ────────────────────────────────────────
    if active_key:
        client    = get_gemini_client(active_key)
        connected = client.is_ready
    else:
        client    = None
        connected = False

    if connected:
        st.markdown('<span class="status-pill on"><span class="dot on"></span>Connected · Gemini 1.5 Flash</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pill off"><span class="dot off"></span>Disconnected</span>', unsafe_allow_html=True)

    st.divider()

    # ── User Profile ─────────────────────────────────────────────
    st.markdown('<div class="sidebar-card"><h4>👤 Your Profile (optional)</h4>', unsafe_allow_html=True)
    job_title  = st.text_input("Current / Target Role", placeholder="e.g. Data Analyst")
    experience = st.selectbox("Experience", ["", "0–1 yr (Fresher)", "1–3 yrs", "3–7 yrs", "7–15 yrs", "15+ yrs"])
    industry   = st.selectbox("Industry", ["", "Technology", "Finance", "Healthcare", "Education", "Marketing", "Design", "Other"])
    st.markdown("</div>", unsafe_allow_html=True)

    st.session_state.user_context = {
        "job_title":  job_title.strip() or None,
        "experience": experience or None,
        "industry":   industry or None,
    }

    # ── Session Stats ─────────────────────────────────────────────
    if client and connected:
        t = client.token_tracker
        st.markdown('<div class="sidebar-card"><h4>📊 Session Stats</h4>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Calls",   t.call_count)
        c2.metric("In tok",  f"{t.total_input:,}")
        c3.metric("Out tok", f"{t.total_output:,}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.divider()

    # ── Clear Chat ───────────────────────────────────────────────
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.chat_history = []
        get_gemini_client.clear()
        st.rerun()

    # ── Quick Topic Chips ────────────────────────────────────────
    st.markdown('<p style="font-size:0.8rem;color:#607090;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin:0.6rem 0 0.4rem">💡 Quick Topics</p>', unsafe_allow_html=True)
    chips = ["Resume tips", "Interview prep", "Salary negotiation", "Career switch", "LinkedIn profile", "Skill roadmap"]
    cols  = st.columns(2)
    for i, chip in enumerate(chips):
        with cols[i % 2]:
            if st.button(chip, key=f"chip_{i}", use_container_width=True):
                st.session_state.pending_input = f"Give me advice on: {chip}"
                st.rerun()


# ------------------------------------------------------------------
# MAIN AREA
# ------------------------------------------------------------------

# ── Hero Banner ───────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-icon">💼</div>
    <div>
        <h1>CareerBot AI</h1>
        <p>Resume · Interviews · Job Search · Salary · Career Transitions</p>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Welcome screen (empty chat) ───────────────────────────────────
if not st.session_state.chat_history:
    st.markdown("""
    <div class="welcome">
        <div style="font-size:2.5rem;">👋</div>
        <h2>How can I help your career today?</h2>
        <p>Ask me anything about resumes, interviews, job searching, salary negotiation,
        or career transitions. Use Quick Topics in the sidebar to get started instantly.</p>
    </div>
    """, unsafe_allow_html=True)


# ── Chat History ──────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    if msg["role"] == "user":
        st.markdown(
            '<div class="sender right">You</div>'
            f'<div class="msg-row user">'
            f'  <div class="avatar user">🧑</div>'
            f'  <div class="bubble user">{msg["content"]}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        # Use st.markdown for bot replies so Markdown (bold, lists) renders properly
        st.markdown('<div class="sender">💼 CareerBot</div>', unsafe_allow_html=True)
        with st.container():
            st.markdown(
                '<div class="bubble bot" style="max-width:82%">',
                unsafe_allow_html=True
            )
            st.markdown(msg["content"])
            st.markdown("</div>", unsafe_allow_html=True)


st.divider()


# ── Input Row ─────────────────────────────────────────────────────
col_input, col_send = st.columns([5, 1])

with col_input:
    default_text = st.session_state.get("pending_input", "")
    user_input   = st.text_area(
        "Message",
        value=default_text,
        placeholder="Ask about your career — e.g. 'How do I prepare for a PM interview?'",
        height=80,
        label_visibility="collapsed",
        key="user_input_area",
    )
    if default_text:
        st.session_state.pending_input = ""

with col_send:
    st.markdown("<br>", unsafe_allow_html=True)
    send_clicked = st.button("Send ➤", use_container_width=True)

st.caption("💡 Tip: Fill in **Your Profile** in the sidebar for more personalised advice.")


# ------------------------------------------------------------------
# MESSAGE PROCESSING
# ------------------------------------------------------------------
if send_clicked and user_input.strip():
    cleaned = user_input.strip()

    # 1. Save user message
    st.session_state.chat_history.append({"role": "user", "content": cleaned})

    # 2. Call the API
    with st.spinner("CareerBot is thinking…"):
        if not connected or client is None:
            bot_text = GeminiClient._not_ready_message()
            success  = False
        else:
            resp     = client.send_message(
                user_input   = cleaned,
                chat_history = st.session_state.chat_history,
                user_context = st.session_state.user_context or None,
            )
            bot_text = resp.text
            success  = resp.success

            if success:
                st.session_state.total_calls += 1

    # 3. Save bot reply and refresh
    st.session_state.chat_history.append({"role": "assistant", "content": bot_text})
    st.rerun()

elif send_clicked and not user_input.strip():
    st.warning("Please type a message before sending!", icon="⚠️")
