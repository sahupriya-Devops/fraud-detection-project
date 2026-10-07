# Automated Real-Time Fraud Detection System on GCP

## Project Overview

This project implements an automated real-time fraud detection system using Google Cloud Platform (GCP).

The system automatically generates e-commerce transactions, publishes them to Google Cloud Pub/Sub, processes them using a Dockerized Python consumer, detects potentially fraudulent transactions, stores transaction results in BigQuery, and sends email alerts for fraudulent transactions through a Cloud Run service.

---

## Architecture

```text
Automated Producer
      |
      v
Google Pub/Sub
fraud-events
      |
      v
fraud-processor
      |
      v
Dockerized Consumer
consumer.py
      |
      +----------------------+
      |                      |
      v                      v
  BigQuery              Fraud Detection
 transactions                 |
                              | FRAUD
                              v
                         fraud-alerts
                              |
                              v
                    fraud-alert-processor
                              |
                              v
                          Cloud Run
                     fraud-email-alert
                              |
                              v
                         Gmail Alert
```

---

## Technologies Used

- Python
- Google Cloud Pub/Sub
- Google BigQuery
- Google Cloud Run
- Google Artifact Registry
- Google Secret Manager
- Docker
- Terraform
- Google Cloud CLI
- Gmail SMTP
- Windows Batch Scripts

---

# Project Structure

The project uses a single root directory. The consumer is **not** inside a separate `consumer` folder.

```text
fraud-detection-project/
│
├── email-alert/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── producer/
│   ├── __pycache__/
│   ├── .venv/
│   ├── consumer.py
│   ├── Dockerfile
│   ├── producer.py
│   ├── requirements.txt
│   ├── start_consumer.bat
│   └── start_producer.bat
│
├── terraform/
│   ├── .terraform/
│   ├── .terraform.lock.hcl
│   ├── artifact_registry.tf
│   ├── bigquery.tf
│   ├── cloud_run.tf
│   ├── email_alert_build.tf
│   ├── main.tf
│   ├── provider.tf
│   ├── pubsub.tf
│   ├── secret.tf
│   ├── terraform.tfstate
│   ├── terraform.tfstate.backup
│   └── variables.tf
│
├── .gitignore
├── fraud-consumer-key.json
└── README.md
```

> **Important:** `.venv/`, `.terraform/`, Terraform state files, and credential/key files should normally be excluded from Git using `.gitignore`. Never commit service-account private keys or other secrets to GitHub.

---

# 1. Automated Transaction Producer

The producer is responsible for continuously generating transaction events.

File:

```text
producer/producer.py
```

The producer generates:

- Transaction ID
- User ID
- Amount
- Merchant
- Location
- Timestamp

Example transaction:

```json
{
  "transaction_id": "88903036-a272-45e7-b536-b975ff60f39e",
  "user_id": "USER2817",
  "amount": 10986.70,
  "merchant": "Amazon",
  "location": "Mumbai",
  "timestamp": "2026-10-07T15:00:47.415071+00:00"
}
```

The producer publishes transactions to:

```text
fraud-events
```

## Start Producer

From the `producer` directory:

```cmd
start_producer.bat
```

The producer automatically generates transactions at the configured interval.

Example:

```text
Fraud Detection Producer is running...
Project  : priya-509505
Topic    : fraud-events
Interval : 5 seconds
```

---

# 2. Google Cloud Pub/Sub

Pub/Sub acts as the messaging layer between the transaction producer and the fraud detection consumer.

## Main Topic

```text
fraud-events
```

## Main Subscription

```text
fraud-processor
```

Flow:

```text
producer.py
    |
    v
fraud-events
    |
    v
fraud-processor
    |
    v
consumer.py
```

---

# 3. Fraud Detection Consumer

The consumer is located directly inside the `producer` directory.

File:

```text
producer/consumer.py
```

There is **no separate consumer folder** in this project.

The consumer performs the following operations:

1. Receives transaction messages from Pub/Sub.
2. Decodes the JSON transaction.
3. Applies fraud detection logic.
4. Inserts the transaction into BigQuery.
5. Publishes a fraud alert when the transaction is fraudulent.
6. Acknowledges the Pub/Sub message after successful processing.

---

# 4. Fraud Detection Logic

The current fraud detection rule is based on transaction amount.

```python
if amount > 10000:
    return "FRAUD", "High transaction amount"

return "LEGITIMATE", "Transaction appears normal"
```

Therefore:

