import streamlit as st
from services import native_auth
from services.api import ApiError
from components import sidebar, chat_area, input_bar

st.set_page_config(
    page_title="Gaunlet — Adversarial Research",
    layout="wide",
    page_icon="⚔️",
    initial_sidebar_state="expanded",
)

# ── CSS Injection ────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, .stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #6e40c9; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    border-right: 1px solid #21262d !important;
}

/* ── Form submit button ── */
.stFormSubmitButton button {
    width: 100% !important;
    font-weight: 600 !important;
    padding: 0.6rem 1rem !important;
    border-radius: 8px !important;
    letter-spacing: 0.01em !important;
    transition: all 0.2s ease !important;
}
.stFormSubmitButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px rgba(110,64,201,0.4) !important;
}

/* ── Tabs ── */
div[data-baseweb="tab-highlight"],
div[data-baseweb="tab-border"] { display: none !important; }
div[data-baseweb="tab-list"] {
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
}
div[data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    margin-bottom: 0.5rem !important;
}

/* ── Headings ── */
h1 { font-weight: 800 !important; letter-spacing: -0.5px !important; }
h2, h3 { font-weight: 600 !important; }

/* ── Divider ── */
hr { margin: 0.75rem 0 !important; opacity: 0.3 !important; }

/* ── Panel intro card ── */
.panel-intro-wrap {
    background: linear-gradient(135deg, rgba(110,64,201,0.08), rgba(9,105,218,0.06));
    border: 1px solid rgba(110,64,201,0.25);
    border-radius: 16px;
    padding: 1.25rem 1.5rem 1.5rem;
    margin: 0.25rem 0;
}
.panel-intro-header {
    font-size: 1.05rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}
.panel-intro-sub {
    font-size: 0.82rem;
    opacity: 0.55;
    margin-bottom: 1.1rem;
}
.expert-grid { display: flex; flex-direction: column; gap: 0.65rem; }
.expert-row {
    display: flex;
    align-items: flex-start;
    gap: 0.85rem;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 0.85rem 1rem;
}
.expert-av {
    width: 42px; height: 42px; min-width: 42px;
    border-radius: 50%;
    background: linear-gradient(135deg, #6e40c9, #0969da);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 700; color: white;
    letter-spacing: -0.5px;
    box-shadow: 0 2px 8px rgba(110,64,201,0.35);
}
.expert-name { font-weight: 600; font-size: 0.92rem; margin-bottom: 3px; }
.expert-badge {
    display: inline-block;
    background: rgba(110,64,201,0.15);
    color: #a78bfa;
    border: 1px solid rgba(110,64,201,0.2);
    border-radius: 5px;
    padding: 1px 7px;
    font-size: 0.7rem; font-weight: 600;
    margin-bottom: 5px;
    text-transform: uppercase; letter-spacing: 0.04em;
}
.expert-desc { font-size: 0.82rem; opacity: 0.65; line-height: 1.5; }

/* ── Login page ── */
.login-hero { text-align: center; padding: 2.5rem 0 2rem; }
.login-logo {
    font-size: 2.8rem; letter-spacing: -2px; font-weight: 800;
    background: linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; line-height: 1; margin-bottom: 0.5rem;
}
.login-tagline { font-size: 0.9rem; opacity: 0.45; font-weight: 400; letter-spacing: 0.02em; }
.login-features {
    display: flex; justify-content: center; gap: 2rem;
    margin-top: 1.5rem; padding-top: 1.5rem;
    border-top: 1px solid rgba(255,255,255,0.06);
}
.login-feature { text-align: center; font-size: 0.78rem; opacity: 0.4; }
.login-feature .fi { font-size: 1.1rem; display: block; margin-bottom: 0.25rem; }

/* ── Sidebar brand ── */
.sidebar-brand {
    padding: 0.5rem 0 1rem;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    margin-bottom: 1rem;
}
.sidebar-brand-title { font-size: 1.3rem; font-weight: 800; letter-spacing: -0.5px; }
.sidebar-brand-sub { font-size: 0.7rem; opacity: 0.35; margin-top: 1px; letter-spacing: 0.05em; }
.sessions-label {
    font-size: 0.7rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.08em;
    opacity: 0.35; margin-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)


# ── Session State Init ───────────────────────────────────────────────────────
_defaults = {
    "token": None, "user_email": None, "thread_id": None,
    "phase": "idle", "messages": [], "interrupt_type": None, "last_response": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Login Page ───────────────────────────────────────────────────────────────
def render_login():
    inject_css()
    _, col, _ = st.columns([1, 1.6, 1])
    with col:
        st.markdown("""
        <div class="login-hero">
            <div class="login-logo">⚔️ GAUNLET</div>
            <div class="login-tagline">AI-Powered Adversarial Research Platform</div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["  Sign In  ", "  Create Account  "])

        with tab1:
            with st.form("login_form"):
                email    = st.text_input("Email",    placeholder="you@example.com",         label_visibility="collapsed")
                password = st.text_input("Password", placeholder="Password",               type="password", label_visibility="collapsed")
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                submit = st.form_submit_button("Sign In →", use_container_width=True, type="primary")
                if submit:
                    if not email or not password:
                        st.error("Please enter both email and password.")
                    else:
                        try:
                            user = native_auth.sign_in(email, password)
                            st.session_state["token"]      = user["idToken"]
                            st.session_state["user_email"] = email
                            st.rerun()
                        except ApiError as e:
                            st.error(str(e))
                        except Exception as e:
                            st.error(f"Sign-in failed: {e}")

        with tab2:
            with st.form("signup_form"):
                email    = st.text_input("Email",    placeholder="you@example.com",               label_visibility="collapsed")
                password = st.text_input("Password", placeholder="Password (min. 8 characters)", type="password", label_visibility="collapsed")
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                submit = st.form_submit_button("Create Account →", use_container_width=True, type="primary")
                if submit:
                    if not email or not password:
                        st.error("Please fill in all fields.")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters.")
                    else:
                        try:
                            user = native_auth.sign_up(email, password)
                            st.session_state["token"]      = user["idToken"]
                            st.session_state["user_email"] = email
                            st.rerun()
                        except ApiError as e:
                            st.error(str(e))
                        except Exception as e:
                            st.error(f"Sign-up failed: {e}")

        st.markdown("""
        <div class="login-features">
            <div class="login-feature"><span class="fi">🔍</span>Deep Analysis</div>
            <div class="login-feature"><span class="fi">⚔️</span>Expert Panel</div>
            <div class="login-feature"><span class="fi">📄</span>Final Report</div>
        </div>
        """, unsafe_allow_html=True)


# ── Main App ─────────────────────────────────────────────────────────────────
if not st.session_state["token"]:
    render_login()
else:
    inject_css()
    sidebar.render_sidebar()

    email_display = st.session_state.get("user_email", "")
    st.markdown(
        "<div style='font-size:1.6rem;font-weight:800;letter-spacing:-0.5px;margin-bottom:2px;'>"
        "⚔️ Gaunlet</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"🟢 Signed in as **{email_display}**")
    st.divider()

    chat_area.render_chat_messages()
    chat_area.render_interrupt_ui()
    input_bar.render_input()
