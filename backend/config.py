import os
from dotenv import load_dotenv
from google.cloud import secretmanager

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")

def get_gcp_secret(secret_id, version_id="latest"):
    """
    Retrieves a secret from Google Cloud Secret Manager.
    """
    client = secretmanager.SecretManagerServiceClient()

    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"

    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        raise RuntimeError(f"Failed to access secret {secret_id}: {e}")

class Config:
    if PROJECT_ID:
        FLASK_SECRET_KEY = get_gcp_secret('flask-secret-key')
        ENCRYPTION_KEY = get_gcp_secret('api-encryption-key')
    else:
        FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
        ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    MONGODB_URI = os.getenv("MONGODB_URI")
    
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
