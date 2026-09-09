# Fraud Detection Streaming Pipeline on GCP

## Project Overview

This project is an end-to-end real-time fraud detection data engineering
pipeline built on **Google Cloud Platform (GCP)**.

The pipeline simulates financial transactions, publishes them to
**Google Cloud Pub/Sub**, processes the transactions using a Python
consumer running inside **Docker**, applies fraud detection rules, and
stores the processed results in **Google BigQuery** for analytics.

The infrastructure required for the pipeline is provisioned using
**Terraform**, while Docker is used to package and run the transaction
processing application.

### Pipeline Flow

**Transaction Generator → Pub/Sub Topic → Pub/Sub Subscription →
Dockerized Fraud Detection Consumer → BigQuery**

The project demonstrates how a real-time event-driven data pipeline can
be designed using managed GCP services and infrastructure as code.

------------------------------------------------------------------------

## Project Architecture

The pipeline consists of the following major components:

### 1. Transaction Producer

The `producer.py` application generates transaction events containing
information such as:

-   Transaction ID
-   User ID
-   Transaction amount
-   Merchant
-   Location
-   Timestamp

The generated transaction is converted into JSON and published to the
Google Cloud Pub/Sub topic.

------------------------------------------------------------------------

### 2. Google Cloud Pub/Sub

Pub/Sub acts as the messaging layer between the transaction producer and
fraud detection consumer.

The project contains:

-   **Topic:** `fraud-events`
-   **Subscription:** `fraud-processor`

The producer publishes transaction events to the `fraud-events` topic.

The `fraud-processor` subscription receives those messages so that the
consumer can process them.

This provides loose coupling between transaction generation and
transaction processing.

------------------------------------------------------------------------

### 3. Fraud Detection Consumer

The `consumer.py` application subscribes to the Pub/Sub subscription and
processes incoming transaction messages.

The consumer:

1.  Receives the transaction from Pub/Sub.
2.  Decodes the message.
3.  Applies fraud detection rules.
4.  Assigns a transaction status.
5.  Generates a reason for the decision.
6.  Inserts the processed transaction into BigQuery.
7.  Acknowledges the Pub/Sub message after successful processing.

Example statuses:

-   `LEGITIMATE`
-   `FRAUD`

Example fraud rule:

``` text
If transaction amount > 10000
    → FRAUD
Else
    → LEGITIMATE
```

The rules can be extended later to support more advanced fraud detection
logic.

------------------------------------------------------------------------

### 4. Docker

The fraud detection consumer is packaged as a Docker image.

Docker provides a consistent runtime environment containing:

-   Python
-   Required Google Cloud libraries
-   Consumer application
-   Runtime dependencies

The image is built using the project's `Dockerfile`.

The container runs:

``` text
python consumer.py
```

The Docker image used by the project is:

``` text
fraud-detection-consumer
```

------------------------------------------------------------------------

### 5. Google Artifact Registry

The Docker image is stored in **Google Artifact Registry**.

Repository:

``` text
fraud-detection
```

Region:

``` text
asia-south1
```

The image is pushed using:

``` text
asia-south1-docker.pkg.dev/ashishandpriya/fraud-detection/fraud-detection-consumer:latest
```

Artifact Registry provides a centralized and secure location for storing
the container image.

------------------------------------------------------------------------

### 6. BigQuery

BigQuery is used as the analytical storage layer for processed
transaction data.

Project:

``` text
ashishandpriya
```

Dataset:

``` text
fraud_detection
```

Table:

``` text
transactions
```

Fully qualified table:

``` text
ashishandpriya.fraud_detection.transactions
```

The table stores both legitimate and fraudulent transactions.

Typical columns include:

  Column             Description
  ------------------ --------------------------------------
  `transaction_id`   Unique transaction identifier
  `user_id`          User associated with the transaction
  `amount`           Transaction amount
  `merchant`         Merchant where transaction occurred
  `location`         Transaction location
  `timestamp`        Transaction timestamp
  `status`           Fraud detection result
  `reason`           Explanation for the result

------------------------------------------------------------------------

## Infrastructure as Code

Terraform is used to provision and manage the GCP infrastructure
required by the project.

The Terraform configuration is located in:

``` text
terraform/
```

### Terraform Files

