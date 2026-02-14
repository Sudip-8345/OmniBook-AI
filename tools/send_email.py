import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.tools import tool
from config import SMTP_EMAIL, SMTP_PASSWORD


@tool
def send_email_confirmation(recipient_email: str, booking_id: int, passenger_name: str) -> str:
    """Send a real booking confirmation email to the passenger via Gmail SMTP."""

    subject = f"OmniBook AI - Booking Confirmation #{booking_id}"
    body = (
        f"Dear {passenger_name},\n\n"
        f"Your booking #{booking_id} has been confirmed!\n\n"
        f"You can view your receipt at: http://localhost:8000/receipt/{booking_id}\n\n"
        f"Thank you for using OmniBook AI!\n\n"
        f"Best regards,\nOmniBook AI Team"
    )

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return json.dumps({
            "status": "skipped",
            "message": "SMTP credentials not configured. Email not sent.",
        })

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, recipient_email, msg.as_string())
        server.quit()

        return json.dumps({
            "status": "sent",
            "message": f"Confirmation email sent to {recipient_email}",
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to send email: {str(e)}",
        })
