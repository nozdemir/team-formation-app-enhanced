from flask import Flask
import logging
import os

def create_app():
    app = Flask(__name__)
    
    # Import and set config
    from .config import Config
    app.config.from_object(Config)
    
    # Set up logging
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
        
    logger = logging.getLogger(__name__)
    
    # Set environment variables for Neo4j (ensure compatibility)
    os.environ['NEO4J_URI'] = app.config['NEO4J_URI']
    os.environ['NEO4J_USER'] = app.config['NEO4J_USER']
    os.environ['NEO4J_USERNAME'] = app.config['NEO4J_USER']  # Both variants
    os.environ['NEO4J_PASSWORD'] = app.config['NEO4J_PASSWORD']
    
    logger.info(f"Neo4j URI: {app.config['NEO4J_URI']}")
    logger.info(f"Neo4j User: {app.config['NEO4J_USER']}")
    
    # Register blueprints
    from .routes import main
    app.register_blueprint(main)
    
    logger.info("Flask app created successfully with blueprints registered")
    
    return app

# Add this logging
logging.basicConfig(filename='app.log', level=logging.INFO)
