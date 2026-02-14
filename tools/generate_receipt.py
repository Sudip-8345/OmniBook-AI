from langchain_core.tools import tool
from database.db import get_receipt_data


@tool
def generate_receipt(booking_id: int) -> str:
    """Generate a formatted receipt for a completed booking.
    Use the booking_id returned from save_booking_to_db."""

    data = get_receipt_data(booking_id)

    if not data:
        return f"No booking found with ID #{booking_id}"

    receipt = f"""
========================================
     OMNIBOOK AI - BOOKING RECEIPT
========================================
Booking ID    : #{data['booking_id']}
Date Booked   : {data['created_at']}
Status        : {data['status'].upper()}
----------------------------------------
PASSENGER DETAILS
  Name        : {data['passenger_name']}
  Email       : {data['email']}
  Phone       : {data['phone']}
  Age         : {data['age']}
----------------------------------------
TICKET DETAILS
  Type        : {data['ticket_type'].upper()}
  Ticket ID   : {data['ticket_id']}
  From        : {data['origin']}
  To          : {data['destination']}
  Date        : {data['date']}
----------------------------------------
PAYMENT DETAILS
  Amount      : ${data['price']:.2f}
  Transaction : {data['transaction_id']}
  Pay Status  : {data['payment_status'].upper()}
========================================
 Thank you for booking with OmniBook AI!
========================================"""

    return receipt.strip()
