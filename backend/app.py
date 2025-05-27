import os
import uuid # For new ID generation if needed directly, though Pydantic models handle it
from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
from pymongo import MongoClient, ReadPreference # ReadPreference might be removed if not using replica set or if default is fine
from datetime import datetime, timezone # Added timezone
# ObjectId might not be needed if all our IDs are strings now
# from bson.objectid import ObjectId 

from pydantic import ValidationError

load_dotenv() # Load environment variables from .env

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "supersecretkey") # Add a Flask secret key for session management
socketio = SocketIO(app, cors_allowed_origins="*") # Allow all origins for now, restrict in production

# MongoDB Setup
mongo_uri = os.getenv("MONGODB_URI")
if not mongo_uri:
    raise ValueError("MONGODB_URI not found in environment variables")
client = MongoClient(mongo_uri)
db = client.llm_chat_app # Or client["llm_chat_app"]

# Import LLM clients and models
from llm_clients import get_claude_response, get_gemini_response, get_chatgpt_response, get_deepseek_response
from models import Conversation, Message # These are now Pydantic models

ALL_LLMS = {
    "claude": get_claude_response,
    "gemini": get_gemini_response,
    "chatgpt": get_chatgpt_response,
    "deepseek": get_deepseek_response
}

# Enable CORS for all routes
from flask_cors import CORS
CORS(app, resources={r"/*": {"origins": "*"}}) # For development only - restrict origins in production

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

        llm_response_text = llm_to_call(
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

# We will add more specific API endpoints later, e.g.:
# - POST /api/conversations (to create a new conversation)
# - GET /api/conversations (to list conversations)
# - GET /api/conversations/<conversation_id> (to get a specific conversation with messages)

@app.route("/api/conversations", methods=["POST"])
def create_conversation():
    try:
        data = request.json
        # Pydantic will use default_factory for id, created_at, updated_at
        new_conv_model = Conversation(**data) 
        
        # Validate LLM names (already part of Conversation model if llm_participants is Enum, but good to check again)
        for llm_name in new_conv_model.llm_participants:
            if llm_name not in ALL_LLMS:
                return jsonify({"error": f"Unsupported LLM: {llm_name}"}), 400

        db_doc = new_conv_model.to_db_document()
        result = db.conversations.insert_one(db_doc)
        created_id = str(db_doc['_id']) # This is now our string UUID

        app.logger.info(f"Conversation created with ID: {created_id}")
        
        # Optionally, send a starting message from the first LLM
        if data.get("start_conversation", False) and new_conv_model.llm_participants:
            first_llm_name = new_conv_model.llm_participants[0]
            llm_to_call = ALL_LLMS.get(first_llm_name)
            if llm_to_call:
                initial_prompt = "Hello! Please introduce yourself based on the system prompt and start the conversation."
                llm_response_text = llm_to_call(prompt=initial_prompt, system_prompt=new_conv_model.system_prompt, chat_history=[])
                
                llm_start_msg_data = {
                    "conversation_id": created_id,
                    "sender_type": 'llm',
                    "sender_id": first_llm_name,
                    "llm_name": first_llm_name,
                    "content": llm_response_text
                }
                llm_start_msg = Message(**llm_start_msg_data)
                db.messages.insert_one(llm_start_msg.to_db_document())

        return jsonify({"message": "Conversation created", "conversation_id": created_id, "data": new_conv_model.model_dump(mode='json')}), 201

    except ValidationError as e:
        app.logger.error(f"Pydantic validation error creating conversation: {e.errors()}")
        return jsonify({"error": "Invalid data for conversation", "details": e.errors()}), 400
    except Exception as e:
        app.logger.error(f"Error creating conversation: {e}", exc_info=True)
        return jsonify({"error": "Failed to create conversation"}), 500

@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    try:
        conv_cursor = db.conversations.find().sort("created_at", -1)
        conversations_list = []
        for conv_doc_db in conv_cursor:
            # No need for .to_dict() if from_db_document is used correctly and then model_dump()
            conversations_list.append(Conversation.from_db_document(conv_doc_db).model_dump(mode='json'))
        return jsonify(conversations_list)
    except Exception as e:
        app.logger.error(f"Error in get_conversations: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch conversations"}), 500

@app.route("/api/conversations/<conversation_id>", methods=["GET"])
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
        
        # Combine conversation details with its messages
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
def delete_conversation(conversation_id: str):
    try:
        if not conversation_id or not isinstance(conversation_id, str):
            return jsonify({"error": "Invalid conversation_id format, must be a string."}), 400

        # Delete the conversation
        result = db.conversations.delete_one({"_id": conversation_id})
        if result.deleted_count == 0:
            return jsonify({"error": "Conversation not found"}), 404
            
        # Delete all messages associated with this conversation
        db.messages.delete_many({"conversation_id": conversation_id})
        
        return jsonify({"message": "Conversation and associated messages deleted successfully"})

    except Exception as e:
        app.logger.error(f"Error deleting conversation {conversation_id}: {e}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred while deleting the conversation."}), 500

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001) # Using port 5001 to avoid conflict with React dev server 