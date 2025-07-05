import os
import uuid # For new ID generation if needed directly, though Pydantic models handle it
from flask import Flask, jsonify, request, session
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference # ReadPreference might be removed if not using replica set or if default is fine
from datetime import datetime, timezone # Added timezone
# ObjectId might not be needed if all our IDs are strings now
# from bson.objectid import ObjectId 

from pydantic import ValidationError
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import bcrypt
from functools import wraps

from config import config

app = Flask(__name__)
app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5874")

# MongoDB Setup
client = MongoClient(config.MONGODB_URI)
db = client.llm_chat_app 

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

# Configure CORS to allow credentials
CORS(app, resources={r"/*": {"origins": "http://localhost:5874", "supports_credentials": True}})

from llm_clients import get_claude_response, get_gemini_response, get_chatgpt_response, get_deepseek_response
from models import Conversation, Message
from models.user import User

ALL_LLMS = {
    "claude": get_claude_response,
    "gemini": get_gemini_response,
    "chatgpt": get_chatgpt_response,
    "deepseek": get_deepseek_response
}

@login_manager.user_loader
def load_user(user_id):
    user_doc = db.users.find_one({"_id": user_id})
    if user_doc:
        return User.from_db_document(user_doc)
    return None

def socket_auth_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        return f(*args, **kwargs)
    return wrapped

