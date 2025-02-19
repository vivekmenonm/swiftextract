import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

# ✅ Load SMTP settings from .env
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

def send_email_verification(email, verification_link):
    """ Sends a verification email to the user """
    try:
        msg = EmailMessage()
        msg["Subject"] = "Verify Your Email - SwiftExtract AI"
        msg["From"] = SMTP_USER
        msg["To"] = email
        msg.set_content(f"""
        Dear user,

        Click the link below to verify your email:

        {verification_link}

        This link will expire in 24 hours.

        Best,
        SwiftExtract AI
        """)

        print("🔹 Connecting to SMTP server...")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)  # Add timeout

        print("🔹 Identifying to server...")
        server.ehlo()  # Must run before starttls()

        print("🔹 Starting TLS encryption...")
        server.starttls()

        print("🔹 Identifying again after TLS...")
        server.ehlo()  # Must run again after starttls()

        print("🔹 Logging into SMTP server...")
        server.login(SMTP_USER, SMTP_PASSWORD)

        print("🔹 Sending email...")
        server.send_message(msg)  # Send email

        print(f"✅ Verification email sent to {email}")
        server.quit()  # Close the connection
        return True

    except Exception as e:
        print(f"🚨 Error sending email: {e}")
        return False