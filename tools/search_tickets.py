import json
from langchain_core.tools import tool
from config import TICKETS_PATH


def _load_tickets():
    """Load ticket data from JSON file."""
    with open(TICKETS_PATH, "r") as f:
        return json.load(f)


@tool
def search_tickets(ticket_type: str, origin: str = "", destination: str = "", date: str = "") -> str:
    """Search for available tickets by type (flight, train, or movie).
    For movies, 'origin' is the city name. Date format: YYYY-MM-DD.
    Leave fields empty to see all available options for that type."""

    data = _load_tickets()

    # Normalize: "flight" -> "flights", "trains" -> "trains"
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

    if not results:
        return "No tickets found matching your criteria. Try broadening your search."

    return json.dumps(results, indent=2)
