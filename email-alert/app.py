import os
import json
import base64
import smtplib

from email.message import EmailMessage
from flask import Flask, request


# ============================================================
# Configuration
# ============================================================

SMTP_SERVER = os.environ.get(
    "SMTP_SERVER",
    "smtp.gmail.com"
)

SMTP_PORT = int(
    os.environ.get(
        "SMTP_PORT",
        "587"
    )
)

SMTP_USERNAME = os.environ["SMTP_USERNAME"]
SMTP_PASSWORD = os.environ["SMTP_PASSWORD"]

ALERT_FROM_EMAIL = os.environ["ALERT_FROM_EMAIL"]
ALERT_TO_EMAIL = os.environ["ALERT_TO_EMAIL"]


# ============================================================
# Flask Application
# ============================================================

app = Flask(__name__)


# ============================================================
# Send Fraud Alert Email
# ============================================================

def send_fraud_email(alert):

    transaction_id = alert.get(
        "transaction_id",
        "Unknown"
    )

    user_id = alert.get(
        "user_id",
        "Unknown"
    )

    amount = alert.get(
        "amount",
        "Unknown"
    )

    merchant = alert.get(
        "merchant",
        "Unknown"
    )

    location = alert.get(
        "location",
        "Unknown"
    )

    fraud_reason = alert.get(
        "fraud_reason",
        "Unknown"
    )

    detected_at = alert.get(
        "detected_at",
        "Unknown"
    )

    # --------------------------------------------------------
    # Create Email
    # --------------------------------------------------------

    message = EmailMessage()

    message["Subject"] = (
        "🚨 FRAUD ALERT - Suspicious Transaction Detected"
    )

    message["From"] = ALERT_FROM_EMAIL
    message["To"] = ALERT_TO_EMAIL

    body = f"""
Fraud Detection System
======================

A suspicious transaction has been detected.

Transaction Details
-------------------

Transaction ID : {transaction_id}
User ID        : {user_id}
Amount         : ₹{amount}
Merchant       : {merchant}
Location       : {location}

Fraud Status   : FRAUD
Reason         : {fraud_reason}

Detected At    : {detected_at}

Please review this transaction immediately.

This email was generated automatically by the
Fraud Detection System.
"""

    message.set_content(body)

    # --------------------------------------------------------
    # Connect to Gmail SMTP
    # --------------------------------------------------------

    with smtplib.SMTP(
        SMTP_SERVER,
        SMTP_PORT
    ) as server:

        server.starttls()

        server.login(
            SMTP_USERNAME,
            SMTP_PASSWORD
        )

        server.send_message(message)


# ============================================================
# Pub/Sub Push Handler
# ============================================================

@app.route("/", methods=["POST"])
def pubsub_handler():

    envelope = request.get_json(
        silent=True
    )

    if not envelope:

        print(
            "Invalid Pub/Sub message.",
            flush=True
        )

        return (
            "Invalid Pub/Sub message",
            400
        )

    # --------------------------------------------------------
    # Extract Pub/Sub Message
    # --------------------------------------------------------

    pubsub_message = envelope.get(
        "message"
    )

    if not pubsub_message:

        print(
            "Missing Pub/Sub message.",
            flush=True
        )

        return (
            "Missing Pub/Sub message",
            400
        )

    encoded_data = pubsub_message.get(
        "data"
    )

    if not encoded_data:

        print(
            "Missing Pub/Sub message data.",
            flush=True
        )

        return (
            "Missing message data",
            400
        )

    # --------------------------------------------------------
    # Decode Message
    # --------------------------------------------------------

    try:

        decoded_data = base64.b64decode(
            encoded_data
        ).decode("utf-8")

        alert = json.loads(
            decoded_data
        )

    except Exception as e:

        print(
            "\nFailed to decode Pub/Sub message:",
            flush=True
        )

        print(
            repr(e),
            flush=True
        )

        return (
            "Invalid message",
            400
        )

    # --------------------------------------------------------
    # Print Received Alert
    # --------------------------------------------------------

    print(
        "\n" + "=" * 60,
        flush=True
    )

    print(
        "FRAUD ALERT RECEIVED",
        flush=True
    )

    print(
        "=" * 60,
        flush=True
    )

    print(
        json.dumps(
            alert,
            indent=2
        ),
        flush=True
    )

    # --------------------------------------------------------
    # Process Only FRAUD Alerts
    # --------------------------------------------------------

    status = alert.get(
        "status",
        ""
    )

    if status != "FRAUD":

        print(
            "\nMessage is not a FRAUD transaction.",
            flush=True
        )

        print(
            "No email will be sent.",
            flush=True
        )

        return (
            "Not a fraud transaction",
            200
        )

    # --------------------------------------------------------
    # Send Fraud Email
    # --------------------------------------------------------

    try:

        send_fraud_email(
            alert
        )

        print(
            "\nFraud alert email sent successfully!",
            flush=True
        )

        print(
            f"To: {ALERT_TO_EMAIL}",
            flush=True
        )

        print(
            "=" * 60,
            flush=True
        )

        # HTTP 200 tells Pub/Sub that
        # the message was processed successfully.
        return (
            "Email sent successfully",
            200
        )

    except Exception as e:

        print(
            "\nFailed to send fraud alert email:",
            flush=True
        )

        print(
            repr(e),
            flush=True
        )

        # Non-2xx response tells Pub/Sub
        # to retry the message.
        return (
            "Failed to send email",
            500
        )


# ============================================================
# Health Check
# ============================================================

@app.route("/", methods=["GET"])
def health_check():

    return (
        "Fraud Alert Email Service is running.",
        200
    )


# ============================================================
# Application Entry Point
# ============================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            "8080"
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
    )