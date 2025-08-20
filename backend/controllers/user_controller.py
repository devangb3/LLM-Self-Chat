from flask import jsonify, request, session
from flask_login import login_user, logout_user, login_required, current_user
from services.user_service import UserService
from services.auth_service import AuthService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Log to stdout for Cloud Run
        logging.FileHandler('app.log')  # Also log to file
    ]
)
logger = logging.getLogger(__name__)
class UserController:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.auth_service = AuthService()
    
    def register(self):
        """Handle user registration"""
        try:
            data = request.json
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400

            success, message = self.user_service.register_user(email, password)
            
            if success:
                return jsonify({"message": message}), 201
            else:
                return jsonify({"error": message}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def login(self):
        """Handle user login"""
        if request.method == "GET":
            logger.info(f"Current user: {current_user}")
            logger.info(f"Session contents: {dict(session)}")
            logger.info(f"User ID in session: {session.get('user_id')}")
            logger.info(f"Session ID: {session.get('_id')}")
            
            if current_user.is_authenticated:
                return jsonify({
                    "message": "Already logged in",
                    "user": {
                        "id": current_user.id,
                        "email": current_user.email,
                        "available_models": self.user_service.get_available_models(current_user.id)
                    }
                })
            else:
                return jsonify({"message": "Not authenticated"}), 401

        try:
            data = request.json
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400

            user, message = self.user_service.authenticate_user(email, password)
            
            if user:
                # Configure session to be permanent
                session.permanent = True
                
                login_user(user, remember=True)
                
                session['user_id'] = user.id
                
                logger.info(f"User logged in successfully: {user.id}")
                logger.info(f"Session after login: {dict(session)}")
                logger.info(f"Current user authenticated: {current_user.is_authenticated}")
                
                # Generate JWT token for WebSocket authentication
                access_token = self.auth_service.create_access_token(user)
                
                return jsonify({
                    "message": "Logged in successfully",
                    "access_token": access_token,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "available_models": self.user_service.get_available_models(user.id)
                    }
                })
            else:
                return jsonify({"error": message}), 401

        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    def logout(self):
        """Handle user logout"""
        logout_user()
        session.clear()  # Clear session data
        return jsonify({"message": "Logged out successfully"})
    
    @login_required
    def get_user_info(self):
        """Get current user information"""
        return jsonify({
            "id": current_user.id,
            "email": current_user.email,
            "available_models": self.user_service.get_available_models(current_user.id)
        })
    
    @login_required
    def update_api_keys(self):
        """Update user API keys"""
        try:
            data = request.json
            api_keys = {}
            
            for model in ["claude", "gemini", "openai", "deepseek"]:
                key = data.get(f"{model}_api_key")
                if key is not None and key.strip():
                    api_keys[model] = key

            success, message = self.user_service.update_api_keys(current_user.id, api_keys)
            
            if success:
                return jsonify({
                    "message": message,
                    "updated_keys": list(api_keys.keys())
                })
            else:
                return jsonify({"message": message}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500 