``` text
terraform/
├── main.tf
├── provider.tf
├── variables.tf
├── bigquery.tf
└── .terraform.lock.hcl
```

### `provider.tf`

Configures the Google Cloud provider used by Terraform.

### `variables.tf`

Contains configurable Terraform variables such as the GCP project
configuration.

### `main.tf`

Contains the main infrastructure configuration, including Pub/Sub
resources.

### `bigquery.tf`

Defines the BigQuery dataset and transactions table.

### `.terraform.lock.hcl`

Locks the provider versions used by the project to provide reproducible
Terraform deployments.

------------------------------------------------------------------------

## Project Structure

``` text
fraud-detection-project/
│
├── producer/
│   ├── producer.py
│   ├── consumer.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── terraform/
│   ├── main.tf
│   ├── provider.tf
│   ├── variables.tf
│   ├── bigquery.tf
│   └── .terraform.lock.hcl
│
├── .gitignore
└── README.md
```

> The service account key file used for local authentication is
> intentionally excluded from Git using `.gitignore`.

------------------------------------------------------------------------

## Technologies Used

  Technology                 Purpose
  -------------------------- ---------------------------------------
  Python                     Transaction generation and processing
  Google Cloud Pub/Sub       Real-time messaging
  Google BigQuery            Analytical data storage
  Docker                     Application containerization
  Google Artifact Registry   Docker image storage
  Terraform                  Infrastructure provisioning
  Google Cloud IAM           Authentication and authorization
  Git                        Source code version control
  GitHub                     Remote source code repository

------------------------------------------------------------------------

## Python Dependencies

The application uses the following Google Cloud libraries:

``` text
google-cloud-pubsub
google-cloud-bigquery
```

They are defined in:

``` text
producer/requirements.txt
```

Install them locally using:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

# GCP Infrastructure Setup

## 1. Configure the GCP Project

Set the active GCP project:

``` bash
gcloud config set project ashishandpriya
```

Verify:

``` bash
gcloud config get-value project
```

Expected:

``` text
ashishandpriya
```

------------------------------------------------------------------------

## 2. Enable Required Services

Enable the required Google Cloud APIs:

``` bash
gcloud services enable pubsub.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

------------------------------------------------------------------------

# Terraform Deployment

Navigate to the Terraform directory:

``` bash
cd terraform
```

Initialize Terraform:

``` bash
terraform init
```

Validate the configuration:

``` bash
terraform validate
```

Create an execution plan:

``` bash
terraform plan
```

Apply the infrastructure:

``` bash
terraform apply
```

Terraform provisions the required Pub/Sub and BigQuery resources.

To remove the Terraform-managed infrastructure:

``` bash
terraform destroy
```

------------------------------------------------------------------------

# Local Authentication

For local development, Google Application Default Credentials can be
configured using:

``` bash
gcloud auth application-default login
```

Verify that credentials are available:

``` bash
gcloud auth application-default print-access-token
```

The Docker container does not automatically receive credentials from the
Windows host.

For local Docker testing, the Google Cloud configuration directory can
be mounted into the container.

Example:

``` bash
docker run --rm -it ^
  -v "%APPDATA%\gcloud:/root/.config/gcloud:ro" ^
  fraud-detection-consumer
```

This allows the containerized application to use the local Application
Default Credentials.

------------------------------------------------------------------------

# Service Account

A dedicated service account is used for the fraud detection consumer.

Example service account:

``` text
fraud-consumer@ashishandpriya.iam.gserviceaccount.com
```

The service account is granted the permissions required by the
application.

Current roles include:

``` text
roles/bigquery.dataEditor
roles/bigquery.jobUser
roles/pubsub.subscriber
```

These permissions allow the consumer to:

-   Read messages from Pub/Sub.
-   Insert processed transactions into BigQuery.
-   Execute required BigQuery jobs.

### Security

The service account JSON key is a sensitive credential.

It must never be committed to GitHub.

The project `.gitignore` contains:

``` text
fraud-consumer-key.json
```

If a service account key is accidentally exposed, it should be revoked
and replaced immediately.

------------------------------------------------------------------------

# Docker Setup

## Build the Docker Image

Navigate to the application directory:

``` bash
cd producer
```

Build the image:

``` bash
docker build -t fraud-detection-consumer .
```

Verify the image:

``` bash
docker images
```

Expected image:

``` text
fraud-detection-consumer
```

------------------------------------------------------------------------

## Test Docker Installation

Verify that Docker is working:

``` bash
docker run --rm hello-world
```

A successful `Hello from Docker!` message confirms that the Docker
engine is running correctly.

------------------------------------------------------------------------

# Run the Consumer

Run the consumer container:

``` bash
docker run --rm -it ^
  -v "%APPDATA%\gcloud:/root/.config/gcloud:ro" ^
  fraud-detection-consumer
