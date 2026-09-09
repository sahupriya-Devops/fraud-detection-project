import json
import random
import uuid
from datetime import datetime, timezone

from google.cloud import pubsub_v1


PROJECT_ID = "ashishandpriya"
TOPIC_ID = "fraud-events"


def generate_transaction():
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": f"USER{random.randint(1000, 9999)}",
        "amount": round(random.uniform(100, 20000), 2),
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publish_transaction():
    publisher = pubsub_v1.PublisherClient()

    topic_path = publisher.topic_path(
        PROJECT_ID,
        TOPIC_ID,
    )

    transaction = generate_transaction()

    message = json.dumps(transaction).encode("utf-8")

    future = publisher.publish(
        topic_path,
        message,
    )

    message_id = future.result()

    print("Transaction published successfully!")
    print(f"Message ID: {message_id}")
    print(f"Transaction: {transaction}")


if __name__ == "__main__":
    publish_transaction()