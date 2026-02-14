import operator
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State schema for the booking agent graph."""
    messages: Annotated[list, add_messages]
    steps: Annotated[list, operator.add]