```

Expected output:

``` text
Fraud detection consumer is running...
Listening on: projects/ashishandpriya/subscriptions/fraud-processor
BigQuery table: ashishandpriya.fraud_detection.transactions
```

The consumer will continue listening for Pub/Sub messages.

------------------------------------------------------------------------

# Run the Producer

Open another terminal.

Navigate to:

``` bash
cd producer
```

Run:

``` bash
python producer.py
```

Example output:

``` text
Transaction published successfully!
Message ID: 21663255670241076
Transaction: {
    'transaction_id': '...',
    'user_id': 'USER4964',
    'amount': 4894.61,
    'merchant': 'Grocery Store',
    'location': 'Delhi',
    'timestamp': '...'
}
```

Each execution publishes a transaction to Pub/Sub.

The running consumer receives the transaction and processes it.

------------------------------------------------------------------------

# End-to-End Processing

The complete flow is:

``` text
                    ┌─────────────────────┐
                    │   producer.py       │
                    │ Transaction Generator│
                    └──────────┬──────────┘
                               │
                               │ Publish JSON
                               ▼
                    ┌─────────────────────┐
                    │   Pub/Sub Topic     │
                    │    fraud-events     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Pub/Sub Subscription│
                    │   fraud-processor   │
                    └──────────┬──────────┘
                               │
                               │ Pull Message
                               ▼
                    ┌─────────────────────┐
                    │ Docker Container    │
                    │   consumer.py       │
                    │                     │
                    │ Fraud Detection     │
                    └──────────┬──────────┘
                               │
                               │ Insert Result
                               ▼
                    ┌─────────────────────┐
                    │     BigQuery        │
                    │ fraud_detection     │
                    │    transactions     │
                    └─────────────────────┘
```

------------------------------------------------------------------------

# Example Fraud Detection

A transaction such as:

``` text
Transaction ID : 3c758b59-4031-4ceb-88bb-8237b5829c52
User ID        : USER5949
Amount         : 14561.01
Merchant       : Online Shop
Location       : Chandigarh
Status         : FRAUD
Reason         : High transaction amount
```

is classified as fraudulent because the transaction amount exceeds the
configured fraud threshold.

A normal transaction may look like:

``` text
Transaction ID : 963d56ff-4898-434f-9acf-1fcc9b0af819
User ID        : USER4964
Amount         : 4894.61
Merchant       : Grocery Store
Location       : Delhi
Status         : LEGITIMATE
Reason         : Transaction appears normal
```

------------------------------------------------------------------------

# BigQuery Validation

After the consumer processes transactions, the results can be queried in
BigQuery.

## View All Transactions

``` sql
SELECT
  transaction_id,
  user_id,
  amount,
  merchant,
  location,
  timestamp,
  status,
  reason
FROM `ashishandpriya.fraud_detection.transactions`
ORDER BY timestamp DESC;
```

------------------------------------------------------------------------

## Find Fraudulent Transactions

``` sql
SELECT *
FROM `ashishandpriya.fraud_detection.transactions`
WHERE status = 'FRAUD';
```

------------------------------------------------------------------------

## Count Fraudulent Transactions

``` sql
SELECT
  COUNT(*) AS fraud_count
FROM `ashishandpriya.fraud_detection.transactions`
WHERE status = 'FRAUD';
```

------------------------------------------------------------------------

## Fraud vs Legitimate Transactions

``` sql
SELECT
  status,
  COUNT(*) AS transaction_count
FROM `ashishandpriya.fraud_detection.transactions`
GROUP BY status;
```

------------------------------------------------------------------------

## Highest Value Transactions

``` sql
SELECT
  transaction_id,
  user_id,
  amount,
  merchant,
  location,
  status
