import json
from datetime import datetime, timezone

from google.cloud import pubsub_v1
from google.cloud import bigquery


# ============================================================
# Configuration
# ============================================================

PROJECT_ID = "priya-509505"
SUBSCRIPTION_ID = "fraud-processor"

BQ_DATASET = "fraud_detection"
BQ_TABLE = "transactions"


# ============================================================
# Clients
# ============================================================

subscriber = pubsub_v1.SubscriberClient()
bigquery_client = bigquery.Client(project=PROJECT_ID)

subscription_path = subscriber.subscription_path(
    PROJECT_ID,
    SUBSCRIPTION_ID
)

table_id = f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}"


# ============================================================
# Fraud Detection Logic
# ============================================================

def detect_fraud(transaction):

    amount = float(transaction["amount"])

    if amount > 10000:
        return "FRAUD", "High transaction amount"

    return "LEGITIMATE", "Transaction appears normal"


# ============================================================
# Pub/Sub Message Handler
# ============================================================

def callback(message):

    received_at = datetime.now(timezone.utc).isoformat()

    print("\n" + "=" * 50, flush=True)
    print("MESSAGE RECEIVED FROM PUB/SUB", flush=True)
    print("=" * 50, flush=True)

    print(
        f"Pub/Sub Message ID : {message.message_id}",
        flush=True
    )

    print(
        f"Received At        : {received_at}",
        flush=True
    )

    try:

        # ----------------------------------------------------
        # Decode Pub/Sub message
        # ----------------------------------------------------

        transaction = json.loads(
            message.data.decode("utf-8")
        )

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

        status, fraud_reason = detect_fraud(transaction)

        print(
            f"Status             : {status}",
            flush=True
        )

        print(
            f"Reason             : {fraud_reason}",
            flush=True
        )

        # ----------------------------------------------------
        # Prepare BigQuery row
        # ----------------------------------------------------

        processed_at = datetime.now(
            timezone.utc
        ).isoformat()

        row = {
            "transaction_id": transaction["transaction_id"],
            "user_id": transaction["user_id"],
            "amount": float(transaction["amount"]),
            "merchant": transaction["merchant"],
            "location": transaction["location"],
            "timestamp": transaction["timestamp"],
            "status": status,
            "fraud_reason": fraud_reason,
            "processed_at": processed_at
        }

        # ----------------------------------------------------
        # Insert into BigQuery
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
        # ACK only after successful processing
        # ----------------------------------------------------
        #
        # Exactly-once delivery requires waiting for the
        # acknowledgment result.
        #

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
    f"Project      : {PROJECT_ID}",
    flush=True
)

print(
    f"Subscription : {subscription_path}",
    flush=True
)

print(
    f"BigQuery     : {table_id}",
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