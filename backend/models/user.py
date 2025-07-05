from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, EmailStr, Field
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv
import uuid
from flask_login import UserMixin

load_dotenv()

ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

class User(BaseModel, UserMixin):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Encrypted API keys
    claude_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        """Required by Flask-Login"""
        return self.id

    def to_db_document(self) -> dict:
        return {
            "_id": self.id,
            "email": self.email,
            "password_hash": self.password_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "claude_api_key": self.claude_api_key,
            "gemini_api_key": self.gemini_api_key,
            "openai_api_key": self.openai_api_key,
            "deepseek_api_key": self.deepseek_api_key
        }

    @classmethod
    def from_db_document(cls, doc: dict) -> 'User':
        return cls(
            id=doc["_id"],
            email=doc["email"],
            password_hash=doc["password_hash"],
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            claude_api_key=doc.get("claude_api_key"),
            gemini_api_key=doc.get("gemini_api_key"),
            openai_api_key=doc.get("openai_api_key"),
            deepseek_api_key=doc.get("deepseek_api_key")
        )

    @staticmethod
    def encrypt_api_key(api_key: str) -> str:
        if not api_key:
            return None
        return cipher_suite.encrypt(api_key.encode()).decode()

    @staticmethod
    def decrypt_api_key(encrypted_key: str) -> str:
        if not encrypted_key:
            return None
        return cipher_suite.decrypt(encrypted_key.encode()).decode()

    def get_available_models(self) -> Dict[str, bool]:
        """Returns a dictionary of available models based on API keys"""
        return {
            "claude": bool(self.claude_api_key),
            "gemini": bool(self.gemini_api_key),
            "chatgpt": bool(self.openai_api_key),
            "deepseek": bool(self.deepseek_api_key)
        } 