import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from utils.logger import logger


def handle_email(config, drive_link, date, mode="edge"):
    email_config = config["email"]
    sender_email = email_config["sender_email"]
    sender_password = email_config["sender_password"]
    receiver_emails = email_config["receiver_emails"]

    if mode == "star":
        subject = f"The Star Newspaper PDFs - {date}"
        body = f"Please find the link to today's Star newspaper PDFs below:\n\n{drive_link}"
    elif mode == "sun":
        subject = f"The Sun PDF - {date}"
        body = f"Please find the link to the latest The Sun Newspaper PDF below:\n\n{drive_link}"
    elif mode == "edge":
        subject = email_config.get("subject", f"Edge Magazine PDF - {date}")
        body = (
            email_config.get(
                "body", "Please find the link to the latest Edge Magazine PDF below:"
            )
            + f"\n\n{drive_link}"
        )

    if sender_email and sender_password and receiver_emails:
        return send_email(sender_email, sender_password, receiver_emails, subject, body)
    return False


def send_email(sender_email, sender_password, receiver_emails, subject, body):
    logger.info(f"Sending email to: {', '.join(receiver_emails)}")
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = sender_email
    msg["Bcc"] = ", ".join(receiver_emails)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        logger.info("Sending email...")
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        logger.info("Email sent")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False
