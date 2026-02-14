import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.tools import tool
from config import SMTP_EMAIL, SMTP_PASSWORD
from database.db import get_receipt_data


def _build_html_email(booking_id, passenger_name):
    """Build a styled HTML email with full receipt details."""
    data = get_receipt_data(booking_id)

    if not data:
        return f"<p>Booking #{booking_id} confirmed for {passenger_name}.</p>"

    return f"""
    <html>
    <body style="margin:0; padding:0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f4f4f7;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f7; padding: 40px 0;">
        <tr>
          <td align="center">
            <table width="600" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08);">

              <!-- Header -->
              <tr>
                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 35px 40px; text-align: center;">
                  <h1 style="color: #ffffff; margin: 0; font-size: 28px;">✈️ OmniBook AI</h1>
                  <p style="color: #e0d4f7; margin: 8px 0 0; font-size: 14px;">Booking Confirmation</p>
                </td>
              </tr>

              <!-- Status Badge -->
              <tr>
                <td style="padding: 30px 40px 0; text-align: center;">
                  <span style="background: #d4edda; color: #155724; padding: 8px 24px; border-radius: 20px; font-weight: 600; font-size: 14px;">✅ CONFIRMED</span>
                </td>
              </tr>

              <!-- Greeting -->
              <tr>
                <td style="padding: 25px 40px 10px;">
                  <p style="font-size: 16px; color: #333;">Dear <strong>{data['passenger_name']}</strong>,</p>
                  <p style="font-size: 15px; color: #555; line-height: 1.6;">Your booking has been confirmed. Here are the details:</p>
                </td>
              </tr>

              <!-- Booking Details Card -->
              <tr>
                <td style="padding: 10px 40px;">
                  <table width="100%" style="background: #f8f9ff; border-radius: 10px; border: 1px solid #e8e8f0;" cellpadding="15" cellspacing="0">
                    <tr>
                      <td colspan="2" style="border-bottom: 1px solid #e8e8f0; padding: 15px 20px;">
                        <strong style="color: #667eea; font-size: 15px;">📋 Booking Details</strong>
                      </td>
                    </tr>
                    <tr>
                      <td style="color: #777; font-size: 14px; padding: 10px 20px; width: 40%;">Booking ID</td>
                      <td style="color: #333; font-size: 14px; font-weight: 600; padding: 10px 20px;">#{data['booking_id']}</td>
                    </tr>
                    <tr style="background: #ffffff;">
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">Type</td>
                      <td style="color: #333; font-size: 14px; font-weight: 600; padding: 10px 20px;">{data['ticket_type'].upper()}</td>
                    </tr>
                    <tr>
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">Ticket ID</td>
                      <td style="color: #333; font-size: 14px; font-weight: 600; padding: 10px 20px;">{data['ticket_id']}</td>
                    </tr>
                    <tr style="background: #ffffff;">
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">From</td>
                      <td style="color: #333; font-size: 14px; font-weight: 600; padding: 10px 20px;">{data['origin']}</td>
                    </tr>
                    <tr>
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">To</td>
                      <td style="color: #333; font-size: 14px; font-weight: 600; padding: 10px 20px;">{data['destination']}</td>
                    </tr>
                    <tr style="background: #ffffff;">
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">Date</td>
                      <td style="color: #333; font-size: 14px; font-weight: 600; padding: 10px 20px;">{data['date']}</td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Passenger Details -->
              <tr>
                <td style="padding: 15px 40px;">
                  <table width="100%" style="background: #fff8f0; border-radius: 10px; border: 1px solid #f0e0c8;" cellpadding="15" cellspacing="0">
                    <tr>
                      <td colspan="2" style="border-bottom: 1px solid #f0e0c8; padding: 15px 20px;">
                        <strong style="color: #e67e22; font-size: 15px;">👤 Passenger</strong>
                      </td>
                    </tr>
                    <tr>
                      <td style="color: #777; font-size: 14px; padding: 10px 20px; width: 40%;">Name</td>
                      <td style="color: #333; font-size: 14px; font-weight: 600; padding: 10px 20px;">{data['passenger_name']}</td>
                    </tr>
                    <tr style="background: #ffffff;">
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">Email</td>
                      <td style="color: #333; font-size: 14px; padding: 10px 20px;">{data['email']}</td>
                    </tr>
                    <tr>
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">Phone</td>
                      <td style="color: #333; font-size: 14px; padding: 10px 20px;">{data['phone']}</td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Payment -->
              <tr>
                <td style="padding: 5px 40px 15px;">
                  <table width="100%" style="background: #f0f9f4; border-radius: 10px; border: 1px solid #c8e6d0;" cellpadding="15" cellspacing="0">
                    <tr>
                      <td colspan="2" style="border-bottom: 1px solid #c8e6d0; padding: 15px 20px;">
                        <strong style="color: #27ae60; font-size: 15px;">💳 Payment</strong>
                      </td>
                    </tr>
                    <tr>
                      <td style="color: #777; font-size: 14px; padding: 10px 20px; width: 40%;">Amount</td>
                      <td style="color: #333; font-size: 20px; font-weight: 700; padding: 10px 20px;">${data['price']:.2f}</td>
                    </tr>
                    <tr style="background: #ffffff;">
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">Transaction ID</td>
                      <td style="color: #333; font-size: 13px; font-family: monospace; padding: 10px 20px;">{data['transaction_id']}</td>
                    </tr>
                    <tr>
                      <td style="color: #777; font-size: 14px; padding: 10px 20px;">Status</td>
                      <td style="padding: 10px 20px;"><span style="background: #d4edda; color: #155724; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 600;">{data['payment_status'].upper()}</span></td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="padding: 25px 40px 35px; text-align: center; border-top: 1px solid #eee;">
                  <p style="color: #999; font-size: 13px; margin: 0;">Thank you for booking with OmniBook AI!</p>
                  <p style="color: #bbb; font-size: 12px; margin: 8px 0 0;">This is an automated confirmation email.</p>
                </td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """


@tool
def send_email_confirmation(recipient_email: str, booking_id: int, passenger_name: str) -> str:
    """Send a styled HTML booking confirmation email with full receipt to the passenger via Gmail SMTP."""

    subject = f"OmniBook AI - Booking Confirmation #{booking_id}"
    html_body = _build_html_email(booking_id, passenger_name)

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return json.dumps({
            "status": "skipped",
            "message": "SMTP credentials not configured. Email not sent.",
        })

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"OmniBook AI <{SMTP_EMAIL}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html"))

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
