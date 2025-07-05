import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "supersecretkey")
    MONGODB_URI = os.getenv("MONGODB_URI")
    
    # API Keys
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

    @staticmethod
    def validate():
        if not Config.MONGODB_URI:
            raise ValueError("MONGODB_URI not found in environment variables")

config = Config()
config.validate()
