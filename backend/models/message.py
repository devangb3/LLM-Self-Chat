import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_type: str
    sender_id: str
    llm_name: Optional[str] = None
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        from_attributes = True

    def to_db_document(self) -> Dict[str, Any]:
        """Converts the Pydantic model to a dictionary suitable for MongoDB, mapping 'id' to '_id'."""
        doc = self.model_dump(exclude_none=True)
        doc["_id"] = doc.pop("id")
        return doc

    @classmethod
    def from_db_document(cls, doc: Dict[str, Any]) -> "Message":
        """Creates a Pydantic model instance from a MongoDB document, mapping '_id' to 'id'."""
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)

if __name__ == "__main__":
    msg_data = {
        "conversation_id": str(uuid.uuid4()),
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