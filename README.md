# OmniBook AI – Autonomous Ticket Booking Agent

An agentic AI system that autonomously books **flights**, **trains**, and **movie tickets** through natural conversation.

Built with **LangGraph** (structured tool-calling agent), **FastAPI**, **Streamlit**, and **SQLite**.

---

## Architecture

```
User (Streamlit Chat UI)
        │
        ▼
  FastAPI Backend  ──►  /receipt/{id}
        │
        ▼
  LangGraph Agent
   ┌────┴────┐
   │  Agent  │◄──── GPT-4o-mini (decides next action)
   │  Node   │
   └────┬────┘
        │ tool calls
        ▼
   ┌─────────┐
   │  Tools  │──► search_tickets, filter_by_budget,
   │  Node   │    collect_passenger_details, process_payment_mock,
   └────┬────┘    save_booking_to_db, generate_receipt,
        │         send_email_confirmation
        ▼
     SQLite DB
```

## Project Structure

```
OmniBook-AI/
├── config.py              # Environment configuration
├── data/
│   └── tickets.json       # Dummy ticket data (flights, trains, movies)
├── database/
│   ├── __init__.py
│   └── db.py              # SQLite init, insert, query functions
├── tools/
│   ├── __init__.py         # Exports all_tools list
│   ├── search_tickets.py
│   ├── filter_by_budget.py
│   ├── collect_passenger.py
│   ├── process_payment.py
│   ├── save_booking.py
│   ├── generate_receipt.py
│   └── send_email.py
├── agent/
│   ├── __init__.py
│   ├── state.py            # AgentState TypedDict
│   └── graph.py            # LangGraph StateGraph definition
├── backend/
│   ├── __init__.py
│   └── main.py             # FastAPI application
├── frontend/
│   └── app.py              # Streamlit chat UI
├── requirements.txt
├── .env.example
├── Dockerfile
└── README.md
```

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 3. Start the FastAPI backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Start the Streamlit frontend (new terminal)

```bash
streamlit run frontend/app.py
```

### 5. Open the app

Navigate to **http://localhost:8501** in your browser.

---

## Docker

```bash
docker build -t omnibook-ai .
docker run -p 8000:8000 -p 8501:8501 -e OPENAI_API_KEY=sk-... omnibook-ai
```

---

## API Endpoints

| Method | Endpoint               | Description                          |
|--------|------------------------|--------------------------------------|
| POST   | `/chat`                | Send message to booking agent        |
| GET    | `/receipt/{booking_id}`| Get receipt data for a booking       |
| DELETE | `/session/{session_id}`| Clear a chat session                 |
| GET    | `/health`              | Health check                         |

### POST /chat

```json
{
  "session_id": "abc123",
  "message": "Book a flight from New York to Los Angeles"
}
```

**Response:**
```json
{
  "response": "Here are the available flights...",
  "steps": ["Calling: search_tickets(...)", "Result: [...]", "..."]
}
```

---

## Tools

| Tool                        | Description                                    |
|-----------------------------|------------------------------------------------|
| `search_tickets`            | Search flights/trains/movies by criteria        |
| `filter_by_budget`          | Filter tickets by max price                     |
| `collect_passenger_details` | Validate passenger name, age, email, phone      |
| `process_payment_mock`      | Simulate payment, returns transaction ID        |
| `save_booking_to_db`        | Persist booking to SQLite                       |
| `generate_receipt`          | Generate formatted receipt from DB              |
| `send_email_confirmation`   | Mock email confirmation                         |

---

## Example Conversation

```
User: Book a flight from New York to Los Angeles

Agent: [Searches tickets] Here are the available flights:
  1. FL001 – SkyHigh Airways, 08:00-11:30, Economy, $250
  2. FL002 – SkyHigh Airways, 14:00-17:30, Business, $420
  Which one would you like? Do you have a budget preference?

User: Option 1 please. My name is John Doe, age 30,
      email john@email.com, phone 1234567890

Agent: [Validates details → Processes payment → Saves booking → Generates receipt]
  ✅ Booking confirmed! Booking #1 saved.
  Receipt and confirmation email sent to john@email.com.
```

---

## Environment Variables

| Variable        | Default          | Description                  |
|-----------------|------------------|------------------------------|
| `OPENAI_API_KEY`| *(required)*     | OpenAI API key               |
| `MODEL_NAME`    | `gpt-4o-mini`    | LLM model to use             |
| `DATABASE_PATH` | `omnibook.db`    | SQLite database file path    |
| `GMAIL_ENABLED` | `false`          | Enable real Gmail sending    |
| `BACKEND_URL`   | `localhost:8000`  | Backend URL for frontend     |
