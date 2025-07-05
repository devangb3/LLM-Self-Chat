from typing import Optional, Dict
from datetime import datetime, timedelta
import jwt
from config import config
from models.user import User

class AuthService:
    def __init__(self):
        self.secret_key = config.FLASK_SECRET_KEY
        self.algorithm = "HS256"
        self.token_expiry_hours = 24
    
    def create_access_token(self, user: User) -> str:
        """Create a JWT access token for a user"""
        payload = {
            "user_id": user.id,
            "email": user.email,
            "exp": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_user_id_from_token(self, token: str) -> Optional[str]:
        """Extract user ID from token"""
        payload = self.verify_token(token)
        return payload.get("user_id") if payload else None 