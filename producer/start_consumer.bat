@echo off
setlocal

title Fraud Detection Consumer

echo.
echo ============================================================
echo       FRAUD DETECTION CONSUMER - STARTING
echo ============================================================
echo.

REM ============================================================
REM CONFIGURATION
REM ============================================================

set "PROJECT_ID=priya-509505"
set "TOPIC_ID=fraud-events"
set "SUBSCRIPTION_ID=fraud-processor"
set "CONTAINER_NAME=fraud-consumer"
set "IMAGE_NAME=fraud-detection-consumer"
set "BQ_TABLE=priya-509505.fraud_detection.transactions"

REM ============================================================
REM 1. CHECK DOCKER
REM ============================================================

echo [1/7] Checking Docker...

docker info >nul 2>&1

if errorlevel 1 (
    echo.
    echo ERROR: Docker Desktop is not running.
    echo Please start Docker Desktop and run this file again.
    echo.
    pause
    exit /b 1
)

echo Docker is running.
echo.

REM ============================================================
REM 2. CHECK GOOGLE CLOUD CLI
REM ============================================================

echo [2/7] Checking Google Cloud CLI...

where gcloud >nul 2>&1

if errorlevel 1 (
    echo.
    echo ERROR: Google Cloud CLI is not installed or not in PATH.
    echo.
    pause
    exit /b 1
)

echo Google Cloud CLI is installed.
echo.

REM ============================================================
REM 3. CHECK / SET GCP PROJECT
REM ============================================================

echo [3/7] Checking GCP project...

set "CURRENT_PROJECT="

call gcloud config get-value project > "%TEMP%\gcp_project.txt" 2>nul

set /p CURRENT_PROJECT=<"%TEMP%\gcp_project.txt"

del "%TEMP%\gcp_project.txt" >nul 2>&1

if "%CURRENT_PROJECT%"=="" (
    echo No GCP project configured.
    echo Setting project to %PROJECT_ID%...

    call gcloud config set project %PROJECT_ID%

    if errorlevel 1 (
        echo.
        echo ERROR: Could not set GCP project.
        echo.
        pause
        exit /b 1
    )

    set "CURRENT_PROJECT=%PROJECT_ID%"
)

if not "%CURRENT_PROJECT%"=="%PROJECT_ID%" (
    echo Current project is: %CURRENT_PROJECT%
    echo Setting project to: %PROJECT_ID%

    call gcloud config set project %PROJECT_ID%

    if errorlevel 1 (
        echo.
        echo ERROR: Could not set GCP project.
        echo.
        pause
        exit /b 1
    )
)

echo GCP project: %PROJECT_ID%
echo.

REM ============================================================
REM 4. CHECK PUB/SUB TOPIC
REM ============================================================

echo [4/7] Checking Pub/Sub topic...

call gcloud pubsub topics describe %TOPIC_ID% --project=%PROJECT_ID% >nul 2>&1

if errorlevel 1 (

    echo Topic does not exist.
    echo Creating topic: %TOPIC_ID%

    call gcloud pubsub topics create %TOPIC_ID% --project=%PROJECT_ID%

    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create Pub/Sub topic.
        echo.
        pause
        exit /b 1
    )

    echo Topic created successfully.

) else (

    echo Topic exists: %TOPIC_ID%

)

echo.

REM ============================================================
REM 5. CHECK PUB/SUB SUBSCRIPTION
REM ============================================================

echo [5/7] Checking Pub/Sub subscription...

call gcloud pubsub subscriptions describe %SUBSCRIPTION_ID% --project=%PROJECT_ID% >nul 2>&1

if errorlevel 1 (

    echo Subscription does not exist.
    echo Creating subscription: %SUBSCRIPTION_ID%

    call gcloud pubsub subscriptions create %SUBSCRIPTION_ID% ^
        --topic=%TOPIC_ID% ^
        --project=%PROJECT_ID% ^
        --ack-deadline=60 ^
        --message-retention-duration=7d

    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create Pub/Sub subscription.
        echo.
        pause
        exit /b 1
    )

    echo Subscription created successfully.

) else (

    echo Subscription exists: %SUBSCRIPTION_ID%

)

echo.

REM ============================================================
REM 6. BUILD / CHECK DOCKER IMAGE
REM ============================================================

echo [6/7] Building Docker image...

docker build -t %IMAGE_NAME% .

if errorlevel 1 (
    echo.
    echo ERROR: Docker image build failed.
    echo.
    pause
    exit /b 1
)

echo Docker image is ready.
echo.

REM ============================================================
REM REMOVE EXISTING CONTAINER
REM ============================================================

echo Checking existing consumer container...

docker container inspect %CONTAINER_NAME% >nul 2>&1

if not errorlevel 1 (

    echo Existing container found.
    echo Removing old container...

    docker rm -f %CONTAINER_NAME% >nul 2>&1

    if errorlevel 1 (
        echo.
        echo ERROR: Could not remove existing consumer container.
        echo.
        pause
        exit /b 1
    )

    echo Old container removed.

) else (

    echo No existing consumer container found.

)

echo.

REM ============================================================
REM 7. START CONSUMER
REM ============================================================

echo [7/7] Starting fraud detection consumer...

docker run -d ^
    --name %CONTAINER_NAME% ^
    -v "%APPDATA%\gcloud:/root/.config/gcloud:ro" ^
    %IMAGE_NAME%

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Docker consumer.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo       FRAUD DETECTION CONSUMER IS RUNNING
echo ============================================================
echo.
echo Project       : %PROJECT_ID%
echo Topic         : %TOPIC_ID%
echo Subscription  : %SUBSCRIPTION_ID%
echo Container     : %CONTAINER_NAME%
echo BigQuery      : %BQ_TABLE%
echo.
echo Consumer started successfully.
echo.
echo Showing consumer logs...
echo.
echo IMPORTANT:
echo Press CTRL+C only to stop viewing logs.
echo The Docker consumer will continue running.
echo.
echo To stop the consumer:
echo     docker stop %CONTAINER_NAME%
echo.
echo To view logs again:
echo     docker logs -f %CONTAINER_NAME%
echo.
echo ============================================================
echo.

docker logs -f %CONTAINER_NAME%

echo.
echo ============================================================
echo Log viewing stopped.
echo Docker consumer is still running.
echo ============================================================
echo.

pause

endlocal