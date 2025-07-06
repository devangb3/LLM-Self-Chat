# Get backend URL
BACKEND_URL=$(gcloud run services describe llm-chat-backend --region=us-central1 --format="value(status.url)")
echo "BACKEND_URL: $BACKEND_URL"
# Set variables
PROJECT_ID="llm-chat-auditor"
REGION="us-central1"
FRONTEND_SERVICE_NAME="llm-chat-frontend"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FRONTEND_IMAGE="gcr.io/$PROJECT_ID/$FRONTEND_SERVICE_NAME:$TIMESTAMP"

# Go to frontend directory
cd frontend

# Create .env.production
cat > .env.production << EOF
REACT_APP_API_URL=$BACKEND_URL/api
REACT_APP_SOCKET_URL=$BACKEND_URL
EOF

# Build with Dockerfile
gcloud builds submit --tag $FRONTEND_IMAGE

# Deploy to Cloud Run
gcloud run deploy $FRONTEND_SERVICE_NAME \
    --image $FRONTEND_IMAGE \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --memory 128Mi \
    --cpu 1 \
    --max-instances 2 \
    --min-instances 1 \
    --concurrency 1000 \
    --set-env-vars "BACKEND_URL=$BACKEND_URL"

cd ..