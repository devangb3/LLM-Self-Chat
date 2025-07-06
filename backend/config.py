import os
from dotenv import load_dotenv
from google.cloud import secretmanager


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
    if PROJECT_ID:
        flask_secret = get_gcp_secret('flask-secret-key')
        encryption_key = get_gcp_secret('api-encryption-key')
        mongodb_uri = get_gcp_secret('mongodb-uri')
        
        FLASK_SECRET_KEY = flask_secret or os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
        ENCRYPTION_KEY = encryption_key or os.getenv('ENCRYPTION_KEY')
        MONGODB_URI = mongodb_uri or os.getenv("MONGODB_URI")
    else:
        FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
        ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
        MONGODB_URI = os.getenv("MONGO_LOCAL_URI")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        missing_vars = []
        
        if not cls.FLASK_SECRET_KEY or cls.FLASK_SECRET_KEY == 'your-secret-key-here':
            missing_vars.append('FLASK_SECRET_KEY')
        
        if not cls.ENCRYPTION_KEY:
            missing_vars.append('ENCRYPTION_KEY')
        
        if not cls.MONGODB_URI:
            missing_vars.append('MONGODB_URI')
        
        if missing_vars:
            raise ValueError(f"Missing required configuration: {', '.join(missing_vars)}")

config = Config()
config.validate()
