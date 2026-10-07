@echo off
setlocal

cd /d "%~dp0"

title Fraud Detection Producer

echo.
echo ============================================================
echo       FRAUD DETECTION PRODUCER - STARTING
echo ============================================================
echo.

REM ============================================================
REM CONFIGURATION
REM ============================================================

set "PROJECT_ID=priya-509505"
set "TOPIC_ID=fraud-events"

REM ============================================================
REM 1. CHECK GOOGLE CLOUD CLI
REM ============================================================

echo [1/4] Checking Google Cloud CLI...

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
REM 2. CHECK / SET GCP PROJECT
REM ============================================================

echo [2/4] Checking GCP project...

call gcloud config set project %PROJECT_ID%

if errorlevel 1 (
    echo.
    echo ERROR: Could not set GCP project.
    echo.
    pause
    exit /b 1
)

echo GCP project: %PROJECT_ID%
echo.

REM ============================================================
REM 3. CHECK PUB/SUB TOPIC
REM ============================================================

echo [3/4] Checking Pub/Sub topic...

call gcloud pubsub topics describe %TOPIC_ID% --project=%PROJECT_ID% >nul 2>&1

if errorlevel 1 (
    echo.
    echo Topic does not exist.
    echo Creating topic: %TOPIC_ID%
    echo.

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
REM 4. START PRODUCER
REM ============================================================

echo [4/4] Starting fraud transaction producer...
echo.
echo ============================================================
echo       FRAUD DETECTION PRODUCER IS RUNNING
echo ============================================================
echo.
echo Project : %PROJECT_ID%
echo Topic   : %TOPIC_ID%
echo.
echo Transactions will be generated automatically.
echo Press CTRL+C to stop the producer.
echo.
echo ============================================================
echo.

python producer.py

echo.
echo ============================================================
echo       PRODUCER STOPPED
echo ============================================================
echo.

pause

endlocal