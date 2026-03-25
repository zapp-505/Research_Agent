import streamlit as st
from services import api


def _reset_auth_and_flow_state():
    st.session_state["token"] = None
    st.session_state["user_email"] = None
    st.session_state["thread_id"] = None
    st.session_state["phase"] = "idle"
    st.session_state["messages"] = []
    st.session_state["interrupt_type"] = None
    st.session_state["last_response"] = None

def handle_start_chat(query: str):
    token = st.session_state.get("token")
    
    with st.spinner("Initializing Research Agents..."):
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
    token = st.session_state.get("token")
    thread_id = st.session_state.get("thread_id")
    
    with st.spinner("Processing feedback... this may take a moment."):
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

def process_api_response(resp: dict):
    st.session_state["phase"] = resp.get("status", "idle")
    st.session_state["thread_id"] = resp.get("thread_id")
    st.session_state["interrupt_type"] = resp.get("interrupt_type")
    st.session_state["last_response"] = resp
    
    # We must fetch the latest message history since the graph advanced
    try:
        if st.session_state["thread_id"]:
            history = api.get_thread_history(st.session_state["token"], st.session_state["thread_id"])
            st.session_state["messages"] = history.get("messages", [])
    except api.AuthExpiredError as e:
        st.warning(str(e))
        _reset_auth_and_flow_state()
        st.rerun()
    except api.ApiError as e:
        st.error(str(e))
    except Exception as e:
        print(f"Fetch history failed inside input_bar: {e}")
        
    st.rerun()

def render_input():
    st.divider()
    phase = st.session_state.get("phase", "idle")
    
    if phase in ["idle", "complete"]:
        # If complete, they can't resume it, they must start a new chat via the sidebar.
        # But if idle, they can start a new chat.
        if phase == "idle":
            prompt = st.chat_input("What would you like to research?", key="start_chat_input")
            if prompt:
                handle_start_chat(prompt)
        else:
            st.info("This research thread is complete. Click '➕ New Chat' in the sidebar to start a new one.")
            
    elif phase == "waiting":
        with st.form("resume_form", clear_on_submit=True):
            user_response = st.text_area("Your response or feedback:")
            cols = st.columns([1, 4])
            with cols[0]:
                submitted = st.form_submit_button("Send Response", use_container_width=True, type="primary")
            if submitted and user_response:
                handle_resume_chat(user_response)
