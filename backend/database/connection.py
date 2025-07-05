from pymongo import MongoClient
from config import config

class DatabaseConnection:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._client:
            self._client = MongoClient(config.MONGODB_URI)
            self._db = self._client.llm_chat_app
    
    @property
    def client(self):
        return self._client
    
    @property
    def db(self):
        return self._db
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None
            self._db = None

# Global database instance
db_connection = DatabaseConnection() 