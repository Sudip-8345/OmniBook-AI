import json
from langchain_core.tools import tool


@tool
def collect_passenger_details(name: str, age: int, email: str, phone: str) -> str:
    """Validate and collect passenger details for booking.
    All fields are required. Returns validation result."""

    errors = []

    if not name or len(name.strip()) < 2:
        errors.append("Name must be at least 2 characters")
    if age < 1 or age > 120:
        errors.append("Age must be between 1 and 120")
    if "@" not in email or "." not in email:
        errors.append("Invalid email address")
    if len(phone.replace(" ", "").replace("-", "").replace("+", "")) < 10:
        errors.append("Phone number must be at least 10 digits")

    if errors:
        return json.dumps({"status": "invalid", "errors": errors})

    return json.dumps({
        "status": "valid",
        "passenger": {
            "name": name.strip(),
            "age": age,
            "email": email.strip(),
            "phone": phone.strip(),
        },
    })
