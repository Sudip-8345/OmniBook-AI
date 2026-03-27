import json
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph

from agent.state import AgentState
from config import TICKETS_PATH
from tools import all_tools
from tools.collect_passenger import collect_passenger_details
from tools.filter_by_budget import filter_by_budget
from tools.search_tickets import search_tickets


SYSTEM_PROMPT = """You are OmniBook AI, an autonomous ticket booking agent. You help users book flights, trains, and movie tickets.

IMPORTANT: You MUST pause and wait for the user's reply at EACH step below. NEVER proceed to the next step without explicit user confirmation. Do only ONE step per turn, then STOP and wait.

UNDERSTANDING USER INPUT:
- CRITICAL: When a user says "at 1500", "under 2000", "within 1000", "for 500", "budget 1500", or any plain number, they ALWAYS mean a BUDGET/PRICE. Call filter_by_budget with that number as max_budget. NEVER pass a plain number as the date parameter.
- Examples of BUDGET (use filter_by_budget): "at 1500", "under 2000", "for 500", "within 1000", "budget 3000", just "1500"
- Examples of DATE (use search_tickets with date): "March 5", "2026-03-05", "5th March", "on March 5th", "tomorrow"
- A valid date MUST contain a month name or be in YYYY-MM-DD format. A plain number like 1500 is NEVER a date.
- If user does not mention a specific date, do NOT pass any date, search without date filter.

STEP 1 - SEARCH: When the user asks to book, use search_tickets to find options.
   If they mention a budget/price, use filter_by_budget instead.
   Then STOP, show the results to the user and ask them to pick one.
   WAIT for user response.

STEP 2 - SELECTION: After the user picks a ticket, confirm their selection with the ticket details and price.
   Then STOP, ask the user for their passenger details (name, age, email, phone) if not already provided.
   WAIT for user response.

STEP 3 - VALIDATE: Once the user provides passenger details, use collect_passenger_details to validate.
   Then STOP, show a booking summary (ticket + passenger + total price) and ask "Shall I proceed with payment?"
   WAIT for user response.

STEP 4 - PAYMENT & BOOKING: ONLY after the user explicitly confirms payment (says yes/confirm/proceed), do ALL of these in sequence:
   a) process_payment_mock
   b) save_booking_to_db
   c) generate_receipt
   d) send_email_confirmation
   Then show the receipt to the user.

RULES:
- NEVER call process_payment_mock, save_booking_to_db, generate_receipt, or send_email_confirmation without explicit user confirmation
- NEVER skip showing options and asking the user to choose
- NEVER bundle multiple steps, always STOP and WAIT after steps 1, 2, and 3
- If the user provides all info at once, you still must show the summary and ask for payment confirmation before proceeding
- For movies: use the city as 'origin' and 'N/A' as 'destination'
- Be helpful, concise, and guide the user through the booking process"""


