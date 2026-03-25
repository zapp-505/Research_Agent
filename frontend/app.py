import streamlit as st
from services import native_auth
from components import sidebar, chat_area, input_bar

st.set_page_config(page_title="Research Agent", layout="wide", page_icon="🤖")

# --- INITIALIZE SESSION STATE ---
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = None
if "phase" not in st.session_state:
    st.session_state["phase"] = "idle"  # idle | waiting | complete
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "interrupt_type" not in st.session_state:
    st.session_state["interrupt_type"] = None
if "last_response" not in st.session_state:
    st.session_state["last_response"] = None


# --- LOGIN SCREEN ---
def render_login():
    st.title("Research Agent Login")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        with st.form("login_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            if submit:
                try:
                    user = native_auth.sign_in(email, password)
                    st.session_state["token"] = user["idToken"]
                    st.session_state["user_email"] = email
                    st.success("Logged in successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
                    
    with tab2:
        with st.form("signup_form"):
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign Up")
            if submit:
                try:
                    user = native_auth.sign_up(email, password)
                    st.session_state["token"] = user["idToken"]
                    st.session_state["user_email"] = email
                    st.success("Account created and logged in!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sign up failed: {e}")

# --- MAIN APP ROUTING ---
if not st.session_state["token"]:
    render_login()
else:
    # Sidebar lists sessions
    sidebar.render_sidebar()
    
    # Main Chat Area
    st.header("Research Agent")
    st.caption(f"Logged in as {st.session_state.get('user_email')}")
    
    # Message History
    chat_area.render_chat_messages()
    
    # Special Interrupt block
    chat_area.render_interrupt_ui()
    
    # Input Block (handles its own rendering based on phase)
    input_bar.render_input()
