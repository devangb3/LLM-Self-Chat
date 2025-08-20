from flask import Flask, jsonify, request, session
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect, generate_csrf
from functools import wraps
import os
import logging
from datetime import timedelta

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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to stdout for Cloud Run
        logging.FileHandler('app.log')  # Also log to file
    ]
)
logger = logging.getLogger(__name__)

try:
    config.validate()
except ValueError as e:
    logger.error(f"Configuration Error: {e}")
    exit(1)

os.environ['FLASK_ENV'] = 'development'  # Explicitly set for development

app = Flask(__name__)
app.config["SECRET_KEY"] = config.FLASK_SECRET_KEY

# Session configuration for cross-origin support
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Ensure session configuration is applied
app.config['SESSION_PERMANENT'] = True

# Explicit session cookie configuration for development cross-origin
if os.getenv('FLASK_ENV') == 'development':
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_SAMESITE'] = None  # Remove SameSite for cross-origin
    app.config['SESSION_COOKIE_DOMAIN'] = None
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

csrf = CSRFProtect(app)

configure_security(app, csrf)

CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5874,http://127.0.0.1:5874,http://localhost:5001').split(',')
logger.info(f"CORS Origins configured: {CORS_ORIGINS}")

CORS(app, 
     resources={r"/*": {"origins": CORS_ORIGINS}}, 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization", "X-CSRFToken", "Cookie"],
     expose_headers=["Set-Cookie"],
     vary_header=False)  # Disable Vary header for development

socketio = SocketIO(app, cors_allowed_origins=CORS_ORIGINS)

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
login_manager.login_view = '/api/auth/login'
login_manager.session_protection = 'strong'
# Allow remember me functionality for persistent sessions
login_manager.remember_cookie_duration = timedelta(hours=1)

app.register_error_handler(400, handle_csrf_error)
app.register_error_handler(403, handle_security_error)

from models.user import User

@login_manager.user_loader
def load_user(user_id):
    logger.info(f"Loading user with ID: {user_id}")
    try:
        user = user_service.get_user_by_id(user_id)
        logger.info(f"Loaded user: {user.email if user else 'None'}")
        return user
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

def socket_auth_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            emit('error', {'message': 'Authentication required'})
            return
        return f(*args, **kwargs)
    return wrapped

@app.before_request
def debug_session():
    """Debug session information"""
    logger.info(f"=== SESSION DEBUG for {request.method} {request.path} ===")
    logger.info(f"Session ID: {session.get('_id', 'No session ID')}")
    logger.info(f"Session permanent: {session.permanent}")
    logger.info(f"Session contents: {dict(session)}")
    logger.info(f"User ID from session: {session.get('_user_id', 'No user ID')}")
    logger.info(f"Current user: {current_user}")
    logger.info(f"Current user authenticated: {current_user.is_authenticated}")
    logger.info(f"Current user ID: {getattr(current_user, 'id', 'No ID')}")
    
    # Check cookies
    cookies = request.cookies
    logger.info(f"Cookies received: {list(cookies.keys())}")
    session_cookie = cookies.get('session')
    if session_cookie:
        logger.info(f"Session cookie present: {session_cookie[:20]}...")
    else:
        logger.info("No session cookie received")
    
    logger.info("=== END SESSION DEBUG ===")

@app.before_request
def log_request_info():
    """Log all incoming requests for debugging"""
    logger.info(f"Request: {request.method} {request.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Origin: {request.headers.get('Origin', 'No Origin')}")
    logger.info(f"User-Agent: {request.headers.get('User-Agent', 'No User-Agent')}")
    
    # Log CSRF token info
    csrf_token = request.headers.get('X-CSRFToken') or request.form.get('csrf_token')
    if csrf_token:
        logger.info(f"CSRF Token present: {csrf_token[:10]}...")
    else:
        logger.warning("No CSRF token found in request")

@app.route("/")
def index():
    logger.info("Index route accessed")
    return jsonify({"message": "LLM Chat App Backend Running"})

@app.route("/api/csrf-token", methods=["GET"])
def get_csrf_token():
    logger.info("CSRF token requested")
    
    # Ensure session is permanent
    session.permanent = True
    
    # Generate CSRF token - this should automatically store it in session
    token = generate_csrf()
    logger.info(f"Generated CSRF token: {token[:10]}...")
    
    # Double-check that token is in session
    if 'csrf_token' not in session:
        session['csrf_token'] = token
        logger.info(f"Manually stored CSRF token in session: {token[:10]}...")
    else:
        logger.info(f"CSRF token already in session: {session['csrf_token'][:10]}...")
    
    return jsonify({"csrf_token": token})

# Socket event handlers
@socketio.on('connect')
def handle_connect():
    logger.info("Socket connection established")
    socket_controller.handle_connect()

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Socket disconnected")
    socket_controller.handle_disconnect()

@socketio.on('trigger_next_llm')
def handle_trigger_next_llm(data):
    logger.info(f"Trigger next LLM event: {data}")
    socket_controller.handle_trigger_next_llm(data)

@socketio.on('set_system_prompt')
def handle_set_system_prompt(data):
    logger.info(f"Set system prompt event: {data}")
    socket_controller.handle_set_system_prompt(data)

# User routes
@app.route("/api/auth/register", methods=["POST"])
@csrf.exempt
def register():
    logger.info("Register endpoint accessed")
    return user_controller.register()

@app.route("/api/auth/login", methods=["GET", "POST"])
@csrf.exempt
def login():
    logger.info(f"Login endpoint accessed with method: {request.method}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    return user_controller.login()

@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    logger.info("Logout endpoint accessed")
    return user_controller.logout()

@app.route("/api/auth/user", methods=["GET"])
def get_user_info():
    logger.info("User info endpoint accessed")
    return user_controller.get_user_info()

@app.route("/api/auth/api-keys", methods=["POST"])
def update_api_keys():
    logger.info("API keys update endpoint accessed")
    return user_controller.update_api_keys()

# Conversation routes
@app.route("/api/conversations", methods=["POST"])
@login_required
def create_conversation():
    logger.info("Create conversation endpoint accessed")
    return conversation_controller.create_conversation()

@app.route("/api/conversations", methods=["GET"])
@login_required
def get_conversations():
    logger.info("Get conversations endpoint accessed")
    return conversation_controller.get_conversations()

@app.route("/api/conversations/<conversation_id>", methods=["GET"])
@login_required
def get_conversation_details(conversation_id: str):
    logger.info(f"Get conversation details endpoint accessed for ID: {conversation_id}")
    return conversation_controller.get_conversation_details(conversation_id)

@app.route("/api/conversations/<conversation_id>", methods=["DELETE"])
@login_required
def delete_conversation(conversation_id: str):
    logger.info(f"Delete conversation endpoint accessed for ID: {conversation_id}")
    return conversation_controller.delete_conversation(conversation_id)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info(f"Starting Flask app on port {port}, debug={debug}")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    
    socketio.run(app, debug=debug, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)