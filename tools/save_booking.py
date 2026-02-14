import json
from langchain_core.tools import tool
from database.db import save_user, save_booking, save_payment


@tool
def save_booking_to_db(
    passenger_name: str,
    passenger_email: str,
    passenger_phone: str,
    passenger_age: int,
    ticket_type: str,
    ticket_id: str,
    origin: str,
    destination: str,
    date: str,
    price: float,
    transaction_id: str,
) -> str:
    """Save a confirmed booking to the database.
    Call this after payment is processed successfully.
    Returns the booking ID for receipt generation."""

    try:
        user_id = save_user(passenger_name, passenger_email, passenger_phone, passenger_age)
        booking_id = save_booking(
            user_id, ticket_type, ticket_id, origin, destination, date, price, transaction_id
        )
        save_payment(booking_id, price, transaction_id, "completed")

        return json.dumps({
            "status": "saved",
            "booking_id": booking_id,
            "message": f"Booking #{booking_id} saved successfully for {passenger_name}",
        })
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})
