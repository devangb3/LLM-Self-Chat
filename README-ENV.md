# Environment Variables Setup Guide

This guide explains how to set up environment variables for the LLM Chat application in different environments.

## 📁 Environment Files Structure

```
├── env.production.example     # Production environment template
├── env.local.example         # Local development template
├── frontend/env.production.example  # Frontend-specific production template
├── backend/env.production.example   # Backend-specific production template
└── .env.local               # Your local environment (not in git)
```

## 🚀 Quick Start

### For Local Development
```bash
# Copy the local development template
cp env.local.example .env.local

# Edit the file with your local settings
nano .env.local
```

### For Production Deployment
```bash
# Copy the production template
cp env.production.example .env.production

# Edit the file with your production settings
nano .env.production
```

## 🔧 Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `PROJECT_ID` | Your GCP project ID | `my-llm-chat-app` |
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://user:pass@cluster.mongodb.net/db` |
| `FLASK_SECRET_KEY` | Flask secret key for sessions | `your-secret-key-here` |
| `ENCRYPTION_KEY` | Key for encrypting API keys | `your-encryption-key-here` |
| `REACT_APP_API_URL` | Backend API URL | `https://backend-url.com/api` |
| `REACT_APP_SOCKET_URL` | WebSocket URL | `https://backend-url.com` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FLASK_ENV` | Flask environment | `development` |
| `FLASK_DEBUG` | Enable Flask debug mode | `true` (dev) / `false` (prod) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5874` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `RATE_LIMIT_REQUESTS` | Rate limiting requests | `100` |
| `SESSION_COOKIE_SECURE` | Secure cookies | `false` (dev) / `true` (prod) |

## 🔐 Security Best Practices

### 1. Never Commit Sensitive Data
```bash
# Add to .gitignore
.env.local
.env.production
.env.*.local
```

### 2. Use Google Secret Manager in Production
```bash
# Store secrets in GCP Secret Manager
gcloud secrets create flask-secret-key --data-file=-
gcloud secrets create api-encryption-key --data-file=-
gcloud secrets create mongodb-uri --data-file=-
```

### 3. Generate Secure Keys
```bash
# Generate Flask secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 🌍 Environment-Specific Configurations

### Local Development
- **Database**: Local MongoDB or development Atlas cluster
- **Security**: Relaxed settings for easier development
- **Debugging**: Full debug mode enabled
- **CORS**: Localhost origins only

### Production
- **Database**: Production MongoDB Atlas cluster
- **Security**: Strict security settings
- **Debugging**: Debug mode disabled
- **CORS**: Production domain origins only
- **HTTPS**: All communication encrypted

### Staging
- **Database**: Staging MongoDB Atlas cluster
- **Security**: Production-like settings
- **Debugging**: Limited debug information
- **CORS**: Staging domain origins

## 🔄 Environment Switching

### Using Different Configs
```bash
# Development
export NODE_ENV=development
export FLASK_ENV=development

# Production
export NODE_ENV=production
export FLASK_ENV=production
```

### Docker Environment
```bash
# Build with production environment
docker build --build-arg NODE_ENV=production -t my-app:prod .

# Run with environment file
docker run --env-file .env.production my-app:prod
```

## 🚨 Common Issues and Solutions

### 1. CORS Errors
```bash
# Check CORS configuration
echo $CORS_ORIGINS

# Update CORS origins
export CORS_ORIGINS="https://your-domain.com,https://another-domain.com"
```

### 2. MongoDB Connection Issues
```bash
# Test MongoDB connection
mongosh "your-mongodb-uri"

# Check network access (for Atlas)
# Ensure your IP is whitelisted in Atlas
```

### 3. Missing Environment Variables
```bash
# Check if variables are set
env | grep -E "(FLASK|MONGODB|REACT_APP)"

# Set missing variables
export FLASK_SECRET_KEY="your-key-here"
```

## 📊 Monitoring Environment Variables

### Health Check Endpoint
```bash
# Check environment status
curl https://your-backend-url.com/health

# Expected response includes environment info
{
  "status": "healthy",
  "environment": "production",
  "database": "connected",
  "version": "1.0.0"
}
```

### Logging Environment Info
```bash
# View environment in logs
gcloud logs tail --service=llm-chat-backend | grep "ENV"
```

## 🔧 Environment Variable Validation

### Backend Validation
The backend automatically validates required environment variables on startup:

```python
# In config.py
@classmethod
def validate(cls):
    missing_vars = []
    if not cls.FLASK_SECRET_KEY:
        missing_vars.append('FLASK_SECRET_KEY')
    if missing_vars:
        raise ValueError(f"Missing: {', '.join(missing_vars)}")
```

### Frontend Validation
The frontend checks for required variables at build time:

```javascript
// In build process
if (!process.env.REACT_APP_API_URL) {
  throw new Error('REACT_APP_API_URL is required');
}
```

## 📝 Deployment Checklist

Before deploying to production:

- [ ] All required environment variables are set
- [ ] Sensitive data is stored in Google Secret Manager
- [ ] CORS origins are configured for production domains
- [ ] HTTPS URLs are used for all external services
- [ ] Debug mode is disabled
- [ ] Logging level is set to INFO or higher
- [ ] Rate limiting is configured appropriately
- [ ] Session security settings are enabled

## 🆘 Getting Help

If you encounter issues with environment variables:

1. Check the application logs for specific error messages
2. Verify all required variables are set
3. Test the configuration locally first
4. Review the security best practices
5. Check the deployment documentation

---

**Remember**: Environment variables are crucial for application security and functionality. Always follow security best practices and never commit sensitive data to version control. 