CITY_PATTERN = re.compile(
    r"\bfrom\s+(?P<origin>[a-zA-Z ]+?)\s+to\s+(?P<destination>[a-zA-Z ]+?)(?:\s+on\b|\s+at\b|\s+under\b|\s+within\b|$)",
    re.IGNORECASE,
)
DATE_PATTERN = re.compile(r"\b(\d{4}-\d{2}-\d{2}|today|tomorrow)\b", re.IGNORECASE)
BUDGET_PATTERN = re.compile(
    r"\b(?:under|within|budget|for|at)\s*₹?\s*(\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)
MOVIE_CITY_PATTERN = re.compile(
    r"\bin\s+([a-zA-Z ]+?)(?:\s+on\b|\s+at\b|\s+under\b|\s+within\b|$)",
    re.IGNORECASE,
)
TICKET_TYPES = {
    "flight": "flight",
    "flights": "flight",
    "train": "train",
    "trains": "train",
    "movie": "movie",
    "movies": "movie",
}


def _load_ticket_data() -> dict:
    with open(TICKETS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_ticket_by_id(ticket_id: str) -> tuple[str, dict] | tuple[None, None]:
    data = _load_ticket_data()
    normalized = ticket_id.upper()
    for ticket_type, tickets in data.items():
        for ticket in tickets:
            if ticket.get("id", "").upper() == normalized:
                return ticket_type.rstrip("s"), ticket
    return None, None


def _extract_search_args(text: str) -> dict | None:
    """Extract a minimal search request for fallback execution."""
    lowered = text.lower()
    ticket_type = next((value for key, value in TICKET_TYPES.items() if key in lowered), "")

    route_match = CITY_PATTERN.search(text)
    origin = route_match.group("origin").strip(" .,!?") if route_match else ""
    destination = route_match.group("destination").strip(" .,!?") if route_match else ""

    if ticket_type == "movie" and not origin:
        movie_city = MOVIE_CITY_PATTERN.search(text)
        origin = movie_city.group(1).strip(" .,!?") if movie_city else ""
        destination = "N/A" if origin else ""

    date_match = DATE_PATTERN.search(text)
    budget_match = BUDGET_PATTERN.search(text)

    if not ticket_type:
        return None
    if ticket_type in {"flight", "train"} and not (origin and destination):
        return None
    if ticket_type == "movie" and not origin:
        return None

    return {
        "ticket_type": ticket_type,
        "origin": origin,
        "destination": destination,
        "date": date_match.group(1) if date_match else "",
        "max_budget": float(budget_match.group(1)) if budget_match else None,
    }


def _extract_ticket_selection(text: str) -> str | None:
    match = re.search(r"\b([A-Za-z]{2}\d{3})\b", text)
    if match:
        return match.group(1).upper()

    squashed = re.sub(r"[^A-Za-z0-9]", "", text).lower()
    typo_match = re.search(r"(fl|tr|mv)[a-z]*0*([0-9]{1,3})", squashed)
    if typo_match:
        return f"{typo_match.group(1).upper()}{int(typo_match.group(2)):03d}"

    fuzzy_match = re.search(r"\b([A-Za-z]{2,3})\s*0*([0-9]{2,3})\b", text)
    if fuzzy_match:
        return f"{fuzzy_match.group(1)[:2].upper()}{int(fuzzy_match.group(2)):03d}"
    return None


def _extract_passenger_details(text: str) -> dict | None:
    name_match = re.search(r"\bname\s*[:=-]?\s*([A-Za-z][A-Za-z .'-]{1,80})", text, re.IGNORECASE)
    age_match = re.search(r"\bage\s*[:=-]?\s*(\d{1,3})\b", text, re.IGNORECASE)
    email_match = re.search(r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", text)
    phone_match = re.search(r"(\+?\d[\d\s-]{8,}\d)", text)

    if not (name_match and age_match and email_match and phone_match):
        return None

    return {
        "name": name_match.group(1).strip(" ,."),
        "age": int(age_match.group(1)),
        "email": email_match.group(1),
        "phone": phone_match.group(1).strip(),
    }


def _format_search_results(tool_result: str, args: dict) -> str:
    """Turn JSON tool output into a short human-friendly list."""
    try:
        tickets = json.loads(tool_result)
    except json.JSONDecodeError:
        return tool_result

    if not tickets:
        return "No tickets found matching your criteria. Try broadening your search."

    lines = []
    for ticket in tickets:
        if args["ticket_type"] == "flight":
            lines.append(
                f"{ticket['id']}: {ticket['airline']} {ticket['origin']} -> {ticket['destination']} on {ticket['date']} "
                f"({ticket['departure']}-{ticket['arrival']}), {ticket['class']}, ₹{ticket['price']}"
            )
        elif args["ticket_type"] == "train":
            lines.append(
                f"{ticket['id']}: {ticket['operator']} {ticket['origin']} -> {ticket['destination']} on {ticket['date']} "
                f"({ticket['departure']}-{ticket['arrival']}), {ticket['class']}, ₹{ticket['price']}"
            )
        else:
            lines.append(
                f"{ticket['id']}: {ticket['title']} at {ticket['theater']}, {ticket['origin']} on {ticket['date']} "
                f"at {ticket['showtime']}, ₹{ticket['price']}"
            )

    return (
        f"Here are the available {args['ticket_type']} options:\n\n"
        + "\n".join(lines)
        + "\n\nPlease pick one by ID."
    )


def _format_selected_ticket(ticket_type: str, ticket: dict) -> str:
    if ticket_type == "flight":
        details = (
            f"Airline: {ticket['airline']}\n"
            f"Route: {ticket['origin']} -> {ticket['destination']}\n"
            f"Date: {ticket['date']}\n"
            f"Time: {ticket['departure']} - {ticket['arrival']}\n"
            f"Class: {ticket['class']}\n"
            f"Price: Rs. {ticket['price']}"
        )
    elif ticket_type == "train":
        details = (
            f"Operator: {ticket['operator']}\n"
            f"Route: {ticket['origin']} -> {ticket['destination']}\n"
            f"Date: {ticket['date']}\n"
            f"Time: {ticket['departure']} - {ticket['arrival']}\n"
            f"Class: {ticket['class']}\n"
            f"Price: Rs. {ticket['price']}"
        )
    else:
        details = (
            f"Title: {ticket['title']}\n"
            f"City: {ticket['origin']}\n"
            f"Theater: {ticket['theater']}\n"
            f"Date: {ticket['date']}\n"
            f"Showtime: {ticket['showtime']}\n"
            f"Price: Rs. {ticket['price']}"
        )

    return (
        f"You've selected {ticket['id']}.\n\n"
        f"{details}\n\n"
        "Please provide passenger details in this format:\n"
        "name: Your Name, age: 28, email: you@example.com, phone: +919999999999"
    )


def _format_passenger_validation(result_str: str, ticket: dict) -> str:
    try:
        result = json.loads(result_str)
    except json.JSONDecodeError:
        return result_str

    if result.get("status") != "valid":
        errors = result.get("errors", [])
        return "Passenger details look incomplete:\n" + "\n".join(f"- {err}" for err in errors)

    passenger = result["passenger"]
    return (
        "Booking summary:\n\n"
        f"Ticket: {ticket['id']}\n"
        f"From: {ticket.get('origin', '')}\n"
        f"To: {ticket.get('destination', 'N/A')}\n"
        f"Date: {ticket.get('date', '')}\n"
        f"Price: Rs. {ticket.get('price', '')}\n\n"
        f"Passenger: {passenger['name']}, age {passenger['age']}\n"
        f"Email: {passenger['email']}\n"
        f"Phone: {passenger['phone']}\n\n"
        "Shall I proceed with payment?"
    )


def _fallback_search_response(messages: list) -> tuple[AIMessage, list[str]] | None:
    """Recover from provider-side tool-call failures for search, selection, and validation."""
    last_human = next((m for m in reversed(messages) if isinstance(m, HumanMessage)), None)
    if not last_human or not isinstance(last_human.content, str):
        return None

    selection = _extract_ticket_selection(last_human.content)
    if selection:
        ticket_type, ticket = _find_ticket_by_id(selection)
        if ticket:
            return AIMessage(content=_format_selected_ticket(ticket_type, ticket)), [f"Fallback: selected ticket {selection}"]

    passenger = _extract_passenger_details(last_human.content)
    if passenger:
        for message in reversed(messages[:-1]):
            if isinstance(message, HumanMessage) and isinstance(message.content, str):
                selected = _extract_ticket_selection(message.content)
                if not selected:
                    continue
                ticket_type, ticket = _find_ticket_by_id(selected)
                if not ticket:
                    break
                result = collect_passenger_details.invoke(passenger)
                return AIMessage(content=_format_passenger_validation(str(result), ticket)), [
                    f"Fallback: collect_passenger_details({json.dumps(passenger)})"
                ]

    args = _extract_search_args(last_human.content)
    if not args:
        return None

    tool_args = {
        "ticket_type": args["ticket_type"],
        "origin": args["origin"],
        "destination": args["destination"],
        "date": args["date"],
    }

    if args["max_budget"] is not None:
        payload = {**tool_args, "max_budget": args["max_budget"]}
        tool_result = filter_by_budget.invoke(payload)
        step = f"Fallback: filter_by_budget({json.dumps(payload)})"
    else:
        tool_result = search_tickets.invoke(tool_args)
        step = f"Fallback: search_tickets({json.dumps(tool_args)})"

    return AIMessage(content=_format_search_results(str(tool_result), args)), [step]


def build_graph(api_key: str, model_name: str = "llama-3.3-70b-versatile"):
    """Build and compile the LangGraph booking agent."""

    llm = ChatGroq(model=model_name, temperature=0, api_key=api_key)
    llm_with_tools = llm.bind_tools(all_tools)
    tool_map = {t.name: t for t in all_tools}

    def agent_node(state: AgentState) -> dict:
        """LLM node that decides whether to reply or call a tool."""
        messages = list(state["messages"])

        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        try:
            response = llm_with_tools.invoke(messages)
        except Exception as e:
            error_text = str(e)
            if "tool_use_failed" in error_text or "Failed to call a function" in error_text:
                fallback = _fallback_search_response(messages)
                if fallback:
                    response, fallback_steps = fallback
                    return {"messages": [response], "steps": fallback_steps}
            raise

        new_steps = []
        if response.content:
            new_steps.append(f"Agent: {response.content[:300]}")
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tc in response.tool_calls:
                args_preview = json.dumps(tc["args"], default=str)[:150]
                new_steps.append(f"Calling: {tc['name']}({args_preview})")

        return {"messages": [response], "steps": new_steps}

    def tool_node(state: AgentState) -> dict:
        """Execute the tool calls requested by the agent."""
        last_msg = state["messages"][-1]
        tool_messages = []
        new_steps = []

        for tool_call in last_msg.tool_calls:
            name = tool_call["name"]
            args = tool_call["args"]

            if name in tool_map:
                try:
                    result = tool_map[name].invoke(args)
                    result_str = str(result)
                except Exception as e:
                    result_str = f"Error running {name}: {str(e)}"
            else:
                result_str = f"Tool '{name}' not found"

            tool_messages.append(
                ToolMessage(content=result_str, tool_call_id=tool_call["id"])
            )
            new_steps.append(f"Result [{name}]: {result_str[:200]}")

        return {"messages": tool_messages, "steps": new_steps}

    def should_continue(state: AgentState) -> str:
        """Route to tools if agent requested tool calls, otherwise end."""
        last_msg = state["messages"][-1]
        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
            return "tools"
        return END

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
