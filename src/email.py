import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from utils import logger


def send_email(sender_email, sender_password, receiver_emails, subject, body):
    logger.info(f"Sending email to: {', '.join(receiver_emails)}")
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = ", ".join(receiver_emails)
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
