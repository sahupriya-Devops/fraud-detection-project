import json
from datetime import datetime, timezone

from google.cloud import pubsub_v1
from google.cloud import bigquery


# ============================================================
# Configuration
# ============================================================

PROJECT_ID = "ashishandpriya"
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

    try:

        transaction = json.loads(message.data.decode("utf-8"))

        status, fraud_reason = detect_fraud(transaction)

        processed_at = datetime.now(timezone.utc).isoformat()

        # ----------------------------------------------------
        # Display transaction
        # ----------------------------------------------------

        print("\nTransaction received")
        print("--------------------")

        print(
            f"Transaction ID : "
            f"{transaction['transaction_id']}"
        )

        print(
            f"User ID        : "
            f"{transaction['user_id']}"
        )

        print(
            f"Amount         : "
            f"{transaction['amount']}"
        )

        print(
            f"Merchant       : "
            f"{transaction['merchant']}"
        )

        print(
            f"Location       : "
            f"{transaction['location']}"
        )

        print(f"Status         : {status}")
        print(f"Reason         : {fraud_reason}")

        # ----------------------------------------------------
        # Prepare BigQuery row
        # ----------------------------------------------------

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
            print("\nBigQuery insertion failed:")
            print(errors)

            message.nack()
            return

        print("\nBigQuery insertion successful!")

        message.ack()

    except Exception as e:

        print("\nError processing message:")
        print(e)

        message.nack()


# ============================================================
# Start Consumer
# ============================================================

print("Fraud detection consumer is running...")
print(f"Listening on: {subscription_path}")
print(f"BigQuery table: {table_id}")

streaming_pull_future = subscriber.subscribe(
    subscription_path,
    callback=callback
)


# ============================================================
# Keep Consumer Running
# ============================================================

try:

    streaming_pull_future.result()

except KeyboardInterrupt:

    streaming_pull_future.cancel()
    streaming_pull_future.result()