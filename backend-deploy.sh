#!/bin/bash

# ==============================================================================
# Google Cloud Run Backend Deployment Script
# ==============================================================================
#
# This script builds and deploys the Flask backend to Google Cloud Run.
#
# Prerequisites:
#   - Google Cloud SDK (gcloud) installed and authenticated.
#   - Docker installed and running.
#   - You have a GCP project with the required APIs enabled.
#   - Your secrets (MongoDB URI, Flask Secret Key, etc.) are stored in
#     Google Secret Manager.
#
# What this script does:
#   1. Sets configuration variables (project ID, region, service name).
#   2. Enables necessary GCP services (Cloud Build, Cloud Run, Secret Manager).
#   3. Builds a Docker container for the backend using Cloud Build.
#   4. Deploys the container to Cloud Run with production-ready settings:
#      - Sets environment variables for production mode.
#      - Securely mounts secrets from Secret Manager.
#      - Configures resource allocation (memory, CPU) and scaling.
#
# Usage:
#   ./backend-deploy.sh
#
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status.
set -o pipefail # Return the exit status of the last command in the pipe that failed.

# --- Configuration ---
# IMPORTANT: Replace with your GCP Project ID.
PROJECT_ID="llm-chat-auditor"

# You can change these if needed.
REGION="us-central1"
SERVICE_NAME="llm-chat-backend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$TIMESTAMP"

# --- Secrets Configuration ---
# Format: "ENV_VAR_NAME=secret-name:version"
# 'latest' is recommended for the version.
SECRETS=(
    "MONGODB_URI=mongodb-uri:latest"
    "FLASK_SECRET_KEY=flask-secret-key:latest"
    "ENCRYPTION_KEY=api-encryption-key:latest"
)

# --- Script Start ---
echo "🚀 Starting Backend Deployment to Google Cloud Run..."
echo "--------------------------------------------------"
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Service: $SERVICE_NAME"
echo "Image:   $IMAGE_NAME"
echo "--------------------------------------------------"

# --- Pre-flight Checks ---
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it and authenticate."
    exit 1
fi

if [ "$PROJECT_ID" == "your-gcp-project-id" ]; then
    echo "❌ Please replace 'your-gcp-project-id' with your actual GCP Project ID in this script."
    exit 1
fi

# --- GCP Setup ---
echo "🔧 Setting GCP project and region..."
gcloud config set project $PROJECT_ID
gcloud config set builds/region $REGION

echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com

# --- Build ---
echo "🏗️ Building the backend Docker container with Cloud Build..."
cd backend
gcloud builds submit . --tag "$IMAGE_NAME"
cd ..
echo "✅ Backend container built successfully."

# --- Deploy ---
echo "☁️ Deploying to Cloud Run..."

# Convert secrets array to a comma-separated string for the gcloud command
secrets_arg=$(IFS=,; echo "${SECRETS[*]}")

gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform "managed" \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory "512Mi" \
    --cpu "1" \
    --max-instances "3" \
    --min-instances "1" \
    --concurrency "80" \
    --set-env-vars "FLASK_ENV=production,CORS_ORIGINS=https://llm-chat-frontend-424176252593.us-central1.run.app" \
    --set-secrets "$secrets_arg"

# --- Post-deployment ---
BACKEND_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

echo ""
echo "✅ Backend deployment completed successfully!"
echo "--------------------------------------------------"
echo "🔗 Backend URL: $BACKEND_URL"
echo "   (This will be used in the frontend deployment)"
echo ""
echo "🔒 Service is running in production mode over HTTPS."
echo "🔐 Secrets are securely mounted from Secret Manager."
echo "--------------------------------------------------"