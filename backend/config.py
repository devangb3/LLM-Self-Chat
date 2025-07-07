import os
import logging
from dotenv import load_dotenv
from google.cloud import secretmanager
import time

logger = logging.getLogger(__name__)

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")

def get_gcp_secret(secret_id, version_id="latest"):
    """
    Retrieves a secret from Google Cloud Secret Manager.
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except ImportError:
        print(f"Warning: google-cloud-secret-manager not installed, using environment variables")
        return None
    except Exception as e:
        print(f"Warning: Failed to access secret {secret_id}: {e}")
        return None

class Config:
    """Configuration class for the application"""
    
    FLASK_SECRET_KEY = None
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    MONGODB_URI = None
    
    ENCRYPTION_KEY = None
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5874').split(',')
    
    # Project Configuration
    PROJECT_ID = os.getenv('PROJECT_ID', 'llm-chat-auditor')
    
    @classmethod
    def load_secrets(cls):
        """Load secrets from Google Secret Manager with retry logic"""
        if PROJECT_ID:
            logger.info("Loading secrets from Secret Manager...")
            
            try:
                client = secretmanager.SecretManagerServiceClient()
                logger.info("Secret Manager client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Secret Manager client: {e}")
                raise
            
            secrets_to_load = {
                'MONGODB_URI': 'mongodb-uri',
                'FLASK_SECRET_KEY': 'flask-secret-key',
                'ENCRYPTION_KEY': 'api-encryption-key'
            }
            
            for attr_name, secret_name in secrets_to_load.items():
                max_retries = 3
                retry_delay = 2
                
                for attempt in range(max_retries):
                    try:
                        logger.info(f"Attempting to load secret '{secret_name}' (attempt {attempt + 1}/{max_retries})")
                        
                        # Build the resource name
                        name = f"projects/{cls.PROJECT_ID}/secrets/{secret_name}/versions/latest"
                        
                        # Access the secret version
                        response = client.access_secret_version(request={"name": name})
                        secret_value = response.payload.data.decode("UTF-8")
                        
                        # Set the attribute
                        setattr(cls, attr_name, secret_value)
                        logger.info(f"Successfully loaded secret '{secret_name}'")
                        break
                        
                    except Exception as e:
                        logger.error(f"Failed to load secret '{secret_name}' (attempt {attempt + 1}/{max_retries}): {e}")
                        
                        if attempt < max_retries - 1:
                            logger.info(f"Retrying in {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                        else:
                            logger.error(f"Failed to load secret '{secret_name}' after {max_retries} attempts")
                            raise ValueError(f"Failed to load secret '{secret_name}': {e}")
        else:
            logger.info("Loading secrets from environment variables (development mode)")
            cls.MONGODB_URI = os.getenv('MONGODB_URI')
            cls.FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
            cls.ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'dev-encryption-key-change-in-production')
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        logger.info("Validating configuration...")
        
        # Load secrets first
        cls.load_secrets()
        
        # Validate required fields
        if not cls.MONGODB_URI:
            raise ValueError("MONGODB_URI is required")
        
        if not cls.FLASK_SECRET_KEY:
            raise ValueError("FLASK_SECRET_KEY is required")
        
        if not cls.ENCRYPTION_KEY:
            raise ValueError("ENCRYPTION_KEY is required")
        
        logger.info("Configuration validation passed")
        return True

# Create config instance
config = Config()
config.validate()