```text
Amount > ₹10,000
       |
       v
     FRAUD
       |
       +------------------+
       |                  |
       v                  v
   BigQuery          fraud-alerts
                          |
                          v
                     Email Alert
```

Transactions of ₹10,000 or less are classified as:

```text
LEGITIMATE
```

---

# 5. Automated Consumer Startup

The consumer is started using:

```text
producer/start_consumer.bat
```

The batch file automatically:

1. Checks Docker.
2. Checks Google Cloud CLI.
3. Configures the GCP project.
4. Checks the Pub/Sub topic.
5. Checks the Pub/Sub subscription.
6. Builds the Docker image.
7. Removes an existing consumer container if necessary.
8. Starts the Docker consumer container.
9. Displays the consumer logs.

## Start Consumer

From the `producer` directory:

```cmd
start_consumer.bat
```

The Docker container is:

```text
fraud-consumer
```

The Docker image is:

```text
fraud-detection-consumer
```

---

# 6. Dockerized Consumer

The consumer runs inside Docker rather than being executed manually with:

```cmd
python consumer.py
```

This makes the consumer easier to start consistently and provides a repeatable runtime environment.

Check the running container:

```cmd
docker ps
```

Expected:

```text
fraud-consumer
```

View logs:

```cmd
docker logs --tail 50 fraud-consumer
```

Follow logs continuously:

```cmd
docker logs -f fraud-consumer
```

Check container status:

```cmd
docker inspect -f "{{.State.Status}}" fraud-consumer
```

Check restart count:

```cmd
docker inspect -f "{{.RestartCount}}" fraud-consumer
```

Expected stable state:

```text
running
```

---

# 7. BigQuery

All processed transactions are stored in BigQuery.

## GCP Project

```text
priya-509505
```

## Dataset

```text
fraud_detection
```

## Table

```text
transactions
```

Full table:

```text
priya-509505.fraud_detection.transactions
```

The table stores fields including:

```text
transaction_id
user_id
amount
merchant
location
timestamp
status
fraud_reason
processed_at
```

---

# 8. BigQuery Processing Flow

Every transaction is inserted into BigQuery.

For example:

```text
Transaction
     |
     v
Fraud Detection
     |
     +----------------------+
     |                      |
     v                      v
LEGITIMATE                FRAUD
     |                      |
     v                      v
BigQuery                 BigQuery
                            |
                            v
                       fraud-alerts
```

---

# 9. Fraud Alert Topic

Fraudulent transactions are published to a separate Pub/Sub topic:

```text
fraud-alerts
```

The consumer publishes an alert only when:

```text
status == FRAUD
```

The alert contains information such as:

```text
transaction_id
user_id
amount
merchant
location
status
fraud_reason
detected_at
```

---

# 10. Cloud Run Email Alert Service

The email service is located in:

```text
email-alert/
```

Files:

```text
email-alert/
├── app.py
├── Dockerfile
└── requirements.txt
```

The service is deployed to Google Cloud Run.

## Service Name

```text
fraud-email-alert
```

## Region

```text
asia-south1
```

The Cloud Run service receives fraud alert messages and sends email notifications.

---

# 11. Pub/Sub Push Subscription

The fraud alert topic is connected to the Cloud Run email service through:

```text
fraud-alert-processor
```

Topic:

```text
fraud-alerts
```

Push endpoint:

```text
https://fraud-email-alert-nmuex6l77a-el.a.run.app
```

The subscription is expected to be:

```text
ACTIVE
```

Flow:

```text
consumer.py
    |
    | FRAUD
    v
fraud-alerts
    |
    v
fraud-alert-processor
    |
    v
Cloud Run
fraud-email-alert
    |
    v
Gmail
```

---

# 12. Email Alert

When a fraudulent transaction is detected, the system automatically sends an email.

Example:

```text
FRAUD ALERT - Suspicious Transaction Detected

Transaction ID : c3037d66-278f-4e08-b10b-36507c6cb226
User ID        : USER1832
Amount         : ₹13090.76
Merchant       : Amazon
Location       : Mumbai
Status         : FRAUD
Reason         : High transaction amount
```

The email service uses Gmail SMTP.

```text
SMTP Server : smtp.gmail.com
SMTP Port   : 587
```

The SMTP password is provided through Google Secret Manager rather than being stored directly in the application code.

---

# 13. Terraform

Terraform is used to manage the GCP infrastructure.

Terraform files are located in:

```text
terraform/
```

The project contains Terraform configuration for infrastructure such as:

```text
Artifact Registry
BigQuery
Cloud Run
Pub/Sub
Secret Manager
Provider configuration
Variables
```

