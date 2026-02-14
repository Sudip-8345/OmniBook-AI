# OmniBook AI

Autonomous ticket booking agent for flights, trains, and movie tickets. Uses a LangGraph tool-calling agent with Groq LLM, Streamlit chat UI, FastAPI backend, and SQLite storage. Sends styled HTML confirmation emails via Gmail SMTP.

## Wanna try it ?
Click here - [Streamlit](https://omnibook-ai-234.streamlit.app/)

## Tech Stack

- LangGraph (agent orchestration)
- Groq / Llama 3.3 70B (LLM)
- FastAPI (REST backend)
- Streamlit (chat frontend with streaming)
- SQLite (users, bookings, payments)
- Gmail SMTP (HTML confirmation emails)

## Project Structure

```
OmniBook-AI/
  config.py                 - environment config
  data/tickets.json         - dummy ticket data
  database/db.py            - SQLite operations
  tools/
    search_tickets.py       - search by type/origin/destination/date
    filter_by_budget.py     - filter by max price
    collect_passenger.py    - validate passenger details
    process_payment.py      - mock payment processing
    save_booking.py         - persist booking to DB
    generate_receipt.py     - generate text receipt
    send_email.py           - send HTML email via SMTP
  agent/
    state.py                - agent state schema
    graph.py                - LangGraph state graph
  backend/main.py           - FastAPI app
  frontend/app.py           - Streamlit chat UI
```

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```
GROQ_API_KEY=your-groq-api-key
MODEL_NAME=llama-3.3-70b-versatile
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Run Locally

Start the backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

Start the frontend (separate terminal):

```bash
streamlit run frontend/app.py
```

Open http://localhost:8501.

## Deploy to Streamlit Cloud

1. Push the repo to GitHub
2. Go to share.streamlit.io and create a new app
3. Set main file path to `frontend/app.py`
4. Add secrets in Settings > Secrets:

```toml
GROQ_API_KEY = "your-key"
MODEL_NAME = "llama-3.3-70b-versatile"
SMTP_EMAIL = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"
```

## Docker

```bash
docker build -t omnibook-ai .
docker run -p 8000:8000 -p 8501:8501 --env-file .env omnibook-ai
```

## API Endpoints

| Method | Endpoint               | Description                  |
|--------|------------------------|------------------------------|
| POST   | /chat                  | Send message to agent        |
| GET    | /receipt/{booking_id}  | Get receipt for a booking    |
| DELETE | /session/{session_id}  | Clear a chat session         |
| GET    | /health                | Health check                 |

## Agent Flow

1. User requests a booking
2. Agent searches available tickets and presents options
3. User selects a ticket
4. Agent asks for passenger details (name, age, email, phone)
5. Agent validates details and shows a booking summary
6. User confirms payment
7. Agent processes payment, saves booking, generates receipt, and sends HTML confirmation email

The agent pauses at each step and waits for user confirmation before proceeding.
