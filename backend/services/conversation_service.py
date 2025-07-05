from typing import Optional, List, Dict, Tuple
from pydantic import ValidationError
from repositories.conversation_repository import ConversationRepository
from services.user_service import UserService
from models import Conversation, Message
from llm_clients import get_claude_response, get_gemini_response, get_chatgpt_response, get_deepseek_response

ALL_LLMS = {
    "claude": get_claude_response,
    "gemini": get_gemini_response,
    "chatgpt": get_chatgpt_response,
    "deepseek": get_deepseek_response
}

class ConversationService:
    def __init__(self, conversation_repository: ConversationRepository, user_service: UserService):
        self.conversation_repository = conversation_repository
        self.user_service = user_service
    
    def create_conversation(self, user_id: str, conversation_data: dict) -> Tuple[bool, str, Optional[str]]:
        """Create a new conversation"""
        try:
            conversation_data["user_id"] = user_id
            new_conv = Conversation(**conversation_data)
            
            # Validate that user has API keys for all LLM participants
            available_models = self.user_service.get_available_models(user_id)
            for llm_name in new_conv.llm_participants:
                if llm_name not in ALL_LLMS:
                    return False, f"Unsupported LLM: {llm_name}", None
                if not available_models.get(llm_name):
                    return False, f"No API key provided for {llm_name}", None
            
            conversation_id = self.conversation_repository.create_conversation(new_conv)
            
            if conversation_data.get("start_conversation", False) and new_conv.llm_participants:
                success, message = self._start_conversation(conversation_id, new_conv)
                if not success:
                    return False, message, None
            
            return True, "Conversation created successfully", conversation_id
            
        except ValidationError as e:
            return False, f"Invalid data for conversation: {e.errors()}", None
        except Exception as e:
            return False, f"Failed to create conversation: {str(e)}", None
    
    def get_conversations(self, user_id: str) -> List[Dict]:
        """Get all conversations for a user"""
        conversations = self.conversation_repository.find_by_user_id(user_id)
        return [conv.model_dump(mode='json') for conv in conversations]
    
    def get_conversation_details(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation with all messages"""
        return self.conversation_repository.get_conversation_with_messages(conversation_id)
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation"""
        return self.conversation_repository.delete_conversation(conversation_id)
    
    def update_system_prompt(self, conversation_id: str, new_prompt: str) -> bool:
        """Update system prompt for a conversation"""
        return self.conversation_repository.update_system_prompt(conversation_id, new_prompt)
    
    def trigger_next_llm(self, conversation_id: str, user_id: str) -> Tuple[bool, str, Optional[Message]]:
        """Trigger the next LLM in the conversation"""
        try:
            conversation = self.conversation_repository.find_by_id(conversation_id)
            if not conversation:
                return False, f"Conversation {conversation_id} not found", None
            
            if not conversation.llm_participants:
                return False, "No LLM participants in this conversation to respond.", None
            
            messages = self.conversation_repository.get_messages(conversation_id)
            
            next_llm_name, current_prompt_text, history_messages = self._determine_next_llm(
                conversation.llm_participants, messages
            )
            
            llm_to_call = ALL_LLMS.get(next_llm_name)
            if not llm_to_call:
                return False, f"LLM client for {next_llm_name} not found or not implemented.", None
            
            api_key = self.user_service.get_api_key_decrypted(user_id, next_llm_name)
            if not api_key:
                return False, f"API key for {next_llm_name} not found.", None
            
            chat_history = self._prepare_chat_history(history_messages, next_llm_name)
            
            llm_response_text = llm_to_call(
                api_key=api_key,
                prompt=current_prompt_text,
                system_prompt=conversation.system_prompt,
                chat_history=chat_history
            )
            
            llm_msg_data = {
                "conversation_id": conversation_id,
                "sender_type": 'llm',
                "sender_id": next_llm_name,
                "llm_name": next_llm_name,
                "content": llm_response_text
            }
            llm_msg = Message(**llm_msg_data)
            
            if self.conversation_repository.add_message(llm_msg):
                return True, "LLM response generated successfully", llm_msg
            else:
                return False, "Failed to save LLM response", None
                
        except Exception as e:
            return False, f"Error triggering next LLM: {str(e)}", None
    
    def _start_conversation(self, conversation_id: str, conversation: Conversation) -> Tuple[bool, str]:
        """Start a conversation with the first LLM"""
        try:
            first_llm_name = conversation.llm_participants[0]
            llm_to_call = ALL_LLMS.get(first_llm_name)
            if not llm_to_call:
                return False, f"LLM client for {first_llm_name} not found"
            
            api_key = self.user_service.get_api_key_decrypted(conversation.user_id, first_llm_name)
            if not api_key:
                return False, f"API key for {first_llm_name} not found"
            
            initial_prompt = "Hello! Please introduce yourself based on the system prompt and start the conversation."
            llm_response_text = llm_to_call(
                api_key=api_key,
                prompt=initial_prompt,
                system_prompt=conversation.system_prompt,
                chat_history=[]
            )
            
            llm_start_msg_data = {
                "conversation_id": conversation_id,
                "sender_type": 'llm',
                "sender_id": first_llm_name,
                "llm_name": first_llm_name,
                "content": llm_response_text
            }
            llm_start_msg = Message(**llm_start_msg_data)
            
            if self.conversation_repository.add_message(llm_start_msg):
                return True, "Conversation started successfully"
            else:
                return False, "Failed to save initial LLM message"
                
        except Exception as e:
            return False, f"Error starting conversation: {str(e)}"
    
    def _determine_next_llm(self, llm_participants: List[str], messages: List[Message]) -> Tuple[str, str, List[Message]]:
        """Determine which LLM should respond next and what the prompt should be"""
        if not messages:
            return llm_participants[0], "Hello! Please introduce yourself based on the system prompt and start the conversation.", []
        
        last_msg = messages[-1]
        history_messages = messages[:-1] if len(messages) > 0 else []
        
        if last_msg.sender_type == 'auditor':
            if last_msg.llm_name and last_msg.llm_name in llm_participants:
                last_llm_name = last_msg.llm_name
            else:
                last_llm_name = llm_participants[0]
        elif last_msg.sender_type == 'llm':
            last_llm_name = last_msg.llm_name
        else:
            raise ValueError(f"Invalid sender_type for last message: {last_msg.sender_type}")
        
        try:
            last_llm_index = llm_participants.index(last_llm_name)
            next_llm_index = (last_llm_index + 1) % len(llm_participants)
            next_llm_name = llm_participants[next_llm_index]
        except ValueError:
            next_llm_name = llm_participants[0]
        
        return next_llm_name, last_msg.content, history_messages
    
    def _prepare_chat_history(self, messages: List[Message], next_llm_name: str) -> List[Dict]:
        """Prepare chat history for LLM API call"""
        chat_history = []
        for msg in messages:
            role = "user"
            if msg.sender_type == "llm":
                if msg.llm_name == next_llm_name:
                    role = "assistant"
                else:
                    role = "user"
            elif msg.sender_type == "auditor":
                role = "user"
            
            if next_llm_name == "gemini":
                gemini_role = "model" if role == "assistant" else "user"
                chat_history.append({"role": gemini_role, "parts": [{"text": msg.content}]})
            else:
                chat_history.append({"role": role, "content": msg.content})
        
        return chat_history 