from typing import Optional, List, Dict
from pymongo.database import Database
from models import Conversation, Message

class ConversationRepository:
    def __init__(self, db: Database):
        self.db = db
        self.conversations_collection = db.conversations
        self.messages_collection = db.messages
    
    def create_conversation(self, conversation: Conversation) -> str:
        """Create a new conversation"""
        doc = conversation.to_db_document()
        result = self.conversations_collection.insert_one(doc)
        return str(doc['_id'])
    
    def find_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """Find conversation by ID"""
        conv_doc = self.conversations_collection.find_one({"_id": conversation_id})
        return Conversation.from_db_document(conv_doc) if conv_doc else None
    
    def find_by_user_id(self, user_id: str) -> List[Conversation]:
        """Find all conversations for a user"""
        conv_cursor = self.conversations_collection.find({"user_id": user_id}).sort("created_at", -1)
        conversations = []
        for conv_doc in conv_cursor:
            try:
                conversations.append(Conversation.from_db_document(conv_doc))
            except Exception:
                continue
        return conversations
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and its messages"""
        conv_result = self.conversations_collection.delete_one({"_id": conversation_id})
        if conv_result.deleted_count > 0:
            self.messages_collection.delete_many({"conversation_id": conversation_id})
            return True
        return False
    
    def update_system_prompt(self, conversation_id: str, new_prompt: str) -> bool:
        """Update system prompt for a conversation"""
        from datetime import datetime, timezone
        result = self.conversations_collection.update_one(
            {'_id': conversation_id},
            {'$set': {'system_prompt': new_prompt, 'updated_at': datetime.now(timezone.utc)}}
        )
        return result.matched_count > 0
    
    def get_messages(self, conversation_id: str) -> List[Message]:
        """Get all messages for a conversation"""
        messages_cursor = self.messages_collection.find({"conversation_id": conversation_id}).sort("created_at", 1)
        messages = []
        for msg_doc in messages_cursor:
            messages.append(Message.from_db_document(msg_doc))
        return messages
    
    def add_message(self, message: Message) -> bool:
        """Add a new message to a conversation"""
        try:
            result = self.messages_collection.insert_one(message.to_db_document())
            return result.inserted_id is not None
        except Exception:
            return False
    
    def get_conversation_with_messages(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation with all its messages"""
        conv_doc = self.conversations_collection.find_one({"_id": conversation_id})
        if not conv_doc:
            return None
        
        conversation = Conversation.from_db_document(conv_doc)
        messages = self.get_messages(conversation_id)
        
        conv_response = conversation.model_dump(mode='json')
        conv_response['messages'] = [msg.model_dump(mode='json') for msg in messages]
        return conv_response 