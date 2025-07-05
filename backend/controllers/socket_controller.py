from flask_socketio import emit, disconnect
from flask_login import current_user, login_user
from services.conversation_service import ConversationService
from services.user_service import UserService
from services.auth_service import AuthService
from flask import session, request

class SocketController:
    def __init__(self, conversation_service: ConversationService, user_service: UserService):
        self.conversation_service = conversation_service
        self.user_service = user_service
        self.auth_service = AuthService()
    
    def handle_connect(self):
        """Handle client connection with authentication"""
        try:
            auth_token = request.args.get('token') or request.headers.get('Authorization')
            
            if auth_token and auth_token.startswith('Bearer '):
                auth_token = auth_token[7:]
            
            if auth_token:
                user_id = self.auth_service.get_user_id_from_token(auth_token)
                if user_id:
                    user = self.user_service.get_user_by_id(user_id)
                    if user:
                        login_user(user, remember=True)
                        print(f'Client connected: {user.email}')
                        emit('response', {'data': 'Connected to backend', 'authenticated': True})
                        return
            
            # Fallback: try to get user from session
            if current_user.is_authenticated:
                print(f'Client connected: {current_user.email}')
                emit('response', {'data': 'Connected to backend', 'authenticated': True})
                return
            
            print('Client connected: unauthenticated')
            emit('response', {'data': 'Connected to backend', 'authenticated': False})
            
        except Exception as e:
            print(f'Connection error: {e}')
            emit('response', {'data': 'Connection error', 'authenticated': False})
    
    def handle_disconnect(self):
        """Handle client disconnection"""
        if current_user.is_authenticated:
            print(f'Client disconnected: {current_user.email}')
        else:
            print('Client disconnected: unauthenticated')
    
    def _ensure_authenticated(self):
        """Ensure user is authenticated for socket operations"""
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return False
        return True
    
    def handle_trigger_next_llm(self, data):
        """Handle trigger_next_llm event"""
        try:
            if not self._ensure_authenticated():
                return
            
            conversation_id = data.get('conversation_id')
            if not conversation_id:
                emit('error', {'message': 'Missing conversation_id in trigger_next_llm event'})
                return
            
            success, message, llm_message = self.conversation_service.trigger_next_llm(
                conversation_id, current_user.id
            )
            
            if success and llm_message:
                emit('message_update', llm_message.model_dump(mode='json'), broadcast=True)
            else:
                emit('error', {'message': message})
                
        except Exception as e:
            emit('error', {'message': f'An unexpected error occurred while triggering the next LLM: {str(e)}'})
    
    def handle_set_system_prompt(self, data):
        """Handle set_system_prompt event"""
        try:
            if not self._ensure_authenticated():
                return
            
            conversation_id = data.get('conversation_id')
            new_prompt = data.get('prompt')

            if not conversation_id or new_prompt is None:
                emit('error', {'message': 'Missing conversation_id or prompt for set_system_prompt'})
                return

            success = self.conversation_service.update_system_prompt(conversation_id, new_prompt)
            
            if success:
                emit('system_prompt_updated', {
                    'conversation_id': conversation_id, 
                    'prompt': new_prompt
                }, broadcast=True)
            else:
                emit('error', {'message': f'Conversation {conversation_id} not found for updating system prompt.'})

        except Exception as e:
            emit('error', {'message': f'Failed to set system prompt: {str(e)}'}) 