import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os
from email.utils import formataddr

logger = logging.getLogger(__name__)

RAW_FROM = os.getenv("GMAIL_FROM")  
APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
TO_EMAILS = os.getenv("GMAIL_TO", "")
RAW_REPLY_TO = os.getenv("GMAIL_REPLY_TO", RAW_FROM)

def parse_single(raw: str):
    """Parse a single 'email:name' string -> (email, formatted_addr)."""
    if not raw:
        return None, None
    if ":" in raw:
        email, name = raw.split(":", 1)
        return email.strip(), formataddr((name.strip(), email.strip()))
    return raw.strip(), raw.strip()

def parse_recipients(raw: str):
    """Parse multiple recipients from 'email:name,email2:name2,...'."""
    recipients = []
    for entry in raw.split(","):
        entry = entry.strip()
        if not entry:
            continue
        _, formatted = parse_single(entry)
        recipients.append(formatted)
    return recipients

# Parse FROM and REPLY-TO
FROM_EMAIL, FROM_ADDR = parse_single(RAW_FROM)
_, REPLY_TO_ADDR = parse_single(RAW_REPLY_TO)

def send_project_enquiry_email(enquiry: dict):
    """
    Send a nicely formatted HTML email for new project enquiries.
    Supports multiple recipients via comma-separated emails in GMAIL_TO.
    """
    subject = f"New Enquiry (Chatbot) from {enquiry.get('name','Unknown')}"

    recipients = parse_recipients(TO_EMAILS)

    if not recipients:
        logger.error("No recipients configured in GMAIL_TO")

    if not recipients:
        logger.error("No recipients configured in GMAIL_TO")
        return {"status_code": 400, "status_message": "No recipients configured"}


 
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background:#f5f5f5; padding:20px;">
    <div style="max-width:650px; margin:auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 2px 6px rgba(0,0,0,0.1);">
        
        <!-- Header -->
        <div style="text-align:center; padding:20px; border-bottom:1px solid #eee;">
        <img src="https://lollypop.design/wp-content/uploads/2023/01/lollypop-logo.png" 
            alt="Lollypop Design" style="max-width:150px; height:auto;">
        <h2 style="margin:20px 0 0; color:#333;">Yay!! We received a new enquiry.</h2>
        </div>

        <!-- Details Section -->
        <div style="padding:25px; line-height:1.6; color:#333;">
        <table style="width:100%; border-collapse:collapse;">
            <tr>
            <td style="font-weight:bold; width:160px; vertical-align:top;">Name:</td>
            <td>{enquiry.get('name','N/A')}</td>
            </tr>
            <tr>
            <td style="font-weight:bold; vertical-align:top;">Email:</td>
            <td><a href="mailto:{enquiry.get('email','N/A')}" style="color:#0073e6; text-decoration:none;">{enquiry.get('email','N/A')}</a></td>
            </tr>
            <tr>
            <td style="font-weight:bold; vertical-align:top;">Category:</td>
            <td>{enquiry.get('category','N/A')}</td>
            </tr>
            <tr>
            <td style="font-weight:bold; vertical-align:top;">Company Info:</td>
            <td style="white-space:pre-line;">{enquiry.get('company_info','N/A')}</td>
            </tr>
            <tr>
            <td style="font-weight:bold; vertical-align:top;">Conversation Summary:</td>
            <td style="white-space:pre-line;">{enquiry.get('summary','N/A')}</td>
            </tr>
        </table>
        </div>

        <!-- Footer -->
        <div style="background:#fafafa; padding:15px; text-align:center; font-size:12px; color:#777;">
        This is an automated notification from <b>Lollypop Design</b>.<br>
        </div>
    </div>
    </body>
    </html>
    """


    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = ", ".join(recipients)
        msg["Reply-To"] = REPLY_TO_ADDR

        msg.attach(MIMEText(html_body, "html"))

        # Send securely via Gmail 
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(FROM_EMAIL, APP_PASSWORD)
            server.sendmail(FROM_EMAIL, [r.split("<")[-1].strip(" >") for r in recipients], msg.as_string())

        logger.info(f"HTML email sent successfully to {recipients}")
        return {"status_code": 200, "status_message": f"Email sent to {recipients}"}

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"status_code": 500, "status_message": str(e)}
