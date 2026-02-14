import streamlit as st
import uuid
import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage
from agent.graph import build_graph
from database.db import init_db, get_receipt_data

# ── Initialize DB + Agent (cached so it only runs once) ─────
init_db()

@st.cache_resource
def get_agent():
    api_key = os.getenv("GROQ_API_KEY", st.secrets.get("GROQ_API_KEY", ""))
    model = os.getenv("MODEL_NAME", st.secrets.get("MODEL_NAME", "llama-3.3-70b-versatile"))
    if not api_key:
        st.error("GROQ_API_KEY not set. Add it to .env or Streamlit secrets.")
        st.stop()
    return build_graph(api_key, model)

agent = get_agent()

# ── Page config ──────────────────────────────────────────────
st.set_page_config(page_title="OmniBook AI", page_icon="✈️", layout="wide")
st.title("✈️ OmniBook AI – Ticket Booking Agent")
st.caption("Book flights, trains, and movie tickets with AI assistance")

# ── Session state ────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_messages" not in st.session_state:
    st.session_state.agent_messages = []

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("Quick Actions")
    st.markdown(
        """
    **Try asking:**
    - *Book a flight from New York to Los Angeles*
    - *Find trains from Chicago to Detroit under $70*
    - *Book a movie ticket in Mumbai*
    - *Show me flights from Boston to Washington DC*
    """
    )

    if st.button("New Conversation"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.session_state.agent_messages = []
        st.rerun()

    st.divider()

    # Receipt lookup
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

# ── Chat history ─────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("steps"):
            with st.expander("Reasoning Steps", expanded=False):
                for step in msg["steps"]:
                    st.text(step)

# ── Chat input ───────────────────────────────────────────────
if prompt := st.chat_input("What would you like to book?"):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run agent with streaming
    with st.chat_message("assistant"):
        try:
            st.session_state.agent_messages.append(HumanMessage(content=prompt))

            response_placeholder = st.empty()
            steps_container = st.container()
            all_steps = []
            final_text = ""
            streamed_tokens = ""

            for event in agent.stream(
                {"messages": st.session_state.agent_messages, "steps": []},
                stream_mode="updates",
            ):
                # Handle agent node events
                if "agent" in event:
                    agent_data = event["agent"]
                    msgs = agent_data.get("messages", [])
                    new_steps = agent_data.get("steps", [])
                    all_steps.extend(new_steps)

                    for m in msgs:
                        if hasattr(m, "content") and m.content:
                            streamed_tokens += m.content
                            response_placeholder.markdown(streamed_tokens + "▌")

                # Handle tool node events
                if "tools" in event:
                    tool_data = event["tools"]
                    new_steps = tool_data.get("steps", [])
                    all_steps.extend(new_steps)
                    with steps_container:
                        for s in new_steps:
                            st.caption(f"⚙️ {s[:120]}")

            # Final render (remove cursor)
            final_text = streamed_tokens or "Done."
            response_placeholder.markdown(final_text)

            # Get final messages from a full invoke to keep state consistent
            result = agent.invoke({
                "messages": st.session_state.agent_messages,
                "steps": [],
            })
            st.session_state.agent_messages = result["messages"]

            if all_steps:
                with st.expander("Reasoning Steps", expanded=False):
                    for step in all_steps:
                        st.text(step)

            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "steps": all_steps,
            })

        except Exception as e:
            st.error(f"Error: {str(e)}")
