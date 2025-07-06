#!/bin/bash

# Deploy to Google Cloud Run with HTTPS
# This script deploys both backend and frontend to Cloud Run

set -e

# Configuration
PROJECT_ID="llm-chat-auditor"
REGION="us-central1"
BACKEND_SERVICE_NAME="llm-chat-backend"
FRONTEND_SERVICE_NAME="llm-chat-frontend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKEND_IMAGE="gcr.io/$PROJECT_ID/$BACKEND_SERVICE_NAME:$TIMESTAMP"
FRONTEND_IMAGE="gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME:$TIMESTAMP"

echo "🚀 Starting deployment to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Set project
echo "Setting GCP project..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Build and deploy backend
echo "🏗️ Building and deploying backend..."
cd backend

# Build the container
gcloud builds submit --tag $BACKEND_IMAGE

# Deploy to Cloud Run with cost-optimized settings
gcloud run deploy $BACKEND_SERVICE_NAME \
    --image $BACKEND_IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 256Mi \
    --cpu 1 \
    --max-instances 3 \
    --min-instances 0 \
    --concurrency 80 \
    --set-env-vars "FLASK_ENV=production" \
    --set-env-vars "PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "CORS_ORIGINS=https://$FRONTEND_SERVICE_NAME-$PROJECT_ID.a.run.app" \
    --set-secrets "MONGODB_URI=mongodb-uri:latest" \
    --set-secrets "FLASK_SECRET_KEY=flask-secret-key:latest" \
    --set-secrets "ENCRYPTION_KEY=api-encryption-key:latest"

# Get backend URL
BACKEND_URL=$(gcloud run services describe $BACKEND_SERVICE_NAME --region=$REGION --format="value(status.url)")

cd ..

# Build and deploy frontend
echo "🏗️ Building and deploying frontend..."
cd frontend

# Create .env.production file
cat > .env.production << EOF
REACT_APP_API_URL=$BACKEND_URL/api
REACT_APP_SOCKET_URL=$BACKEND_URL
EOF

# Build the container
gcloud builds submit --tag $FRONTEND_IMAGE

# Deploy to Cloud Run with cost-optimized settings
gcloud run deploy $FRONTEND_SERVICE_NAME \
    --image $FRONTEND_IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 128Mi \
    --cpu 1 \
    --max-instances 2 \
    --min-instances 0 \
    --concurrency 1000 \
    --set-env-vars "BACKEND_URL=$BACKEND_URL"

cd ..

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe $FRONTEND_SERVICE_NAME --region=$REGION --format="value(status.url)")

echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Frontend URL: $FRONTEND_URL"
echo "🔧 Backend URL: $BACKEND_URL"
echo ""
echo "🔒 Both services are automatically served over HTTPS!"
echo "🔐 Secrets are securely managed via Google Secret Manager!"
echo "💰 Cost-optimized settings applied:"
echo "   - Backend: 256Mi RAM, max 3 instances"
echo "   - Frontend: 128Mi RAM, max 2 instances"
echo "   - Backend scales to zero when not in use"
echo ""
echo "📝 Secrets used from Secret Manager:"
echo "   - mongodb-uri"
echo "   - flask-secret-key"
echo "   - api-encryption-key" 