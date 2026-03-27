import os
import sys
import uuid

import streamlit as st
from langchain_core.messages import HumanMessage

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load config - try streamlit secrets first, fall back to .env
try:
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    MODEL_NAME = st.secrets.get("MODEL_NAME", "llama-3.3-70b-versatile")
    os.environ["GROQ_API_KEY"] = GROQ_API_KEY
    os.environ["MODEL_NAME"] = MODEL_NAME
    if "SMTP_EMAIL" in st.secrets:
        os.environ["SMTP_EMAIL"] = st.secrets["SMTP_EMAIL"]
        os.environ["SMTP_PASSWORD"] = st.secrets["SMTP_PASSWORD"]
except Exception:
    from dotenv import load_dotenv

    load_dotenv(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    )

from agent.graph import build_graph
from database.pg_db import get_receipt_data, init_db

init_db()


@st.cache_resource
def get_agent():
    api_key = os.getenv("GROQ_API_KEY", "")
    model = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")
    if not api_key:
        st.error("GROQ_API_KEY not set. Add it to .env or Streamlit secrets.")
        st.stop()
    return build_graph(api_key, model)


agent = get_agent()

st.set_page_config(page_title="OmniBook AI", page_icon="AI", layout="wide")
st.title("OmniBook AI - Ticket Booking Agent")
st.caption("Book flights, trains, and movie tickets with AI assistance")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

with st.sidebar:
    st.header("Quick Actions")
    st.markdown(
        """
    **Try asking:**
    - *Book a flight from Ahmedabad to Goa*
    - *Find trains from Mumbai to Delhi at 1500*
    - *Book a movie ticket in Kolkata*
    - *Show me flights from Kolkata to Delhi*
    """
    )

    if st.button("New Conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.agent_messages = []
        st.rerun()

    st.divider()

    st.subheader("Receipt Lookup")
    booking_id_input = st.number_input("Booking ID", min_value=1, step=1, value=1)
    if st.button("Get Receipt"):
        data = get_receipt_data(booking_id_input)
        if data:
            st.json(data)
        else:
            st.warning("Booking not found.")

    st.divider()
    st.caption(f"Session: {st.session_state.session_id[:8]}...")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("steps"):
            with st.expander("Reasoning Steps", expanded=False):
                for step in msg["steps"]:
                    st.text(step)

if prompt := st.chat_input("What would you like to book?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            st.session_state.agent_messages.append(HumanMessage(content=prompt))

            response_placeholder = st.empty()
            steps_container = st.container()
            all_steps = []
            final_text = "Done."
            final_state = None

            for state in agent.stream(
                {"messages": st.session_state.agent_messages, "steps": []},
                stream_mode="values",
            ):
                final_state = state
                steps = state.get("steps", [])
                messages = state.get("messages", [])

                if steps:
                    all_steps = steps
                    with steps_container:
                        for step in steps[-3:]:
                            st.caption(f"Step: {step[:120]}")

                if messages:
                    last_message = messages[-1]
                    if getattr(last_message, "content", ""):
                        final_text = last_message.content
                        response_placeholder.markdown(final_text + "...")

            response_placeholder.markdown(final_text)

            if final_state and final_state.get("messages"):
                st.session_state.agent_messages = final_state["messages"]

            if all_steps:
                with st.expander("Reasoning Steps", expanded=False):
                    for step in all_steps:
                        st.text(step)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": final_text,
                    "steps": all_steps,
                }
            )

        except Exception as e:
            st.error(f"Error: {str(e)}")
