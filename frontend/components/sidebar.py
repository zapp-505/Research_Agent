import streamlit as st
from services import api


def _reset_local_state():
    st.session_state["token"]          = None
    st.session_state["user_email"]     = None
    st.session_state["thread_id"]      = None
    st.session_state["phase"]          = "idle"
    st.session_state["messages"]       = []
    st.session_state["interrupt_type"] = None
    st.session_state["last_response"]  = None


def _phase_icon(phase: str) -> str:
    return {"idle": "⚪", "waiting": "🟡", "complete": "🟢"}.get(phase, "⚪")


def render_sidebar():
    with st.sidebar:
        # ── Brand ──────────────────────────────────────────────────────────
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">⚔️ Gaunlet</div>
            <div class="sidebar-brand-sub">ADVERSARIAL RESEARCH</div>
        </div>
        """, unsafe_allow_html=True)

        # ── Action Buttons ──────────────────────────────────────────────────
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New Chat", use_container_width=True, type="primary"):
                st.session_state["thread_id"]      = None
                st.session_state["phase"]          = "idle"
                st.session_state["messages"]       = []
                st.session_state["interrupt_type"] = None
                st.session_state["last_response"]  = None
                st.rerun()
        with col2:
            if st.button("Logout", use_container_width=True):
                _reset_local_state()
                st.rerun()

        st.divider()

        # ── Sessions List ───────────────────────────────────────────────────
        st.markdown(
            "<div class='sessions-label'>Your Sessions</div>",
            unsafe_allow_html=True,
        )

        try:
            sessions = api.get_sessions(st.session_state["token"])
            if not sessions:
                st.markdown(
                    "<div style='font-size:0.82rem;opacity:0.35;padding:0.4rem 0;'>"
                    "No sessions yet. Start a new chat!</div>",
                    unsafe_allow_html=True,
                )
            else:
                current_thread = st.session_state.get("thread_id")
                for session in sessions:
                    thread_id = session["thread_id"]
                    title     = session.get("title", "Untitled Session")
                    phase     = session.get("agent_phase", "idle")
                    icon      = _phase_icon(phase)
                    short     = title[:34] + ("…" if len(title) > 34 else "")
                    label     = f"{icon} {short}"

                    # Highlight active session
                    is_active = thread_id == current_thread
                    btn_type  = "primary" if is_active else "secondary"

                    if st.button(label, key=f"sess_{session['_id']}",
                                 use_container_width=True, type=btn_type):
                        history = api.get_thread_history(
                            st.session_state["token"], thread_id
                        )
                        st.session_state["thread_id"]      = thread_id
                        st.session_state["messages"]       = history.get("messages", [])
                        st.session_state["phase"]          = phase
                        st.session_state["interrupt_type"] = "resumed" if phase == "waiting" else None
                        st.session_state["last_response"]  = {}
                        st.rerun()

        except api.AuthExpiredError:
            st.warning("Session expired. Please log in again.")
            _reset_local_state()
            st.rerun()
        except Exception as e:
            st.error(f"Failed to load sessions: {e}")
