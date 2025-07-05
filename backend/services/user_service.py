from typing import Optional, Dict, Tuple
from repositories.user_repository import UserRepository
from models.user import User
import bcrypt

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def register_user(self, email: str, password: str) -> Tuple[bool, str]:
        """Register a new user"""
        existing_user = self.user_repository.find_by_email(email)
        if existing_user:
            return False, "Email already registered"
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        new_user = User(email=email, password_hash=password_hash)
        success = self.user_repository.create(new_user)
        
        if success:
            return True, "User registered successfully"
        else:
            return False, "Failed to create user"
    
    def authenticate_user(self, email: str, password: str) -> Tuple[Optional[User], str]:
        """Authenticate a user"""
        user = self.user_repository.find_by_email(email)
        if not user:
            return None, "Invalid email or password"
        
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return None, "Invalid email or password"
        
        return user, "Authentication successful"
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.user_repository.find_by_id(user_id)
    
    def update_api_keys(self, user_id: str, api_keys: Dict[str, str]) -> Tuple[bool, str]:
        """Update API keys for a user"""
        if not api_keys:
            return False, "No valid API keys provided"
        
        success = self.user_repository.update_api_keys(user_id, api_keys)
        if success:
            return True, "API keys updated successfully"
        else:
            return False, "No changes were made to API keys"
    
    def get_api_key_decrypted(self, user_id: str, model_name: str) -> Optional[str]:
        """Get decrypted API key for a specific model"""
        encrypted_key = self.user_repository.get_api_key(user_id, model_name)
        if encrypted_key:
            return User.decrypt_api_key(encrypted_key)
        return None
    
    def get_available_models(self, user_id: str) -> Dict[str, bool]:
        """Get available models for a user"""
        return self.user_repository.get_available_models(user_id) 