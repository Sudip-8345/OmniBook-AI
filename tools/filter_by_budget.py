import json
from langchain_core.tools import tool
from config import TICKETS_PATH


@tool
def filter_by_budget(ticket_type: str, max_budget: float, origin: str = "", destination: str = "", date: str = "") -> str:
    """Filter available tickets by maximum budget.
    Returns only tickets with price <= max_budget.
    ticket_type: flight, train, or movie. max_budget: maximum price in INR (Indian Rupees)."""

    with open(TICKETS_PATH, "r") as f:
        data = json.load(f)

    type_key = ticket_type.lower().rstrip("s") + "s"
    if type_key not in data:
        return f"Unknown ticket type '{ticket_type}'. Choose from: flight, train, movie."

    results = data[type_key]

    if origin:
        results = [t for t in results if origin.lower() in t.get("origin", "").lower()]
    if destination:
        results = [t for t in results if destination.lower() in t.get("destination", "").lower()]
    if date:
        results = [t for t in results if t.get("date", "") == date]

    results = [t for t in results if t.get("price", 0) <= max_budget]

    if not results:
        return f"No tickets found within budget of \u20b9{max_budget:.2f}. Try increasing your budget."

    return json.dumps(results, indent=2)
