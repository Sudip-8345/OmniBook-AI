import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from agent.state import AgentState
from tools import all_tools


SYSTEM_PROMPT = """You are OmniBook AI, an autonomous ticket booking agent. You help users book flights, trains, and movie tickets.

IMPORTANT: You MUST pause and wait for the user's reply at EACH step below. NEVER proceed to the next step without explicit user confirmation. Do only ONE step per turn, then STOP and wait.

UNDERSTANDING USER INPUT:
- When a user says "at 1500", "under 2000", "within 1000", "for 500", "budget 1500" etc., they mean a BUDGET/PRICE, NOT a date. Use filter_by_budget with that number as max_budget.
- Dates are ONLY in formats like "March 5", "2026-03-05", "5th March", "tomorrow", etc.
- If the user does not mention a specific date, search without a date filter to show all available options.
- Prices are in INR (Indian Rupees) for this system.

STEP 1 - SEARCH: When the user asks to book, use search_tickets to find options.
   If they mention a budget/price, use filter_by_budget instead.
   Then STOP — show the results to the user and ask them to pick one.
   WAIT for user response.

STEP 2 - SELECTION: After the user picks a ticket, confirm their selection with the ticket details and price.
   Then STOP — ask the user for their passenger details (name, age, email, phone) if not already provided.
   WAIT for user response.

STEP 3 - VALIDATE: Once the user provides passenger details, use collect_passenger_details to validate.
   Then STOP — show a booking summary (ticket + passenger + total price) and ask "Shall I proceed with payment?"
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
- NEVER bundle multiple steps — always STOP and WAIT after steps 1, 2, and 3
- If the user provides all info at once, you still must show the summary and ask for payment confirmation before proceeding
- For movies: use the city as 'origin' and 'N/A' as 'destination'
- Be helpful, concise, and guide the user through the booking process"""


def build_graph(api_key: str, model_name: str = "llama-3.3-70b-versatile"):
    """Build and compile the LangGraph booking agent."""

    llm = ChatGroq(model=model_name, temperature=0, api_key=api_key)
    llm_with_tools = llm.bind_tools(all_tools)
    tool_map = {t.name: t for t in all_tools}

    def agent_node(state: AgentState) -> dict:
        """LLM agent node — decides next action or responds to user."""
        messages = list(state["messages"])

        # Inject system prompt if not present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

        response = llm_with_tools.invoke(messages)

        # Track reasoning steps
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

    # Assemble the graph
    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()
