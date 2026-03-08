"""Send the weekly flyer email via Gmail."""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")


def send_flyer_email(html: str, to_email: str | None = None) -> bool:
    """Send the HTML flyer via Gmail SMTP.

    Requires GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env.
    Get an app password at: https://myaccount.google.com/apppasswords
    """
    gmail_addr = os.environ.get("GMAIL_ADDRESS", "")
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "")
    recipient = to_email or gmail_addr  # default: send to yourself

    if not gmail_addr or not gmail_pass:
        print("Error: GMAIL_ADDRESS and GMAIL_APP_PASSWORD not set in .env")
        print("  Get an app password at: https://myaccount.google.com/apppasswords")
        return False

    today = date.today().strftime("%B %d, %Y")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Meat Scout — Best Deals for {today}"
    msg["From"] = f"Meat Scout <{gmail_addr}>"
    msg["To"] = recipient

    # Plain text fallback
    text_part = MIMEText(
        f"Meat Scout Weekly Deals — {today}\n\n"
        "Your HTML email client couldn't render this flyer.\n"
        "Run: python main.py  to see deals in your terminal.",
        "plain",
    )

    # HTML flyer
    html_part = MIMEText(html, "html")

    msg.attach(text_part)
    msg.attach(html_part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_addr, gmail_pass)
            server.sendmail(gmail_addr, recipient, msg.as_string())
        print(f"Flyer sent to {recipient}")
        return True
    except smtplib.SMTPException as e:
        print(f"Email failed: {e}")
        return False
