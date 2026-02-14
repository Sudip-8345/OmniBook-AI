from tools.search_tickets import search_tickets
from tools.filter_by_budget import filter_by_budget
from tools.collect_passenger import collect_passenger_details
from tools.process_payment import process_payment_mock
from tools.save_booking import save_booking_to_db
from tools.generate_receipt import generate_receipt
from tools.send_email import send_email_confirmation

all_tools = [
    search_tickets,
    filter_by_budget,
    collect_passenger_details,
    process_payment_mock,
    save_booking_to_db,
    generate_receipt,
    send_email_confirmation,
]