Typical Terraform commands:

```cmd
terraform init
```

```cmd
terraform plan
```

```cmd
terraform apply
```

---

# 14. Artifact Registry

The Docker image used by the Cloud Run email service is stored in Google Artifact Registry.

Example image:

```text
asia-south1-docker.pkg.dev/priya-509505/fraud-email-alert/fraud-email-alert:latest
```

Cloud Run uses this image to run the email alert service.

---

# 15. Secret Manager

The Gmail SMTP password is stored securely using Google Secret Manager.

Cloud Run receives the secret as an environment secret instead of exposing the password in the source code.

This prevents credentials from being committed to GitHub.

---

# 16. Complete End-to-End Workflow

```text
                    +---------------------+
                    |  Automated Producer |
                    |    producer.py      |
                    +----------+----------+
                               |
                               | Publish
                               v
                    +---------------------+
                    |   Pub/Sub Topic     |
                    |    fraud-events     |
                    +----------+----------+
                               |
                               v
                    +---------------------+
                    |    Subscription     |
                    |  fraud-processor    |
                    +----------+----------+
                               |
                               v
                    +---------------------+
                    | Docker Consumer     |
                    |   consumer.py       |
                    +----------+----------+
                               |
                    +----------+----------+
                    |                     |
                    v                     v
             +-------------+       +-------------+
             |  BigQuery   |       | Fraud Check |
             | transactions|       +------+------+
             +-------------+              |
                                   +------+------+
                                   |             |
                              LEGITIMATE        FRAUD
                                   |             |
                                   v             v
                               BigQuery      BigQuery
                                                 |
                                                 v
                                          +-------------+
                                          | fraud-alerts|
                                          +------+------+
                                                 |
                                                 v
                                       +-------------------+
                                       | fraud-alert-      |
                                       | processor         |
                                       +---------+---------+
                                                 |
                                                 v
                                       +-------------------+
                                       | Cloud Run         |
                                       | fraud-email-alert |
                                       +---------+---------+
                                                 |
                                                 v
                                           Gmail Alert
```

---

# 17. Verification Commands

## Check BigQuery Transaction Count

```cmd
bq query --use_legacy_sql=false --project_id=priya-509505 "SELECT COUNT(*) AS total_transactions FROM `priya-509505.fraud_detection.transactions`"
```

## View Recent Transactions

```cmd
bq query --use_legacy_sql=false --project_id=priya-509505 "SELECT transaction_id, user_id, amount, merchant, location, status, fraud_reason, timestamp, processed_at FROM `priya-509505.fraud_detection.transactions` ORDER BY processed_at DESC LIMIT 10"
```

## View Fraud Statistics

```cmd
bq query --use_legacy_sql=false --project_id=priya-509505 "SELECT status, COUNT(*) AS transaction_count, ROUND(SUM(amount),2) AS total_amount FROM `priya-509505.fraud_detection.transactions` GROUP BY status ORDER BY status"
```

---

# 18. Verify Consumer

```cmd
docker ps
```

```cmd
docker logs --tail 50 fraud-consumer
```

```cmd
docker inspect -f "{{.State.Status}}" fraud-consumer
```

```cmd
docker inspect -f "{{.RestartCount}}" fraud-consumer
```

Expected:

```text
running
```

---

# 19. Verify Cloud Run

Describe the Cloud Run service:

```cmd
gcloud run services describe fraud-email-alert --region=asia-south1 --project=priya-509505
```

Read Cloud Run logs:

```cmd
gcloud run services logs read fraud-email-alert --region=asia-south1 --project=priya-509505 --limit=50
```

Test the service:

```cmd
curl https://fraud-email-alert-107755427512.asia-south1.run.app/
```

Expected response:

```text
Fraud Alert Email Service is running.
```

---

# 20. Verify Pub/Sub Fraud Alert Subscription

```cmd
gcloud pubsub subscriptions describe fraud-alert-processor --project=priya-509505
```

Expected:

```text
state: ACTIVE
```

---

# 21. Manual Fraud Alert Test

To test the Cloud Run email alert path independently:

```cmd
gcloud pubsub topics publish fraud-alerts --project=priya-509505 --message="{\"transaction_id\":\"TEST-001\",\"amount\":15000,\"status\":\"FRAUD\",\"reason\":\"High transaction amount\"}"
```

Then check:

```cmd
gcloud run services logs read fraud-email-alert --region=asia-south1 --project=priya-509505 --limit=30
```

Expected log messages include:

```text
FRAUD ALERT RECEIVED
```

