# Production Deployment Guide - Google Cloud Platform with HTTPS

This guide will help you deploy the LLM Chat application to Google Cloud Platform with automatic HTTPS support.

## Prerequisites

1. **Google Cloud Account**: You need a GCP account with billing enabled
2. **Google Cloud CLI**: Install the [gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. **Docker**: Install Docker for local testing (optional)
4. **MongoDB**: Set up a MongoDB instance (Atlas recommended for production)

## Step 1: Initial Setup

### 1.1 Create a GCP Project
```bash
# Create a new project (or use existing)
gcloud projects create your-project-id --name="LLM Chat App"

# Set the project as default
gcloud config set project your-project-id
```

### 1.2 Enable Required APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 1.3 Set up Authentication
```bash
# Authenticate with GCP
gcloud auth login

# Set up application default credentials
gcloud auth application-default login
```

## Step 2: Environment Setup

### 2.1 Update Configuration
Edit the deployment scripts with your project details:

```bash
# In setup-gcp.sh and deploy.sh, replace:
PROJECT_ID="your-gcp-project-id"
```

### 2.2 Set up Secrets
```bash
# Make scripts executable
chmod +x deploy.sh


## Step 3: Deploy to Cloud Run

### 3.1 Deploy Both Services
```bash
# Deploy backend and frontend
./deploy.sh
```

This will:
- Build Docker containers
- Push to Google Container Registry
- Deploy to Cloud Run
- Configure HTTPS automatically
- Set up CORS between services

### 3.2 Verify Deployment
After deployment, you'll see URLs like:
```
🌐 Frontend URL: https://llm-chat-frontend-xxxxx-uc.a.run.app
🔧 Backend URL: https://llm-chat-backend-xxxxx-uc.a.run.app
```

## Step 4: Custom Domain (Optional)

### 4.1 Map Custom Domain
```bash
# Map a custom domain to your frontend service
gcloud run domain-mappings create \
  --service llm-chat-frontend \
  --domain your-domain.com \
  --region us-central1
```

### 4.2 Update DNS
1. Add a CNAME record pointing to the provided domain
2. Wait for SSL certificate provisioning (can take up to 24 hours)

## Step 5: Environment Variables

### 5.1 Update CORS Origins
If you're using a custom domain, update the CORS origins:

```bash
# Update the backend service with new CORS origins
gcloud run services update llm-chat-backend \
  --region us-central1 \
  --set-env-vars "CORS_ORIGINS=https://your-domain.com,https://llm-chat-frontend-xxxxx-uc.a.run.app"
```

### 5.2 Update Frontend Environment
Create a `.env.production` file in the frontend directory:
```env
REACT_APP_API_URL=https://llm-chat-backend-xxxxx-uc.a.run.app/api
REACT_APP_SOCKET_URL=https://llm-chat-backend-xxxxx-uc.a.run.app
```

## Step 6: Monitoring and Logging

### 6.1 View Logs
```bash
# View backend logs
gcloud logs tail --service=llm-chat-backend

# View frontend logs
gcloud logs tail --service=llm-chat-frontend
```

### 6.2 Set up Monitoring
1. Go to Google Cloud Console
2. Navigate to Monitoring
3. Create dashboards for your services

## Step 7: Scaling and Performance

### 7.1 Adjust Resources
```bash
# Scale backend for higher traffic
gcloud run services update llm-chat-backend \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 20
```

### 7.2 Enable Autoscaling
Cloud Run automatically scales based on traffic, but you can adjust:
- Minimum instances (for faster cold starts)
- Maximum instances (to control costs)
- Concurrency (requests per instance)

## Security Features

### HTTPS/SSL
- ✅ Automatically provisioned by Cloud Run
- ✅ Valid SSL certificates
- ✅ HTTP/2 support
- ✅ Security headers configured

### Secret Management
- ✅ Secrets stored in Google Secret Manager
- ✅ Encrypted at rest and in transit
- ✅ IAM-controlled access
- ✅ Automatic rotation support

### CORS Configuration
- ✅ Properly configured for production domains
- ✅ Credentials support enabled
- ✅ Secure cookie settings

## Troubleshooting

### Common Issues

1. **CORS Errors**
   ```bash
   # Check CORS configuration
   gcloud run services describe llm-chat-backend --region=us-central1
   ```

2. **Secret Access Issues**
   ```bash
   # Verify service account permissions
   gcloud projects get-iam-policy your-project-id
   ```

3. **WebSocket Connection Issues**
   - Ensure the backend URL is correct in frontend environment
   - Check that CORS origins include the frontend URL

4. **MongoDB Connection Issues**
   - Verify MongoDB URI in Secret Manager
   - Check network access (IP whitelist if using Atlas)

### Debug Commands
```bash
# Test backend health
curl https://llm-chat-backend-xxxxx-uc.a.run.app/

# Check service status
gcloud run services list --region=us-central1

# View recent deployments
gcloud run revisions list --service=llm-chat-backend --region=us-central1
```

## Cost Optimization

### 7.1 Resource Optimization
- Use appropriate memory/CPU settings
- Set reasonable max instances
- Monitor usage in Cloud Console

### 7.2 Free Tier
- Cloud Run: 2 million requests/month free
- Secret Manager: First 6,000 operations/month free
- Cloud Build: 120 build-minutes/day free

## Maintenance

### 7.1 Updates
```bash
# Deploy updates
./deploy.sh

# Rollback if needed
gcloud run services update-traffic llm-chat-backend \
  --to-revisions=llm-chat-backend-00001-abc=100 \
  --region=us-central1
```

### 7.2 Backup
- MongoDB: Use Atlas backup features
- Secrets: Automatically backed up in Secret Manager
- Code: Use version control (Git)

## Support

For issues:
1. Check Cloud Run logs
2. Verify environment variables
3. Test locally with production config
4. Review GCP documentation

---

**Note**: This deployment automatically provides HTTPS/SSL certificates and secure communication between all components. 