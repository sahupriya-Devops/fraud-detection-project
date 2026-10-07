import json
from datetime import datetime, timezone

from google.cloud import pubsub_v1
from google.cloud import bigquery


# ============================================================
# Configuration
# ============================================================

PROJECT_ID = "priya-509505"

# Main transaction subscription
SUBSCRIPTION_ID = "fraud-processor"

# Fraud alert topic
ALERT_TOPIC_ID = "fraud-alerts"

# BigQuery
BQ_DATASET = "fraud_detection"
BQ_TABLE = "transactions"


# ============================================================
# Clients
# ============================================================

# Pub/Sub subscriber client
subscriber = pubsub_v1.SubscriberClient()

# Pub/Sub publisher client
publisher = pubsub_v1.PublisherClient()

# BigQuery client
bigquery_client = bigquery.Client(
    project=PROJECT_ID
)


# ============================================================
# Pub/Sub Paths
# ============================================================

# Main transaction subscription
subscription_path = subscriber.subscription_path(
    PROJECT_ID,
    SUBSCRIPTION_ID
)

# Fraud alert topic
alert_topic_path = publisher.topic_path(
    PROJECT_ID,
    ALERT_TOPIC_ID
)


# ============================================================
# BigQuery Table
# ============================================================

table_id = (
    f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"
)


# ============================================================
# Fraud Detection Logic
# ============================================================

def detect_fraud(transaction):

    amount = float(
        transaction["amount"]
    )

    if amount > 10000:

        return (
            "FRAUD",
            "High transaction amount"
        )

    return (
        "LEGITIMATE",
        "Transaction appears normal"
    )


# ============================================================
# Publish Fraud Alert
# ============================================================

def publish_fraud_alert(
    transaction,
    fraud_reason,
    processed_at
):

    # --------------------------------------------------------
    # Create fraud alert payload
    # --------------------------------------------------------

    alert = {

        "transaction_id":
            transaction["transaction_id"],

        "user_id":
            transaction["user_id"],

        "amount":
            float(transaction["amount"]),

        "merchant":
            transaction["merchant"],

        "location":
            transaction["location"],

        "status":
            "FRAUD",

        "fraud_reason":
            fraud_reason,

        "detected_at":
            processed_at
    }

    # --------------------------------------------------------
    # Convert alert to JSON
    # --------------------------------------------------------

    alert_data = json.dumps(
        alert
    ).encode("utf-8")

    # --------------------------------------------------------
    # Publish to fraud-alerts topic
    # --------------------------------------------------------

    alert_future = publisher.publish(
        alert_topic_path,
        alert_data
    )

    # Wait for Pub/Sub publish confirmation
    alert_message_id = alert_future.result()

    print(
        "\nFraud alert published successfully!",
        flush=True
    )

    print(
        f"Alert Topic      : {ALERT_TOPIC_ID}",
        flush=True
    )

    print(
        f"Alert Message ID : {alert_message_id}",
        flush=True
    )

    return alert_message_id


# ============================================================
# Pub/Sub Message Handler
# ============================================================

