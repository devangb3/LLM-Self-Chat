from flask import jsonify, request
from flask_login import current_user
from services.conversation_service import ConversationService

class ConversationController:
    def __init__(self, conversation_service: ConversationService):
        self.conversation_service = conversation_service
    
    def create_conversation(self):
        """Create a new conversation"""
        try:
            data = request.json
            success, message, conversation_id = self.conversation_service.create_conversation(
                current_user.id, data
            )
            
            if success:
                return jsonify({"id": conversation_id, "message": message})
            else:
                return jsonify({"error": message}), 400
                
        except Exception as e:
            return jsonify({"error": f"Failed to create conversation: {str(e)}"}), 500
    
    def get_conversations(self):
        """Get all conversations for the current user"""
        try:
            conversations = self.conversation_service.get_conversations(current_user.id)
            return jsonify(conversations)
        except Exception as e:
            return jsonify({"error": f"Failed to fetch conversations: {str(e)}"}), 500
    
    def get_conversation_details(self, conversation_id: str):
        """Get conversation details with messages"""
        try:
            if not conversation_id or not isinstance(conversation_id, str):
                return jsonify({"error": "Invalid conversation_id format, must be a string."}), 400
            
            conversation_data = self.conversation_service.get_conversation_details(conversation_id)
            if not conversation_data:
                return jsonify({"error": "Conversation not found"}), 404
            
            return jsonify(conversation_data)
            
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred while fetching conversation details: {str(e)}"}), 500
    
    def delete_conversation(self, conversation_id: str):
        """Delete a conversation"""
        try:
            if not conversation_id or not isinstance(conversation_id, str):
                return jsonify({"error": "Invalid conversation_id format, must be a string."}), 400
            
            success = self.conversation_service.delete_conversation(conversation_id)
            if not success:
                return jsonify({"error": "Conversation not found"}), 404
            
            return jsonify({"message": "Conversation and associated messages deleted successfully"})
            
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred while deleting the conversation: {str(e)}"}), 500 