import os
import logging
from app import create_app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Get environment variables
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV', 'production') == 'development'
    
    logger.info(f"Starting Flask app on port {port} with debug={debug}")
    logger.info("Available routes:")
    logger.info("- / (Home page)")
    logger.info("- /test (Test endpoint)")
    logger.info("- /api/health (Health check)")
    logger.info("- /api/algorithms (Get algorithms)")
    logger.info("- /api/keywords (Get keywords)")
    logger.info("- /api/form-teams (Form teams - POST)")
    logger.info("- /api/test_connection (Test database)")
    logger.info("- /api/search-authors (Search authors)")
    logger.info("- /api/algorithm-info/<id> (Get algorithm details)")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
