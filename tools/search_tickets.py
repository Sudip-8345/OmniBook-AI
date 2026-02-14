import json
import re
from langchain_core.tools import tool
from config import TICKETS_PATH


def _load_tickets():
    """Load ticket data from JSON file."""
    with open(TICKETS_PATH, "r") as f:
        return json.load(f)


def _is_valid_date(s):
    """Check if string matches YYYY-MM-DD format."""
    return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', s))


@tool
def search_tickets(ticket_type: str, origin: str = "", destination: str = "", date: str = "") -> str:
    """Search for available tickets by type (flight, train, or movie).
    For movies, 'origin' is the city name.
    IMPORTANT: 'date' must be in YYYY-MM-DD format ONLY. Do NOT pass budget/price numbers here.
    If the user mentions a price/budget number, use filter_by_budget tool instead."""

    data = _load_tickets()

    type_key = ticket_type.lower().rstrip("s") + "s"
    if type_key not in data:
        return f"Unknown ticket type '{ticket_type}'. Choose from: flight, train, movie."

    results = data[type_key]

    if origin:
        results = [t for t in results if origin.lower() in t.get("origin", "").lower()]
    if destination:
        results = [t for t in results if destination.lower() in t.get("destination", "").lower()]

    # Only filter by date if it's a valid YYYY-MM-DD format, otherwise ignore it
    if date:
        if _is_valid_date(date):
            results = [t for t in results if t.get("date", "") == date]
        else:
            # If a number was passed as date, it's likely a budget — hint the agent
            try:
                budget = float(date)
                filtered = [t for t in results if t.get("price", 0) <= budget]
                if filtered:
                    results = filtered
                    return json.dumps(results, indent=2) + f"\n\n(Note: Showing results within budget of {budget}. The value '{date}' was treated as a budget, not a date.)"
            except ValueError:
                pass  # Not a number either, just ignore the date filter

    if not results:
        return "No tickets found matching your criteria. Try broadening your search."

    return json.dumps(results, indent=2)

    return json.dumps(results, indent=2)