and:

```text
Fraud alert email sent successfully!
```

---

# 22. Verified End-to-End Test

The system has been tested successfully with automated transactions.

A verified test produced:

```text
Total Transactions : 11
FRAUD              : 7
LEGITIMATE         : 4
```

Fraud transaction total:

```text
₹92,868.07
```

Legitimate transaction total:

```text
₹14,927.61
```

The test confirmed that:

- Transactions were generated automatically.
- Transactions were published to Pub/Sub.
- The Docker consumer received the messages.
- Fraud detection was performed.
- Transactions were inserted into BigQuery.
- Fraud transactions were published to `fraud-alerts`.
- The Cloud Run email service received fraud alerts.
- Gmail email alerts were successfully delivered.

---

# 23. Error Handling

The consumer acknowledges messages only after successful processing.

## Legitimate Transaction

```text
Receive Message
      |
      v
Fraud Detection
      |
      v
BigQuery Insert
      |
      v
ACK
```

## Fraudulent Transaction

```text
Receive Message
      |
      v
Fraud Detection
      |
      v
BigQuery Insert
      |
      v
Publish Fraud Alert
      |
      v
ACK
```

If BigQuery insertion fails:

```text
Message -> NACK
```

If publishing a required fraud alert fails:

```text
Message -> NACK
```

This prevents successful acknowledgement before the required processing is complete.

---

# 24. Running the Complete System

## Step 1 — Start the Consumer

Open a terminal in:

```text
fraud-detection-project\producer
```

Run:

```cmd
start_consumer.bat
```

Verify:

```cmd
docker ps
```

---

## Step 2 — Start the Producer

Open another terminal in:

```text
fraud-detection-project\producer
```

Run:

```cmd
start_producer.bat
```

The producer automatically generates transactions every few seconds.

---

## Step 3 — Monitor Consumer

```cmd
docker logs -f fraud-consumer
```

You should see:

```text
MESSAGE RECEIVED FROM PUB/SUB
```

followed by either:

```text
Status : LEGITIMATE
```

or:

```text
Status : FRAUD
```

---

## Step 4 — Verify BigQuery

Run:

```cmd
bq query --use_legacy_sql=false --project_id=priya-509505 "SELECT status, COUNT(*) AS transaction_count, ROUND(SUM(amount),2) AS total_amount FROM `priya-509505.fraud_detection.transactions` GROUP BY status ORDER BY status"
```

---

## Step 5 — Check Email

When a generated transaction has:

```text
amount > ₹10,000
```

a fraud alert should be sent automatically to the configured email address.

---

# 25. Security Notes

Do not commit the following to GitHub:

```text
.venv/
.terraform/
terraform.tfstate
terraform.tfstate.backup
*.tfstate*
*.json credentials/service-account keys
```

In particular, a file such as:

```text
fraud-consumer-key.json
```

should not be committed if it contains service-account credentials.

Use `.gitignore` to protect local credentials and generated files.

---

# 26. Project Outcome

This project demonstrates an end-to-end real-time fraud detection pipeline on Google Cloud Platform.

The final architecture combines:

```text
Python
+
Google Pub/Sub
+
Docker
+
BigQuery
+
Cloud Run
+
Artifact Registry
+
Secret Manager
+
Terraform
+
Gmail SMTP
```

The system automatically:

```text
Generate Transaction
        ↓
Publish to Pub/Sub
        ↓
Consume Transaction
        ↓
Detect Fraud
        ↓
Store in BigQuery
        ↓
Publish Fraud Alert
        ↓
Cloud Run
        ↓
Send Gmail Alert
```

The complete workflow has been tested successfully.

---

# Author

**Priya Sahu**

GitHub:

https://github.com/sahupriya-Devops/automated-ecommerce-gcp.git

---

# Project Status

```text
Automated Transaction Producer     [COMPLETED]
Pub/Sub Transaction Topic          [COMPLETED]
Pub/Sub Transaction Subscription   [COMPLETED]
Dockerized Consumer                [COMPLETED]
Fraud Detection Logic              [COMPLETED]
BigQuery Storage                   [COMPLETED]
Fraud Alert Topic                  [COMPLETED]
Cloud Run Email Service            [COMPLETED]
Pub/Sub Push Subscription          [COMPLETED]
Gmail Email Alerts                 [COMPLETED]
Secret Manager                     [COMPLETED]
Terraform Infrastructure           [COMPLETED]
End-to-End Testing                 [COMPLETED]
```

**PROJECT STATUS: COMPLETED AND TESTED**