def callback(message):

    received_at = datetime.now(
        timezone.utc
    ).isoformat()

    print(
        "\n" + "=" * 50,
        flush=True
    )

    print(
        "MESSAGE RECEIVED FROM PUB/SUB",
        flush=True
    )

    print(
        "=" * 50,
        flush=True
    )

    print(
        f"Pub/Sub Message ID : "
        f"{message.message_id}",
        flush=True
    )

    print(
        f"Received At        : "
        f"{received_at}",
        flush=True
    )

    try:

        # ----------------------------------------------------
        # Decode Pub/Sub message
        # ----------------------------------------------------

        transaction = json.loads(
            message.data.decode("utf-8")
        )

        # ----------------------------------------------------
        # Print Transaction
        # ----------------------------------------------------

        print(
            f"Transaction ID     : "
            f"{transaction['transaction_id']}",
            flush=True
        )

        print(
            f"User ID            : "
            f"{transaction['user_id']}",
            flush=True
        )

        print(
            f"Amount             : "
            f"{transaction['amount']}",
            flush=True
        )

        print(
            f"Merchant           : "
            f"{transaction['merchant']}",
            flush=True
        )

        print(
            f"Location           : "
            f"{transaction['location']}",
            flush=True
        )

        # ----------------------------------------------------
        # Fraud Detection
        # ----------------------------------------------------

        status, fraud_reason = detect_fraud(
            transaction
        )

        print(
            f"Status             : {status}",
            flush=True
        )

        print(
            f"Reason             : {fraud_reason}",
            flush=True
        )

        # ----------------------------------------------------
        # Processing Timestamp
        # ----------------------------------------------------

        processed_at = datetime.now(
            timezone.utc
        ).isoformat()

        # ----------------------------------------------------
        # Prepare BigQuery Row
        # ----------------------------------------------------

        row = {

            "transaction_id":
                transaction["transaction_id"],

            "user_id":
                transaction["user_id"],

            "amount":
                float(transaction["amount"]),

            "merchant":
                transaction["merchant"],

            "location":
                transaction["location"],

            "timestamp":
                transaction["timestamp"],

            "status":
                status,

            "fraud_reason":
                fraud_reason,

            "processed_at":
                processed_at
        }

        # ----------------------------------------------------
        # Insert Into BigQuery
        # ----------------------------------------------------

        errors = bigquery_client.insert_rows_json(
            table_id,
            [row]
        )

        if errors:

            print(
                "\nBigQuery insertion FAILED:",
                flush=True
            )

            print(
                errors,
                flush=True
            )

            print(
                "\nMessage will be NACKED.",
                flush=True
            )

            message.nack()

            return

        print(
            "\nBigQuery insertion successful!",
            flush=True
        )

        # ----------------------------------------------------
        # Publish Fraud Alert
        # ----------------------------------------------------
        #
        # Only FRAUD transactions are published to the
        # fraud-alerts topic.
        #
        # The email-alert service receives these messages
        # through the fraud-alert-processor subscription
        # and sends the Gmail notification.
        # ----------------------------------------------------

        if status == "FRAUD":

            try:

                publish_fraud_alert(
                    transaction,
                    fraud_reason,
                    processed_at
                )

            except Exception as alert_error:

                print(
                    "\nFRAUD ALERT PUBLISH FAILED:",
                    flush=True
                )

                print(
                    repr(alert_error),
                    flush=True
                )

                print(
                    "Message will be NACKED "
                    "because the fraud alert "
                    "was not published.",
                    flush=True
                )

                message.nack()

                return

        else:

            print(
                "\nNo fraud alert required.",
                flush=True
            )

        # ----------------------------------------------------
        # ACK Only After Complete Processing
        # ----------------------------------------------------
        #
        # The message is acknowledged only after:
        #
        # 1. Fraud detection completed
        # 2. BigQuery insertion succeeded
        # 3. Fraud alert was successfully published
        #    when the transaction was FRAUD
        #
        # ----------------------------------------------------

        ack_future = message.ack_with_response()

        ack_future.result()

        print(
            "Message acknowledged successfully.",
            flush=True
        )

        print(
            "=" * 50,
            flush=True
        )

    except Exception as e:

        print(
            "\nERROR PROCESSING MESSAGE:",
            flush=True
        )

        print(
            repr(e),
            flush=True
        )

        print(
            "Message will be NACKED.",
            flush=True
        )

        message.nack()


# ============================================================
# Start Consumer
# ============================================================

print(
    "\nFraud Detection Consumer is starting...",
    flush=True
)

print(
    f"Project       : {PROJECT_ID}",
    flush=True
)

print(
    f"Subscription  : {subscription_path}",
    flush=True
)

print(
    f"BigQuery      : {table_id}",
    flush=True
)

print(
    f"Alert Topic   : {alert_topic_path}",
    flush=True
)


# ============================================================
# Flow Control
# ============================================================

flow_control = pubsub_v1.types.FlowControl(
    max_messages=10
)


# ============================================================
# Start Streaming Pull
# ============================================================

streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=callback,
    flow_control=flow_control
)

print(
    "\nWaiting for transactions...\n",
    flush=True
)


# ============================================================
# Keep Consumer Alive
# ============================================================

try:

    streaming_pull_future.result()

except KeyboardInterrupt:

    print(
        "\nStopping consumer...",
        flush=True
    )

    streaming_pull_future.cancel()

    try:

        streaming_pull_future.result()

    except Exception:

        pass

    print(
        "Consumer stopped.",
        flush=True
    )

except Exception as e:

    print(
        "\nStreaming pull stopped unexpectedly:",
        flush=True
    )

    print(
        repr(e),
        flush=True
    )

    streaming_pull_future.cancel()