@app.route("/")
def index():
    return jsonify({"message": "LLM Chat App Backend Running"})

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('response', {'data': 'Connected to backend'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('trigger_next_llm')
def handle_trigger_next_llm(data):
    app.logger.info(f'Received trigger_next_llm data: {data}')
    try:
        conversation_id = data.get('conversation_id')
        if not conversation_id:
            emit('error', {'message': 'Missing conversation_id in trigger_next_llm event'})
            return

        conv_doc = db.conversations.find_one({"_id": conversation_id})
        if not conv_doc:
            emit('error', {'message': f'Conversation {conversation_id} not found'})
            return
        
        current_conversation = Conversation.from_db_document(conv_doc)
        system_prompt = current_conversation.system_prompt
        llm_participants = current_conversation.llm_participants

        if not llm_participants:
            emit('info', {'message': 'No LLM participants in this conversation to respond.'})
            return

        all_messages_cursor = db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", 1)
        
        all_db_messages = list(all_messages_cursor)
        
        history_docs_for_llm = []
        current_prompt_text = ""
        next_llm_name = ""

        if not all_db_messages: # No messages yet, first LLM to speak
            next_llm_name = llm_participants[0]
            current_prompt_text = "Hello! Please introduce yourself based on the system prompt and start the conversation."
            history_docs_for_llm = []
        else:
            last_msg_doc = all_db_messages[-1]
            last_msg_obj = Message.from_db_document(last_msg_doc)
            
            if last_msg_obj.sender_type == 'auditor':
                # This case should ideally not happen with the new flow.
                # If it does, we might default to the first LLM or an error.
                # For now, let's assume the last message is from an LLM.
                # If an auditor message somehow gets in, the next LLM will respond to it.
                app.logger.warning(f"Last message in conversation {conversation_id} was from auditor. Proceeding with next LLM.")
                # Who is next LLM? If auditor was last, pick first LLM from participants.
                # Or, if we want strict LLM-to-LLM, this could be an error or special handling.
                # Let's assume the last message *should* have been an LLM.
                # For robustness, pick the first LLM if the last one wasn't an LLM we can find in participants.
                last_llm_name_for_sequence = llm_participants[-1] # Default to ensure a cycle
                if last_msg_obj.llm_name and last_msg_obj.llm_name in llm_participants:
                    last_llm_name_for_sequence = last_msg_obj.llm_name
                
                try:
                    last_llm_index = llm_participants.index(last_llm_name_for_sequence)
                    next_llm_index = (last_llm_index + 1) % len(llm_participants)
                    next_llm_name = llm_participants[next_llm_index]
                except ValueError: # last_llm_name not in participants
                    next_llm_name = llm_participants[0] # Default to first participant

            elif last_msg_obj.sender_type == 'llm':
                last_llm_name = last_msg_obj.llm_name
                try:
                    last_llm_index = llm_participants.index(last_llm_name)
                    next_llm_index = (last_llm_index + 1) % len(llm_participants)
                    next_llm_name = llm_participants[next_llm_index]
                except ValueError:
                    # Last LLM not in current participant list (e.g., list was changed)
                    # Default to the first LLM in the current list
                    app.logger.warning(f"Last LLM {last_llm_name} not in participants {llm_participants}. Defaulting to first.")
                    next_llm_name = llm_participants[0]
            else: # Should not happen
                 emit('error', {'message': f'Invalid sender_type for last message: {last_msg_obj.sender_type}'})
                 return

            current_prompt_text = last_msg_obj.content
            history_docs_for_llm = all_db_messages # LLM client might handle taking last as prompt. Let's pass all.
                                                  # Or, more accurately, pass all *but* the last as history, and last as prompt.
                                                  # The llm_to_call functions expect (prompt, system_prompt, chat_history)
                                                  # So history should be messages *before* the current_prompt_text's message.
            history_docs_for_llm = all_db_messages[:-1] if len(all_db_messages) > 0 else []


        llm_to_call = ALL_LLMS.get(next_llm_name)
        if not llm_to_call:
            emit('error', {'message': f'LLM client for {next_llm_name} not found or not implemented.'})
            return

        chat_history_for_llm = []
        for msg_doc_db in history_docs_for_llm: # These are messages BEFORE the current_prompt_text
            msg_obj = Message.from_db_document(msg_doc_db)
            role = "user" 
            if msg_obj.sender_type == "llm":
                if msg_obj.llm_name == next_llm_name: # This LLM's own past messages
                    role = "assistant"
                else: # Messages from other LLMs become "user" context for the current LLM
                    role = "user"
            elif msg_obj.sender_type == "auditor": # Auditor messages form "user" context
                role = "user"

            app.logger.info(f"[App TriggerNextLLM] History loop - Current LLM: {next_llm_name}, Sender: {msg_obj.sender_id} ({msg_obj.sender_type}, name: {msg_obj.llm_name}), Assigned base role: {role}")

            if next_llm_name == "gemini":
                gemini_role = "model" if role == "assistant" else "user"
                app.logger.info(f"[App TriggerNextLLM] For Gemini, mapping base role '{role}' to '{gemini_role}' for history message: {msg_obj.content[:50]}...")
                chat_history_for_llm.append({"role": gemini_role, "parts": [{"text": msg_obj.content}] })
            else:
                chat_history_for_llm.append({"role": role, "content": msg_obj.content})
        
        app.logger.info(f"[App TriggerNextLLM] Calling LLM {next_llm_name} with prompt: '{current_prompt_text[:100]}...' and history of {len(chat_history_for_llm)} messages.")

        api_key = getattr(current_user, f"{next_llm_name}_api_key", None)
        if not api_key:
            emit('error', {'message': f'API key for {next_llm_name} not found.'})
            return

        llm_response_text = llm_to_call(
            api_key=User.decrypt_api_key(api_key),
            prompt=current_prompt_text, 
            system_prompt=system_prompt, 
            chat_history=chat_history_for_llm
        )

        llm_msg_data = {
            "conversation_id": conversation_id,
            "sender_type": 'llm',
            "sender_id": next_llm_name, # Storing the LLM's unique key/name
            "llm_name": next_llm_name,  # Storing the LLM's unique key/name also here for display
            "content": llm_response_text
            # created_at will be defaulted by Pydantic model
        }
        llm_msg = Message(**llm_msg_data)
        db.messages.insert_one(llm_msg.to_db_document())
        emit('message_update', llm_msg.model_dump(mode='json'), broadcast=True)

    except ValidationError as e:
        app.logger.error(f"Pydantic validation error in trigger_next_llm: {e.errors()}")
        emit('error', {'message': f'Data validation error: {e.errors()}'})
    except Exception as e:
        app.logger.error(f"Error in trigger_next_llm: {e}", exc_info=True)
        emit('error', {'message': 'An unexpected error occurred while triggering the next LLM.'})

@socketio.on('set_system_prompt')
def handle_set_system_prompt(data):
    app.logger.info(f"Received set_system_prompt: {data}")
    try:
        conversation_id = data.get('conversation_id')
        new_prompt = data.get('prompt')

        if not conversation_id or new_prompt is None:
            emit('error', {'message': 'Missing conversation_id or prompt for set_system_prompt'})
            return

        # Find the conversation and update its system_prompt
        result = db.conversations.update_one(
            {'_id': conversation_id},
            {'$set': {'system_prompt': new_prompt, 'updated_at': datetime.now(timezone.utc)}}
        )

        if result.matched_count == 0:
            emit('error', {'message': f'Conversation {conversation_id} not found for updating system prompt.'})
            return
        
        app.logger.info(f"System prompt updated for conversation {conversation_id}. Matched: {result.matched_count}, Modified: {result.modified_count}")
        emit('system_prompt_updated', {'conversation_id': conversation_id, 'prompt': new_prompt}, broadcast=True)

    except Exception as e:
        app.logger.error(f"Error in set_system_prompt: {e}", exc_info=True)
        emit('error', {'message': 'Failed to set system prompt.'})

@app.route("/api/auth/register", methods=["POST"])
def register():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Check if user already exists
        if db.users.find_one({"email": email}):
            return jsonify({"error": "Email already registered"}), 400

        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Create new user
        new_user = User(
            email=email,
            password_hash=password_hash
        )

        db.users.insert_one(new_user.to_db_document())
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return jsonify({"message": "Please use POST method to login"}), 200

    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user_doc = db.users.find_one({"email": email})
        if not user_doc:
            return jsonify({"error": "Invalid email or password"}), 401

        user = User.from_db_document(user_doc)
        if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({"error": "Invalid email or password"}), 401

        login_user(user, remember=True)
        return jsonify({
            "message": "Logged in successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "available_models": user.get_available_models()
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})

@app.route("/api/auth/user", methods=["GET"])
@login_required
def get_user():
    return jsonify({
        "id": current_user.id,
        "email": current_user.email,
        "available_models": current_user.get_available_models()
    })

@app.route("/api/auth/api-keys", methods=["POST"])
@login_required
def update_api_keys():
    try:
        data = request.json
        updates = {}
        
        for model in ["claude", "gemini", "openai", "deepseek"]:
            key = data.get(f"{model}_api_key")
            if key is not None and key.strip():
                updates[f"{model}_api_key"] = User.encrypt_api_key(key)

        if not updates:
            return jsonify({"error": "No valid API keys provided"}), 400

        result = db.users.update_one(
            {"_id": current_user.id},
            {"$set": updates}
        )

        if result.modified_count == 0:
            return jsonify({"message": "No changes were made to API keys"}), 200

        return jsonify({
            "message": "API keys updated successfully",
            "updated_keys": list(updates.keys())
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/conversations", methods=["POST"])
@login_required
def create_conversation():
    try:
        
        data = request.json
        data["user_id"] = current_user.id
        new_conv_model = Conversation(**data)
        
        available_models = current_user.get_available_models()
        for llm_name in new_conv_model.llm_participants:
            if llm_name not in ALL_LLMS:
                return jsonify({"error": f"Unsupported LLM: {llm_name}"}), 400
            if not available_models.get(llm_name):
                app.logger.error(f"Available models: {available_models}")
                return jsonify({"error": f"No API key provided for {llm_name}"}), 400

        db_doc = new_conv_model.to_db_document()
        result = db.conversations.insert_one(db_doc)
        created_id = str(db_doc['_id'])

        app.logger.info(f"Conversation created with ID: {created_id}")
        
        if data.get("start_conversation", False) and new_conv_model.llm_participants:
            first_llm_name = new_conv_model.llm_participants[0]
            llm_to_call = ALL_LLMS.get(first_llm_name)
            if llm_to_call:
                api_key = getattr(current_user, f"{first_llm_name}_api_key", None)
                if not api_key:
                    return jsonify({"error": f"API key for {first_llm_name} not found"}), 400

                initial_prompt = "Hello! Please introduce yourself based on the system prompt and start the conversation."
                llm_response_text = llm_to_call(
                    api_key=User.decrypt_api_key(api_key),
                    prompt=initial_prompt, 
                    system_prompt=new_conv_model.system_prompt, 
                    chat_history=[]
                )
                
                llm_start_msg_data = {
                    "conversation_id": created_id,
                    "sender_type": 'llm',
                    "sender_id": first_llm_name,
                    "llm_name": first_llm_name,
                    "content": llm_response_text
                }
                llm_start_msg = Message(**llm_start_msg_data)
                db.messages.insert_one(llm_start_msg.to_db_document())

        return jsonify({"id": created_id, "message": "Conversation created successfully"})

    except ValidationError as e:
        app.logger.error(f"Pydantic validation error creating conversation: {e.errors()}")
        return jsonify({"error": "Invalid data for conversation", "details": e.errors()}), 400
    except Exception as e:
        app.logger.error(f"Error creating conversation: {e}", exc_info=True)
        return jsonify({"error": "Failed to create conversation"}), 500

@app.route("/api/conversations", methods=["GET"])
@login_required
def get_conversations():
    try:
        conv_cursor = db.conversations.find({"user_id": current_user.id}).sort("created_at", -1)
        conversations_list = []
        for conv_doc_db in conv_cursor:
            try:
                conversations_list.append(Conversation.from_db_document(conv_doc_db).model_dump(mode='json'))
            except Exception as e:
                app.logger.error(f"Error processing conversation {conv_doc_db.get('_id')}: {e}")
                continue
        return jsonify(conversations_list)
    except Exception as e:
        app.logger.error(f"Error in get_conversations: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch conversations"}), 500

@app.route("/api/conversations/<conversation_id>", methods=["GET"])
@login_required
def get_conversation_details(conversation_id: str):
    try:
        if not conversation_id or not isinstance(conversation_id, str):
            return jsonify({"error": "Invalid conversation_id format, must be a string."}), 400

        conv_doc_db = db.conversations.find_one({"_id": conversation_id})
        
        if not conv_doc_db:
            return jsonify({"error": "Conversation not found"}), 404
        
        conversation_model = Conversation.from_db_document(conv_doc_db)
        
        messages_cursor = db.messages.find({"conversation_id": conversation_id}).sort("created_at", 1)
        messages_list = []
        for msg_doc_db in messages_cursor:
            messages_list.append(Message.from_db_document(msg_doc_db).model_dump(mode='json'))
        
        conv_response = conversation_model.model_dump(mode='json')
        conv_response['messages'] = messages_list
        return jsonify(conv_response)

    except ValidationError as e:
        app.logger.error(f"Pydantic validation error in get_conversation_details for ID {conversation_id}: {e.errors()}", exc_info=True)
        return jsonify({"error": "Data validation error while fetching conversation.", "details": e.errors()}), 500
    except Exception as e:
        app.logger.error(f"Error in get_conversation_details for ID {conversation_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while fetching conversation details."}), 500

@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
@login_required
def delete_conversation(conversation_id: str):
    try:
        if not conversation_id or not isinstance(conversation_id, str):
            return jsonify({"error": "Invalid conversation_id format, must be a string."}), 400

        result = db.conversations.delete_one({"_id": conversation_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Conversation not found"}), 404
            
        db.messages.delete_many({"conversation_id": conversation_id})
        
        return jsonify({"message": "Conversation and associated messages deleted successfully"})

    except Exception as e:
        app.logger.error(f"Error deleting conversation {conversation_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while deleting the conversation."}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)