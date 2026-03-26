import streamlit as st
from services import api


def _reset_auth_and_flow_state():
    st.session_state["token"]          = None
    st.session_state["user_email"]     = None
    st.session_state["thread_id"]      = None
    st.session_state["phase"]          = "idle"
    st.session_state["messages"]       = []
    st.session_state["interrupt_type"] = None
    st.session_state["last_response"]  = None


def _fetch_and_store_history():
    """Pull latest message history from the backend into session state."""
    thread_id = st.session_state.get("thread_id")
    token     = st.session_state.get("token")
    if not thread_id or not token:
        return
    try:
        history = api.get_thread_history(token, thread_id)
        st.session_state["messages"] = history.get("messages", [])
    except api.AuthExpiredError:
        st.warning("Session expired. Please log in again.")
        _reset_auth_and_flow_state()
        st.rerun()
    except api.ApiError as e:
        st.error(str(e))
    except Exception as e:
        print(f"[input_bar] history fetch failed: {e}")


def process_api_response(resp: dict):
    st.session_state["phase"]          = resp.get("status", "idle")
    st.session_state["thread_id"]      = resp.get("thread_id")
    st.session_state["interrupt_type"] = resp.get("interrupt_type")
    st.session_state["last_response"]  = resp
    _fetch_and_store_history()
    st.rerun()


def handle_start_chat(query: str):
    token = st.session_state.get("token")
    with st.spinner("🔍 Analysing your query…"):
        try:
            resp = api.chat_start(token, query)
            process_api_response(resp)
        except api.AuthExpiredError as e:
            st.warning(str(e))
            _reset_auth_and_flow_state()
            st.rerun()
        except api.ApiError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Error starting chat: {e}")


def handle_resume_chat(user_response: str):
    token     = st.session_state.get("token")
    thread_id = st.session_state.get("thread_id")
    with st.spinner("⚙️ Processing your response…"):
        try:
            resp = api.chat_resume(token, thread_id, user_response)
            process_api_response(resp)
        except api.AuthExpiredError as e:
            st.warning(str(e))
            _reset_auth_and_flow_state()
            st.rerun()
        except api.ApiError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Error resuming chat: {e}")


def render_input():
    st.divider()
    phase = st.session_state.get("phase", "idle")

    if phase == "idle":
        prompt = st.chat_input("What would you like to research?", key="start_chat_input")
        if prompt:
            handle_start_chat(prompt)

    elif phase == "complete":
        st.info("✅ This research session is complete. Click **➕ New Chat** in the sidebar to start a fresh one.")

    elif phase == "waiting":
        itype = st.session_state.get("interrupt_type")

        if itype == "expert_critique":
            placeholder = "Respond to the expert's critique…"
            hint = "💡 You can defend your proposal, provide evidence, or acknowledge the concern."
        elif itype == "confirmation":
            placeholder = "Type 'yes' to confirm, or describe any corrections…"
            hint = "💡 Say 'yes' to proceed, or tell me what to adjust."
        else:
            placeholder = "Your response…"
            hint = ""

        if hint:
            st.markdown(
                f"<div style='font-size:0.8rem;opacity:0.5;margin-bottom:0.5rem;'>{hint}</div>",
                unsafe_allow_html=True,
            )

        with st.form("resume_form", clear_on_submit=True):
            user_response = st.text_area(
                "Response",
                placeholder=placeholder,
                label_visibility="collapsed",
                height=100,
            )
            submitted = st.form_submit_button(
                "Send Response →",
                use_container_width=True,
                type="primary",
            )
            if submitted and user_response.strip():
                handle_resume_chat(user_response.strip())
            elif submitted:
                st.warning("Please enter a response before sending.")
