from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from functools import wraps

from config import config
from database.connection import db_connection
from repositories.user_repository import UserRepository
from repositories.conversation_repository import ConversationRepository
from services.user_service import UserService
from services.conversation_service import ConversationService
from controllers.user_controller import UserController
from controllers.conversation_controller import ConversationController
from controllers.socket_controller import SocketController
from security import configure_security, handle_csrf_error, handle_security_error

try:
    config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    exit(1)

app = Flask(__name__)
app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY

csrf = CSRFProtect(app)

configure_security(app, csrf)

socketio = SocketIO(app, cors_allowed_origins="http://localhost:5874")

db = db_connection.db

user_repository = UserRepository(db)
conversation_repository = ConversationRepository(db)

user_service = UserService(user_repository)
conversation_service = ConversationService(conversation_repository, user_service)

user_controller = UserController(user_service)
conversation_controller = ConversationController(conversation_service)
socket_controller = SocketController(conversation_service, user_service)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

CORS(app, resources={r"/*": {"origins": "http://localhost:5874", "supports_credentials": True}})

app.register_error_handler(400, handle_csrf_error)
app.register_error_handler(403, handle_security_error)

from models.user import User

@login_manager.user_loader
def load_user(user_id):
    return user_service.get_user_by_id(user_id)

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

@app.route("/api/csrf-token", methods=["GET"])
def get_csrf_token():
    return jsonify({"csrf_token": csrf._get_token()})

# Socket event handlers
@socketio.on('connect')
def handle_connect():
    socket_controller.handle_connect()

@socketio.on('disconnect')
def handle_disconnect():
    socket_controller.handle_disconnect()

@socketio.on('trigger_next_llm')
def handle_trigger_next_llm(data):
    socket_controller.handle_trigger_next_llm(data)

@socketio.on('set_system_prompt')
def handle_set_system_prompt(data):
    socket_controller.handle_set_system_prompt(data)

# User routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    return user_controller.register()

@app.route("/api/auth/login", methods=["GET", "POST"])
def login():
    return user_controller.login()

@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    return user_controller.logout()

@app.route("/api/auth/user", methods=["GET"])
@login_required
def get_user():
    return user_controller.get_user_info()

@app.route("/api/auth/api-keys", methods=["POST"])
@login_required
def update_api_keys():
    return user_controller.update_api_keys()

# Conversation routes
@app.route("/api/conversations", methods=["POST"])
@login_required
def create_conversation():
    return conversation_controller.create_conversation()

@app.route("/api/conversations", methods=["GET"])
@login_required
def get_conversations():
    return conversation_controller.get_conversations()

@app.route("/api/conversations/<conversation_id>", methods=["GET"])
@login_required
def get_conversation_details(conversation_id: str):
    return conversation_controller.get_conversation_details(conversation_id)

@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
@login_required
def delete_conversation(conversation_id: str):
    return conversation_controller.delete_conversation(conversation_id)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)