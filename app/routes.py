from flask import Blueprint, render_template, request, jsonify
import logging
import traceback
import os  # Add this line at the top with other imports

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

# Global team formation instance
team_formation = None

def get_team_formation():
    """Get or create team formation instance"""
    global team_formation
    if team_formation is None:
        try:
            from .team_formation import ScientificTeamFormation
            team_formation = ScientificTeamFormation()
            logger.info("Team formation instance created successfully")
        except Exception as e:
            logger.error(f"Failed to create team formation instance: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise
    return team_formation

@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@main.route('/test')
def test():
    """Simple test route"""
    return jsonify({
        'status': 'working',
        'message': 'Flask app is running correctly',
        'structure': 'application factory pattern'
    })

@main.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            'status': 'healthy',
            'message': 'Flask app is running',
            'pattern': 'application factory',
            'routes': ['/test', '/api/health', '/api/algorithms', '/api/keywords', '/api/form-teams', '/api/test_connection']
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@main.route('/api/algorithms')
def get_algorithms():
    """Get available algorithms"""
    try:
        logger.info("Getting algorithms...")
        
        try:
            tf = get_team_formation()
            algorithms = tf.get_available_algorithms()
            
            algorithm_list = []
            for code, info in algorithms.items():
                algorithm_list.append({
                    "id": code,
                    "name": info["name"],
                    "description": info["description"]
                })
            
            logger.info(f"Successfully loaded {len(algorithm_list)} algorithms from team formation class")
            return jsonify(algorithm_list)
            
        except Exception as db_error:
            logger.warning(f"Team formation error, using fallback algorithms: {db_error}")
            
        # Fallback algorithms (matching your Jupyter notebook)
        fallback_algorithms = [
            {"id": "ACET", "name": "All-Connections-Equal Team Formation", "description": "Considers all types of connections equally"},
            {"id": "CAT", "name": "Co-Authorship Team Formation", "description": "Builds teams only using co-authorship relations"},
            {"id": "OAT", "name": "Organizational Affiliation Team Formation", "description": "Builds teams only using co-working relations"},
            {"id": "PRT", "name": "Prioritized Relationship Team Formation", "description": "Prioritizes co-authorship relations over organizational relations"},
            {"id": "COT", "name": "Cohesion-Optimized Team Formation", "description": "Maximizes team cohesion"},
            {"id": "TAT", "name": "Time-Aware Team Formation", "description": "Considers recency of collaborations"},
            {"id": "CIT", "name": "Citation-Optimized Team Formation", "description": "Optimizes based on citation impact"}
        ]
        logger.info(f"Returning {len(fallback_algorithms)} fallback algorithms")
        return jsonify(fallback_algorithms)
        
    except Exception as e:
        logger.error(f"Error in get_algorithms: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/keywords')
def get_keywords():
    """Get available keywords"""
    try:
        logger.info("Getting keywords...")
        
        try:
            tf = get_team_formation()
            keywords = tf.get_keywords(limit=100)
            logger.info(f"Successfully loaded {len(keywords)} keywords from database")
            return jsonify(keywords)
            
        except Exception as db_error:
            logger.warning(f"Database error, using fallback keywords: {db_error}")
        
        fallback_keywords = [
            "machine learning", "data mining", "optimization", "algorithms",
            "database systems", "software engineering", "artificial intelligence",
            "computer vision", "natural language processing", "deep learning",
            "load balancing", "scheduling", "strategic planning", 
            "constraint programming", "project management"
        ]
        return jsonify(fallback_keywords)
        
    except Exception as e:
        logger.error(f"Error in get_keywords: {e}")
        return jsonify({'error': str(e)}), 500

@main.route('/api/test_connection')
def test_connection():
    """Test Neo4j database connection"""
    try:
        logger.info("Testing database connection...")
        tf = get_team_formation()
        
        if tf.test_database_connection():
            debug_info = tf.debug_database_structure()
            return jsonify({
                'success': True,
                'message': 'Database connection successful',
                'debug_info': debug_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Database connection failed - connection test returned False'
            }), 500
            
    except Exception as e:
        logger.error(f"Database test error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': f'Database connection error: {str(e)}'
        }), 500

@main.route('/api/form-teams', methods=['POST'])
def api_form_teams():
    """API endpoint for team formation"""
    try:
        logger.info("=== Team Formation Request Started ===")
        
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        logger.info(f"Received data: {data}")
        
        # Validate required fields
        algorithm = data.get('algorithm')
        keywords = data.get('keywords', [])
        num_teams = data.get('num_teams', 5)
        
        logger.info(f"Algorithm: {algorithm}")
        logger.info(f"Keywords: {keywords}")
        logger.info(f"Number of teams: {num_teams}")
        
        if not algorithm:
            logger.error("No algorithm specified")
            return jsonify({'success': False, 'error': 'Algorithm is required'}), 400
        
        if not keywords or len(keywords) == 0:
            logger.error("No keywords provided")
            return jsonify({'success': False, 'error': 'At least one keyword is required'}), 400
        
        if not isinstance(num_teams, int) or num_teams < 1:
            logger.error(f"Invalid number of teams: {num_teams}")
            return jsonify({'success': False, 'error': 'Number of teams must be a positive integer'}), 400
        
        # Initialize team formation system
        logger.info("Initializing team formation system...")
        try:
            tf = get_team_formation()
            logger.info("Team formation system initialized successfully")
        except Exception as tf_error:
            logger.error(f"Failed to initialize team formation system: {tf_error}")
            return jsonify({
                'success': False, 
                'error': f'Database connection failed: {str(tf_error)}'
            }), 500
        
        # Form teams using the unified team formation method
        logger.info(f"Starting team formation with algorithm: {algorithm}")
        try:
            # Use the single consistent form_teams method
            # Use the single unified form_teams method for all algorithms
            teams_data = tf.form_teams(
                algorithm=algorithm,
                keywords=keywords,
                num_teams=num_teams
            )
            
            logger.info("Team formation completed successfully")
            logger.info(f"Teams data type: {type(teams_data)}")
            
            if teams_data:
                logger.info(f"Number of teams formed: {len(teams_data) if isinstance(teams_data, (list, tuple)) else 'Unknown'}")
            
        except Exception as algo_error:
            logger.error(f"Algorithm execution failed: {algo_error}")
            logger.error(f"Algorithm error traceback:", exc_info=True)
            return jsonify({
                'success': False, 
                'error': f'Team formation failed: {str(algo_error)}'
            }), 500
        
        # Process and format the results
        try:
            logger.info("Processing team formation results...")
            
            if not teams_data:
                logger.warning("No teams were formed")
                return jsonify({
                    'success': False,
                    'error': 'No teams could be formed with the given parameters. Try different keywords or fewer teams.'
                }), 200
            
            # Convert teams data to the expected format
            formatted_teams = []
            
            if isinstance(teams_data, dict) and 'teams' in teams_data:
                # If teams_data is a dict with 'teams' key
                teams_list = teams_data['teams']
                summary = teams_data.get('summary', {})
            elif isinstance(teams_data, (list, tuple)):
                # If teams_data is directly a list of teams
                teams_list = teams_data
                summary = {}
            else:
                logger.error(f"Unexpected teams_data format: {type(teams_data)}")
                teams_list = []
                summary = {}
            
            logger.info(f"Processing {len(teams_list)} teams...")
            
            for i, team in enumerate(teams_list):
                try:
                    formatted_team = {
                        'team_number': i + 1,
                        'team_name': team.get('team_name', f'Team {i + 1}'),
                        'members': [],
                        'skills_covered': team.get('skills_covered', []),
                        'requested_skills': team.get('missing_skills', [])
                    }
                    
                    # Process team members
                    members = team.get('members', [])
                    for member in members:
                        if isinstance(member, dict):
                            formatted_team['members'].append({
                                'author_name': member.get('name', member.get('author_name', 'Unknown')),
                                'role': member.get('role', 'Member')
                            })
                        else:
                            # If member is just a string/name
                            formatted_team['members'].append({
                                'author_name': str(member),
                                'role': 'Member'
                            })
                    
                    formatted_teams.append(formatted_team)
                    logger.info(f"Processed team {i + 1}: {len(formatted_team['members'])} members")
                    
                except Exception as team_error:
                    logger.error(f"Error processing team {i}: {team_error}")
                    continue
            
            # Prepare response
            response_data = {
                'success': True,
                'algorithm': algorithm,
                'total_teams': len(formatted_teams),
                'teams': formatted_teams
            }
            
            # Add summary if available
            if summary:
                response_data['summary'] = {
                    'algorithm_name': summary.get('algorithm_name', algorithm.replace('_', ' ').title()),
                    'keywords_requested': keywords,
                    'success_rate': summary.get('success_rate', 'N/A'),
                    'avg_team_size': summary.get('avg_team_size', 'N/A'),
                    'avg_completeness': summary.get('avg_completeness', 'N/A')
                }
            
            logger.info("=== Team Formation Request Completed Successfully ===")
            return jsonify(response_data)
            
        except Exception as format_error:
            logger.error(f"Error formatting results: {format_error}")
            logger.error("Format error traceback:", exc_info=True)
            return jsonify({
                'success': False, 
                'error': f'Error processing results: {str(format_error)}'
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in api_form_teams: {e}")
        logger.error("Full traceback:", exc_info=True)
        return jsonify({
            'success': False, 
            'error': f'Internal server error: {str(e)}'
        }), 500

@main.route('/api/search-authors', methods=['GET'])
def search_authors():
    """Search for authors by name or skills"""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 results
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        tf = get_team_formation()
        authors = tf.search_authors(query, limit)
        
        return jsonify({
            'success': True,
            'authors': authors,
            'query': query,
            'count': len(authors)
        })
        
    except Exception as e:
        logger.error(f"Error in search_authors: {e}")
        return jsonify({
            'success': False,
            'error': f'Search failed: {str(e)}',
            'authors': []
        }), 500

@main.route('/api/algorithm-info/<algorithm_id>')
def get_algorithm_info(algorithm_id):
    """Get detailed information about a specific algorithm"""
    try:
        tf = get_team_formation()
        algo_info = tf.config.get_algorithm_info(algorithm_id)
        
        if not algo_info:
            return jsonify({
                'success': False,
                'error': f'Algorithm {algorithm_id} not found'
            }), 404
        
        return jsonify({
            'success': True,
            'algorithm': {
                'id': algorithm_id,
                'name': algo_info['name'],
                'description': algo_info['description'],
                'seed_filter': algo_info['seed_filter'],
                'member_finder': algo_info['member_finder']
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting algorithm info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@main.route('/api/keywords-file')
def get_keywords_from_file():
    """Get keywords from gazi_keywords.txt file"""
    try:
        logger.info("Loading keywords from gazi_keywords.txt...")
        
        # Try to find the keywords file - Updated paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'data', 'gazi_keywords.txt'),
            os.path.join(os.path.dirname(__file__), '..', 'data', 'gazi_keywords.txt'),
            'app/data/gazi_keywords.txt',
            'data/gazi_keywords.txt',
            'gazi_keywords.txt'
        ]
        
        keywords = []
        file_found = False
        
        for file_path in possible_paths:
            try:
                abs_path = os.path.abspath(file_path)
                if os.path.exists(abs_path):
                    logger.info(f"Found keywords file at: {abs_path}")
                    with open(abs_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        # Split by comma and clean up keywords
                        keywords = [kw.strip() for kw in content.split(',') if kw.strip() and len(kw.strip()) > 1]
                        file_found = True
                        break
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
                continue
        
        if not file_found:
            logger.warning("gazi_keywords.txt not found, falling back to database keywords")
            try:
                tf = get_team_formation()
                keywords = tf.get_keywords(limit=200)
            except Exception as db_error:
                logger.warning(f"Database fallback failed: {db_error}")
                # Final fallback to hardcoded keywords
                keywords = [
                    "machine learning", "data mining", "optimization", "algorithms",
                    "database systems", "software engineering", "artificial intelligence",
                    "computer vision", "natural language processing", "deep learning",
                    "load balancing", "scheduling", "strategic planning", 
                    "constraint programming", "project management", "neural networks",
                    "pattern recognition", "information retrieval", "data analysis"
                ]
        
        # Remove duplicates, filter out very short keywords, and sort
        keywords = sorted(list(set([kw for kw in keywords if len(kw) > 2])))
        
        logger.info(f"Successfully loaded {len(keywords)} keywords for auto-complete")
        return jsonify(keywords)
        
    except Exception as e:
        logger.error(f"Error in get_keywords_from_file: {e}")
        return jsonify({
            'error': f'Failed to load keywords: {str(e)}',
            'fallback_keywords': [
                "machine learning", "optimization", "algorithms", "data mining"
            ]
        }), 500
