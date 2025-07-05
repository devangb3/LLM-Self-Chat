from typing import Optional, Dict
from pymongo.database import Database
from models.user import User

class UserRepository:
    def __init__(self, db: Database):
        self.db = db
        self.collection = db.users
    
    def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        user_doc = self.collection.find_one({"_id": user_id})
        return User.from_db_document(user_doc) if user_doc else None
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        user_doc = self.collection.find_one({"email": email})
        return User.from_db_document(user_doc) if user_doc else None
    
    def create(self, user: User) -> bool:
        """Create a new user"""
        try:
            result = self.collection.insert_one(user.to_db_document())
            return result.inserted_id is not None
        except Exception:
            return False
    
    def update_api_keys(self, user_id: str, api_keys: Dict[str, str]) -> bool:
        """Update API keys for a user"""
        updates = {}
        for model, key in api_keys.items():
            if key and key.strip():
                updates[f"{model}_api_key"] = User.encrypt_api_key(key)
        
        if not updates:
            return False
        
        result = self.collection.update_one(
            {"_id": user_id},
            {"$set": updates}
        )
        return result.modified_count > 0
    
    def get_api_key(self, user_id: str, model_name: str) -> Optional[str]:
        """Get encrypted API key for a specific model"""
        user_doc = self.collection.find_one(
            {"_id": user_id}, 
            {f"{model_name}_api_key": 1}
        )
        return user_doc.get(f"{model_name}_api_key") if user_doc else None
    
    def get_available_models(self, user_id: str) -> Dict[str, bool]:
        """Get available models for a user"""
        user_doc = self.collection.find_one(
            {"_id": user_id},
            {"claude_api_key": 1, "gemini_api_key": 1, "openai_api_key": 1, "deepseek_api_key": 1}
        )
        if not user_doc:
            return {}
        
        return {
            "claude": bool(user_doc.get("claude_api_key")),
            "gemini": bool(user_doc.get("gemini_api_key")),
            "chatgpt": bool(user_doc.get("openai_api_key")),
            "deepseek": bool(user_doc.get("deepseek_api_key"))
        } 