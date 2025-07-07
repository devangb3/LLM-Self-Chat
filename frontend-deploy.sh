#!/bin/bash

# ==============================================================================
# Google Cloud Run Frontend Deployment Script
# ==============================================================================
#
# This script builds and deploys the React frontend to Google Cloud Run.
#
# Prerequisites:
#   - Google Cloud SDK (gcloud) installed and authenticated.
#   - Docker installed and running.
#   - You have a GCP project with the required APIs enabled.
#   - The backend has been deployed and you have its URL.
#
# What this script does:
#   1. Sets configuration variables (project ID, region, service name).
#   2. Prompts for the backend URL.
#   3. Builds a Docker container for the frontend using Cloud Build. The
#      backend URL is passed as a build argument to be baked into the static
#      files.
#   4. Deploys the container to Cloud Run with production-ready settings.
#
# Usage:
#   ./frontend-deploy.sh
#
# ==============================================================================

set -e # Exit immediately if a command exits with a non-zero status.
set -o pipefail # Return the exit status of the last command in the pipe that failed.

# --- Configuration ---
# IMPORTANT: Replace with your GCP Project ID.
PROJECT_ID="llm-chat-auditor"

# You can change these if needed.
REGION="us-central1"
SERVICE_NAME="llm-chat-frontend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME:$TIMESTAMP"

# --- Backend URL ---
# IMPORTANT: Replace with your backend's Cloud Run URL.
# You can get this from the output of the backend deployment script.
BACKEND_URL="https://llm-chat-backend-424176252593.us-central1.run.app"

# --- Script Start ---
echo "🚀 Starting Frontend Deployment to Google Cloud Run..."
echo "--------------------------------------------------"
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo "Service: $SERVICE_NAME"
echo "Image:   $IMAGE_NAME"
echo "Backend: $BACKEND_URL"
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

if [ "$BACKEND_URL" == "https://your-backend-service-url.a.run.app" ]; then
    echo "❌ Please replace 'https://your-backend-service-url.a.run.app' with your actual Backend Cloud Run URL."
    exit 1
fi

# --- GCP Setup ---
echo "🔧 Setting GCP project and region..."
gcloud config set project $PROJECT_ID
gcloud config set run/region $REGION

# --- Build ---
echo "🏗️ Building the frontend Docker container with Cloud Build..."
# We use a cloudbuild.yaml file to define the build steps and pass substitutions.
cd frontend
gcloud builds submit . --config cloudbuild.yaml \
    --substitutions=_IMAGE_NAME="$IMAGE_NAME",_REACT_APP_API_URL="$BACKEND_URL/api"
cd ..
echo "✅ Frontend container built successfully."

# --- Deploy ---
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image "$IMAGE_NAME" \
    --platform "managed" \
    --region "$REGION" \
    --allow-unauthenticated \
    --port 8080 \
    --memory "256Mi" \
    --cpu "1" \
    --max-instances "2" \
    --min-instances "0" \
    --concurrency "1000" \
    --set-env-vars "BACKEND_URL=$BACKEND_URL"

# --- Post-deployment ---
FRONTEND_URL=$(gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)")

echo ""
echo "✅ Frontend deployment completed successfully!"
echo "--------------------------------------------------"
echo "🔗 Frontend URL: $FRONTEND_URL"
echo ""
echo "🔒 Service is running over HTTPS."
echo "💡 Remember to update your backend's CORS settings to allow requests from the frontend URL."
echo "   You can do this by re-running the backend deployment with the updated CORS_ORIGINS environment variable."
echo "--------------------------------------------------"