FROM `ashishandpriya.fraud_detection.transactions`
ORDER BY amount DESC
LIMIT 10;
```

------------------------------------------------------------------------

# Artifact Registry

The Docker image can be stored in Google Artifact Registry.

Authenticate Docker with Artifact Registry:

``` bash
gcloud auth configure-docker asia-south1-docker.pkg.dev
```

Tag the image:

``` bash
docker tag fraud-detection-consumer:latest \
asia-south1-docker.pkg.dev/ashishandpriya/fraud-detection/fraud-detection-consumer:latest
```

Push the image:

``` bash
docker push asia-south1-docker.pkg.dev/ashishandpriya/fraud-detection/fraud-detection-consumer:latest
```

The image can then be used by other GCP compute services such as Cloud
Run or GKE as the project evolves.

------------------------------------------------------------------------

# Git and GitHub

Initialize the repository:

``` bash
git init
```

Rename the default branch:

``` bash
git branch -M main
```

Check the repository:

``` bash
git status
```

Add project files:

``` bash
git add .
```

Create the initial commit:

``` bash
git commit -m "Initial fraud detection project"
```

Add the GitHub remote:

``` bash
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
```

Push the project:

``` bash
git push -u origin main
```

------------------------------------------------------------------------

# Git Ignore

The project excludes files that should not be committed.

Important exclusions include:

``` text
.venv/
__pycache__/
*.pyc
terraform/.terraform/
*.tfstate
*.tfstate.*
fraud-consumer-key.json
```

This prevents local environments, Terraform state, generated files, and
sensitive credentials from being pushed to the repository.

------------------------------------------------------------------------

# Key Learning Outcomes

This project demonstrates practical experience with:

-   Real-time data ingestion
-   Event-driven architecture
-   Google Cloud Pub/Sub
-   BigQuery
-   Python data processing
-   Docker containerization
-   Google Artifact Registry
-   Terraform Infrastructure as Code
-   Google Cloud IAM
-   Application Default Credentials
-   Service account authentication
-   Git and GitHub
-   Cloud-based data engineering architecture

------------------------------------------------------------------------

# Future Enhancements

The current project provides a foundation for a larger real-time fraud
detection platform.

Possible enhancements include:

### Advanced Fraud Rules

Add rules based on:

-   Multiple transactions within a short time
-   Unusual transaction locations
-   User spending patterns
-   Merchant risk scores
-   Repeated failed transactions
-   Large deviations from historical spending

### Machine Learning

Replace rule-based detection with a machine learning model using:

-   Vertex AI
-   BigQuery ML
-   Scikit-learn
-   TensorFlow

### Cloud Run Deployment

Deploy the Dockerized consumer to Google Cloud Run for a managed
serverless deployment.

### Monitoring

Add:

-   Cloud Logging
-   Cloud Monitoring
-   Error reporting
-   Pub/Sub backlog monitoring
-   Application metrics

### Data Visualization

Create dashboards using:

-   Looker Studio
-   BigQuery
-   Other BI tools

Possible dashboard metrics:

-   Total transactions
-   Fraud transactions
-   Fraud percentage
-   Total transaction value
-   Fraud value
-   Fraud by location
-   Fraud by merchant
-   Fraud trends over time

------------------------------------------------------------------------

# Project Workflow Summary

``` text
1. Terraform provisions GCP infrastructure
             ↓
2. Producer generates transaction
             ↓
3. Transaction is published to Pub/Sub
             ↓
4. Pub/Sub stores and delivers the event
             ↓
5. Dockerized consumer receives the event
             ↓
6. Fraud detection logic evaluates transaction
             ↓
7. Result is written to BigQuery
             ↓
8. BigQuery is queried for analysis
             ↓
9. Results can be visualized in a dashboard
```

------------------------------------------------------------------------

# Conclusion

This project demonstrates an end-to-end **real-time fraud detection
pipeline on Google Cloud Platform**.

It combines messaging, containerization, infrastructure as code, IAM,
and analytical storage into a practical data engineering workflow.

The architecture can be extended from a local development environment
into a production-ready cloud platform by introducing managed compute,
automated CI/CD, advanced fraud detection models, monitoring, and
analytics dashboards.
