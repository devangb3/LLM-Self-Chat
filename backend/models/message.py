import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# Example structure for a Message document in MongoDB

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str  # This will be the string UUID of the Conversation
    sender_type: str  # "llm" or "auditor"
    sender_id: str    # LLM name (e.g., "claude", "gemini") or auditor's user ID
    llm_name: Optional[str] = None # Specific LLM that sent the message (if sender_type is "llm")
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

    def to_db_document(self) -> Dict[str, Any]:
        """Converts the Pydantic model to a dictionary suitable for MongoDB, mapping 'id' to '_id'."""
        doc = self.model_dump(exclude_none=True)
        doc["_id"] = doc.pop("id")
        # conversation_id is already a string, so no special handling needed for DB if it's just stored as a string.
        # If it were an ObjectId before, this simplifies it.
        return doc

    @classmethod
    def from_db_document(cls, doc: Dict[str, Any]) -> "Message":
        """Creates a Pydantic model instance from a MongoDB document, mapping '_id' to 'id'."""
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)

# Example Usage (for testing this file):
if __name__ == "__main__":
    msg_data = {
        "conversation_id": str(uuid.uuid4()), # Example conversation UUID
        "sender_type": "llm",
        "sender_id": "claude",
        "llm_name": "claude-3-opus",
        "content": "Hello from Claude!"
    }
    message = Message(**msg_data)
    print("Pydantic Message:", message)
    print("Message ID:", message.id)
    
    db_doc = message.to_db_document()
    print("To DB Document:", db_doc)
    
    retrieved_msg = Message.from_db_document(db_doc)
    print("From DB Document:", retrieved_msg)
    assert retrieved_msg.id == message.id
    assert retrieved_msg.content == message.content 