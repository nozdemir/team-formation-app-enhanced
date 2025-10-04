import os
from dotenv import load_dotenv

# Load environment variables from .env file (if it exists)
try:
    load_dotenv()
except ImportError:
    pass  # dotenv might not be installed in production

class Config:
    """Application configuration class"""
    # Neo4j Configuration
    NEO4J_URI = os.environ.get('NEO4J_URI') or 'bolt://localhost:7687'
    NEO4J_USER = os.environ.get('NEO4J_USERNAME') or os.environ.get('NEO4J_USER') or 'neo4j'
    NEO4J_PASSWORD = os.environ.get('NEO4J_PASSWORD') or 'password'
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'on']
    
    @staticmethod
    def init_app(app):
        pass
