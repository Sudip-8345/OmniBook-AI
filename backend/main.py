import sys
import os

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from config import GROQ_API_KEY, MODEL_NAME
from agent.graph import build_graph
from database.db import init_db, get_receipt_data

# ── Initialize ───────────────────────────────────────────────
app = FastAPI(title="OmniBook AI", description="Autonomous Ticket Booking Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()
agent = build_graph(GROQ_API_KEY, MODEL_NAME)

# In-memory session store  {session_id: [messages]}
sessions: dict = {}


# ── Schemas ──────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str


class ChatResponse(BaseModel):
    response: str
    steps: list[str]


# ── Endpoints ────────────────────────────────────────────────
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Send a message to the booking agent and get a response with reasoning steps."""
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY not set. Add it to your .env file.")

    # Get or create session
    if req.session_id not in sessions:
        sessions[req.session_id] = []

    # Append the new user message
    sessions[req.session_id].append(HumanMessage(content=req.message))

    # Run the agent graph
    try:
        result = agent.invoke({
            "messages": sessions[req.session_id],
            "steps": [],
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    # Persist updated message history
    sessions[req.session_id] = result["messages"]

    # Extract final response
    response_text = result["messages"][-1].content or "Done."
    steps = result.get("steps", [])

    return ChatResponse(response=response_text, steps=steps)


@app.get("/receipt/{booking_id}")
async def get_receipt(booking_id: int):
    """Retrieve receipt data for a booking by ID."""
    data = get_receipt_data(booking_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Booking #{booking_id} not found")
    return data


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    """Clear a chat session to start fresh."""
    if session_id in sessions:
        del sessions[session_id]
    return {"message": f"Session '{session_id}' cleared"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "OmniBook AI"}


# ── Dev entry point ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
