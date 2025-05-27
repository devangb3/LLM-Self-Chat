import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Conversation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    system_prompt: str
    llm_participants: List[str]
    auditor_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:

        from_attributes = True

    def to_db_document(self) -> Dict[str, Any]:
        """Converts the Pydantic model to a dictionary suitable for MongoDB, mapping 'id' to '_id'."""
        doc = self.model_dump(exclude_none=True)
        doc["_id"] = doc.pop("id")
        return doc

    @classmethod
    def from_db_document(cls, doc: Dict[str, Any]) -> "Conversation":
        """Creates a Pydantic model instance from a MongoDB document, mapping '_id' to 'id'."""
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)

# Example Usage (for testing this file):
if __name__ == "__main__":
    conv_data = {
        "system_prompt": "You are a helpful AI.",
        "llm_participants": ["chatgpt", "claude"],
        "auditor_id": "user123"
    }
    conversation = Conversation(**conv_data)
    print("Pydantic Conversation:", conversation)
    print("Conversation ID:", conversation.id)
    
    db_doc = conversation.to_db_document()
    print("To DB Document:", db_doc)
    
    retrieved_conv = Conversation.from_db_document(db_doc)
    print("From DB Document:", retrieved_conv)
    assert retrieved_conv.id == conversation.id
    assert retrieved_conv.system_prompt == conversation.system_prompt 