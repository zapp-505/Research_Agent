import json
import streamlit as st


def _initials(name: str) -> str:
    """Extract up to 2 initials, stripping common titles."""
    cleaned = name.replace("Dr.", "").replace("Prof.", "").replace("Mr.", "").replace("Ms.", "").strip()
    words = [w for w in cleaned.split() if w]
    return "".join(w[0].upper() for w in words[:2]) if words else "?"


def _render_panel_intro(content: str):
    """Render the rich expert-panel introduction card."""
    try:
        experts = json.loads(content)
    except (json.JSONDecodeError, TypeError, ValueError):
        st.info(f"**⚔️ Expert panel assembled.**\n\n{content}")
        return

    n = len(experts)
    cards_html = ""
    for expert in experts:
        name    = expert.get("name", "Expert")
        role    = expert.get("role", "Specialist")
        summary = expert.get("summary", "")
        av      = _initials(name)
        cards_html += f"""
        <div class="expert-row">
            <div class="expert-av">{av}</div>
            <div>
                <div class="expert-name">{name}</div>
                <span class="expert-badge">{role}</span>
                <div class="expert-desc">{summary}</div>
            </div>
        </div>"""

    label = "specialist" if n == 1 else "specialists"
    st.markdown(f"""
<div class="panel-intro-wrap">
  <div class="panel-intro-header">⚔️ Expert Panel Assembled</div>
  <div class="panel-intro-sub">{n} {label} will challenge your research proposal from different angles</div>
  <div class="expert-grid">{cards_html}</div>
</div>""", unsafe_allow_html=True)


def render_chat_messages():
    """
    Renders all messages in st.session_state["messages"].

    Roles handled:
      "user"        → user chat bubble
      "assistant"   → assistant bubble (present_node, research_node)
      "ai"          → alias for assistant
      "expert"      → expert critique bubble (expert_node)
      "report"      → final report bubble (blue_team_node)
      "panel_intro" → rich HTML expert panel card (panel_generator_node)
    """
    messages = st.session_state.get("messages", [])
    report_already_rendered = False

    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role    = msg.get("role", "")
        content = msg.get("content", "")

        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)

        elif role in ("assistant", "ai"):
            name = msg.get("name")
            with st.chat_message("assistant"):
                if name and name not in ("assistant", "ai"):
                    st.caption(f"**{name}**")
                st.markdown(content)

        elif role == "expert":
            # Content format from expert_node: "[Name — Role]: <critique text>"
            header, body = "", content
            if content.startswith("[") and "]:" in content:
                idx    = content.index("]:")
                header = content[1:idx]
                body   = content[idx + 2:].strip()
            with st.chat_message("assistant", avatar="⚔️"):
                if header:
                    st.markdown(
                        f"<span style='font-size:0.78rem;font-weight:700;color:#a78bfa;"
                        f"text-transform:uppercase;letter-spacing:0.06em;'>⚔️ {header}</span>",
                        unsafe_allow_html=True,
                    )
                st.markdown(body)

        elif role == "report":
            report_already_rendered = True
            with st.chat_message("assistant", avatar="📄"):
                st.markdown(
                    "<span style='font-size:0.78rem;font-weight:700;color:#60a5fa;"
                    "text-transform:uppercase;letter-spacing:0.06em;'>📄 Final Research Report</span>",
                    unsafe_allow_html=True,
                )
                st.divider()
                st.markdown(content)

        elif role == "panel_intro":
            _render_panel_intro(content)

    # Fallback: show live final_report from last_response if not yet persisted in messages
    if (
        st.session_state.get("phase") == "complete"
        and not report_already_rendered
        and st.session_state.get("last_response")
    ):
        report = st.session_state["last_response"].get("final_report")
        if report:
            with st.chat_message("assistant", avatar="📄"):
                st.markdown(
                    "<span style='font-size:0.78rem;font-weight:700;color:#60a5fa;"
                    "text-transform:uppercase;letter-spacing:0.06em;'>📄 Final Research Report</span>",
                    unsafe_allow_html=True,
                )
                st.divider()
                st.markdown(report)


def render_interrupt_ui():
    """Renders the UI block when the agent is paused waiting for human input."""
    phase = st.session_state.get("phase")
    itype = st.session_state.get("interrupt_type")

    if phase != "waiting":
        return

    resp    = st.session_state.get("last_response", {})
    message = resp.get("message", "The agent is waiting for your input.")

    if itype == "expert_critique":
        expert_name = resp.get("expert_name", "Expert")
        expert_role = resp.get("expert_role", "Reviewer")
        st.markdown(
            f"<div style='font-size:0.82rem;font-weight:700;color:#a78bfa;margin-bottom:0.4rem;'>"
            f"⚔️ {expert_name} &nbsp;·&nbsp; "
            f"<span style='font-weight:400;opacity:0.7;'>{expert_role}</span></div>",
            unsafe_allow_html=True,
        )
        st.info(message)

    elif itype == "confirmation":
        st.markdown(
            "<div style='font-size:0.82rem;font-weight:600;color:#fbbf24;margin-bottom:0.4rem;'>"
            "🔍 Review Interpretation</div>",
            unsafe_allow_html=True,
        )
        st.warning(message)

    elif itype == "resumed":
        st.info("⏸ This session was previously paused. Send your response below to continue.")

    else:
        st.info(message)
