import json
import random
import time
import uuid
from datetime import datetime, timezone

from google.cloud import pubsub_v1


# ============================================================
# Configuration
# ============================================================

PROJECT_ID = "priya-509505"
TOPIC_ID = "fraud-events"

# Time between transactions
PUBLISH_INTERVAL = 5


# ============================================================
# Pub/Sub Publisher
# ============================================================

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    PROJECT_ID,
    TOPIC_ID
)


# ============================================================
# Generate Transaction
# ============================================================

def generate_transaction():

    return {
        "transaction_id": str(uuid.uuid4()),

        "user_id": (
            f"USER{random.randint(1000, 9999)}"
        ),

        "amount": round(
            random.uniform(100, 20000),
            2
        ),

        "merchant": random.choice(
            [
                "Amazon",
                "Walmart",
                "Electronics Store",
                "Grocery Store",
                "Online Shop",
            ]
        ),

        "location": random.choice(
            [
                "Delhi",
                "Mumbai",
                "Bangalore",
                "Chandigarh",
                "Hyderabad",
            ]
        ),

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }


# ============================================================
# Publish Transaction
# ============================================================

def publish_transaction():

    transaction = generate_transaction()

    message = json.dumps(
        transaction
    ).encode("utf-8")

    future = publisher.publish(
        topic_path,
        message
    )

    message_id = future.result()

    print(
        "\n" + "=" * 60,
        flush=True
    )

    print(
        "TRANSACTION PUBLISHED",
        flush=True
    )

    print(
        "=" * 60,
        flush=True
    )

    print(
        f"Message ID   : {message_id}",
        flush=True
    )

    print(
        f"Transaction ID: {transaction['transaction_id']}",
        flush=True
    )

    print(
        f"User ID      : {transaction['user_id']}",
        flush=True
    )

    print(
        f"Amount       : ₹{transaction['amount']}",
        flush=True
    )

    print(
        f"Merchant     : {transaction['merchant']}",
        flush=True
    )

    print(
        f"Location     : {transaction['location']}",
        flush=True
    )

    print(
        f"Timestamp    : {transaction['timestamp']}",
        flush=True
    )

    print(
        "=" * 60,
        flush=True
    )


# ============================================================
# Start Continuous Producer
# ============================================================

def start_producer():

    print(
        "\nFraud Detection Producer is running...",
        flush=True
    )

    print(
        f"Project  : {PROJECT_ID}",
        flush=True
    )

    print(
        f"Topic    : {TOPIC_ID}",
        flush=True
    )

    print(
        f"Interval : {PUBLISH_INTERVAL} seconds",
        flush=True
    )

    print(
        "\nPress CTRL+C to stop the producer.\n",
        flush=True
    )

    while True:

        try:

            publish_transaction()

            print(
                f"\nWaiting {PUBLISH_INTERVAL} seconds...",
                flush=True
            )

            time.sleep(
                PUBLISH_INTERVAL
            )

        except Exception as error:

            print(
                "\nERROR PUBLISHING TRANSACTION:",
                flush=True
            )

            print(
                repr(error),
                flush=True
            )

            print(
                "\nRetrying in 5 seconds...",
                flush=True
            )

            time.sleep(5)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":

    try:

        start_producer()

    except KeyboardInterrupt:

        print(
            "\n\nProducer stopped by user.",
            flush=True
        )