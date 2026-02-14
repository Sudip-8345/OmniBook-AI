import json
import uuid
from langchain_core.tools import tool


@tool
def process_payment_mock(amount: float, passenger_name: str, passenger_email: str) -> str:
    """Process a mock payment for ticket booking.
    Returns a transaction ID on success. No real charges are made."""

    if amount <= 0:
        return json.dumps({"status": "failed", "error": "Amount must be greater than zero"})

    transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

    return json.dumps({
        "status": "success",
        "transaction_id": transaction_id,
        "amount_charged": amount,
        "passenger_name": passenger_name,
        "message": f"Payment of \u20b9{amount:.2f} processed successfully for {passenger_name}",
    })
