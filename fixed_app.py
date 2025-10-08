#!/usr/bin/env python3
"""
Fixed Flask app with both databases and algorithms working
"""
from flask import Flask, jsonify, render_template, request
import os
import sys

# Add the app directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, 'app')
sys.path.insert(0, app_dir)

# Import team formation module
from team_formation import ScientificTeamFormation

app = Flask(__name__, template_folder='app/templates', static_folder='app/static')

# Database configurations
DATABASE_CONFIGS = {
    'gazi_db': {
        'name': 'Small (Gazi) Network',
        'description': 'Gazi University research network for faster testing',
        'uri': 'neo4j+s://cc773764.databases.neo4j.io',
        'user': 'neo4j',
        'password': 'z2rSb4ew9gxVlqlrFk8l_VZQcVhIzBwgnlder4nKv1A',
        'size': 'small',
        'expected_time': '10-30 seconds'
    },
    'industrial_db': {
        'name': 'Full (Industrial Engineering) Network',
        'description': 'Complete industrial engineering research database with extensive data',
        'uri': 'neo4j+s://54f41429.databases.neo4j.io',
        'user': 'neo4j',
        'password': 'j1fv7zahO1N8ly6efLg0xUfDBQxwTGrQhEuZZn_gPkM',
        'size': 'large',
        'expected_time': '30-120 seconds'
    }
}

current_database = 'gazi_db'

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/api/databases', methods=['GET'])
def get_databases():
    """Get available database configurations"""
    try:
        databases = {}
        for db_id, config in DATABASE_CONFIGS.items():
            databases[db_id] = {
                'id': db_id,
                'name': config['name'],
                'description': config['description'],
                'size': config['size'],
                'expected_time': config['expected_time'],
                'selected': db_id == current_database
            }
        
        return jsonify({
            'databases': databases,
            'current': current_database
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/algorithms', methods=['GET'])
def get_algorithms():
    """Get available algorithms"""
    algorithms = [
        {
            "id": "ACET",
            "name": "All-Connections-Equal Team Formation",
            "description": "Considers all types of connections equally"
        },
        {
            "id": "CAT", 
            "name": "Co-Authorship Team Formation",
            "description": "Builds teams only using co-authorship relations"
        },
        {
            "id": "OAT",
            "name": "Organizational Affiliation Team Formation", 
            "description": "Builds teams only using co-working relations"
        },
        {
            "id": "PRT",
            "name": "Prioritized Relationship Team Formation",
            "description": "Prioritizes co-authorship relations over organizational relations"
        },
        {
            "id": "COT",
            "name": "Cohesion-Optimized Team Formation",
            "description": "Maximizes team cohesion by selecting members with most connections to existing team"
        },
        {
            "id": "TAT",
            "name": "Team Affiliation Team Formation",
            "description": "Forms teams based on organizational affiliation patterns"
        },
        {
            "id": "CIT",
            "name": "Citation-Impact Team Formation", 
            "description": "Considers citation impact and research influence in team formation"
        }
    ]
    
    return jsonify(algorithms)

@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    """Get available keywords from gazi_keywords.txt file"""
    try:
        keywords_file = os.path.join('app', 'data', 'gazi_keywords.txt')
        
        if not os.path.exists(keywords_file):
            print(f"❌ Keywords file not found: {keywords_file}")
            # Fallback to basic keywords
            keywords = [
                "machine learning", "artificial intelligence", "optimization", "algorithms",
                "data mining", "neural networks", "pattern recognition", "operations research"
            ]
        else:
            print(f"📖 Loading keywords from: {keywords_file}")
            with open(keywords_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Split by comma and clean up keywords
                keywords = [kw.strip() for kw in content.split(',')]
                # Remove empty keywords and sort
                keywords = sorted([kw for kw in keywords if kw and len(kw) > 1])
                print(f"✅ Loaded {len(keywords)} keywords from file")
        
        return jsonify(keywords)
        
    except Exception as e:
        print(f"❌ Error loading keywords: {e}")
        # Return fallback keywords
        fallback_keywords = [
            "machine learning", "artificial intelligence", "optimization", "algorithms",
            "data mining", "neural networks", "pattern recognition", "operations research",
            "supply chain", "decision making", "simulation", "scheduling"
        ]
        return jsonify(fallback_keywords)

@app.route('/api/select-database', methods=['POST'])
def select_database():
    """Select a database for team formation"""
    global current_database
    
    try:
        from flask import request
        data = request.get_json()
        database_id = data.get('database_id')
        
        if database_id not in DATABASE_CONFIGS:
            return jsonify({'error': f'Invalid database ID: {database_id}'}), 400
        
        # Update current database selection
        old_database = current_database
        current_database = database_id
        
        # Set environment variables for the selected database
        config = DATABASE_CONFIGS[database_id]
        os.environ['NEO4J_URI'] = config['uri']
        os.environ['NEO4J_USER'] = config['user']
        os.environ['NEO4J_PASSWORD'] = config['password']
        
        print(f"🔄 Database switched from {old_database} to {database_id}")
        print(f"🔗 Neo4j URI: {config['uri']}")
        
        return jsonify({
            'success': True,
            'database': {
                'id': database_id,
                'name': config['name'],
                'description': config['description'],
                'size': config['size'],
                'expected_time': config['expected_time']
            },
            'message': f"Successfully switched to {config['name']}"
        })
        
    except Exception as e:
        print(f"❌ Error selecting database: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/form-teams', methods=['POST'])
def form_teams():
    """Form teams using selected algorithm and database"""
    try:
        from flask import request
        data = request.get_json()
        
        algorithm = data.get('algorithm')
        keywords = data.get('keywords', [])
        num_teams = data.get('numTeams', 5)
        database = data.get('database', current_database)
        
        print(f"🚀 Starting team formation...")
        print(f"📊 Database: {DATABASE_CONFIGS[database]['name']}")
        print(f"🧮 Algorithm: {algorithm}")
        print(f"🔍 Keywords: {keywords}")
        print(f"👥 Number of teams: {num_teams}")
        
        # Set the correct environment variables for the selected database
        config = DATABASE_CONFIGS[database]
        os.environ['NEO4J_URI'] = config['uri']
        os.environ['NEO4J_USER'] = config['user']
        os.environ['NEO4J_PASSWORD'] = config['password']
        
        # Import and initialize team formation
        import sys
        sys.path.append('app')
        from team_formation import ScientificTeamFormation
        
        print(f"🔗 Connecting to {config['name']}...")
        tf = ScientificTeamFormation()
        
        # Form teams
        print(f"⚙️ Running {algorithm} algorithm...")
        teams = tf.form_teams(
            algorithm=algorithm,
            keywords=keywords,
            num_teams=num_teams
        )
        
        print(f"✅ Successfully formed {len(teams)} teams")
        
        return jsonify({
            'success': True,
            'teams': teams,
            'algorithm': algorithm,
            'database': config['name'],
            'total_teams': len(teams),
            'keywords_used': keywords
        })
        
    except Exception as e:
        print(f"❌ Team formation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to form teams. Please check your settings and try again.'
        }), 500

@app.route('/api/keywords-file')
def get_keywords_from_file():
    """Get keywords from file (alias for /api/keywords)"""
    return get_keywords()

@app.route('/api/form-teams-async', methods=['POST'])
def form_teams_async():
    """Async team formation endpoint - directly process and return results"""
    try:
        # Process the request directly by calling the same logic
        data = request.get_json()
        algorithm = data.get('algorithm')
        keywords = data.get('keywords', [])
        num_teams = data.get('num_teams', 5)
        selected_database = data.get('database', current_database)
        
        # Validate database selection
        if selected_database not in DATABASE_CONFIGS:
            raise Exception(f"Invalid database selection: {selected_database}")
        
        print(f"🚀 Starting team formation...")
        print(f"📊 Database: {DATABASE_CONFIGS[selected_database]['name']}")
        print(f"🧮 Algorithm: {algorithm}")
        print(f"🔍 Keywords: {keywords}")
        print(f"👥 Number of teams: {num_teams}")
        
        # Get database configuration
        config = DATABASE_CONFIGS[selected_database]
        print(f"🔗 Connecting to {config['name']}...")
        
        # Set environment variables with retry configuration
        os.environ['NEO4J_URI'] = config['uri']
        os.environ['NEO4J_USER'] = config['user']
        os.environ['NEO4J_PASSWORD'] = config['password']
        
        # Initialize team formation system with retry
        retry_count = 0
        max_retries = 3
        tf = None
        
        while retry_count < max_retries and tf is None:
            try:
                print(f"🔄 Connection attempt {retry_count + 1}/{max_retries}")
                tf = ScientificTeamFormation()
                break
            except Exception as conn_error:
                retry_count += 1
                print(f"❌ Connection attempt {retry_count} failed: {conn_error}")
                if retry_count < max_retries:
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry
                else:
                    raise conn_error
        
        if tf is None:
            raise Exception("Failed to establish database connection after multiple attempts")
        
        print(f"⚙️ Running {algorithm} algorithm...")
        teams_result = tf.form_teams(
            algorithm=algorithm,
            keywords=keywords,
            num_teams=num_teams
        )
        
        # Extract teams array from the result dictionary
        teams = teams_result.get('teams', []) if isinstance(teams_result, dict) else teams_result
        
        print(f"✅ Successfully formed {len(teams)} teams")
        print(f"🔍 Debug - teams_result type: {type(teams_result)}")
        print(f"🔍 Debug - teams type: {type(teams)}")
        
        # Build the result data
        result_data = {
            'success': True,
            'teams': teams,
            'algorithm': algorithm,
            'database': config['name'],
            'total_teams': len(teams),
            'keywords_used': keywords,
            'message': teams_result.get('message', 'Teams formed successfully') if isinstance(teams_result, dict) else 'Teams formed successfully'
        }
        
        # Return for async compatibility
        return jsonify({
            'success': True,
            'task_id': 'direct_processing',
            'task_status': {
                'status': 'completed',
                'result': result_data,
                'message': 'Team formation completed successfully'
            }
        })
            
    except Exception as e:
        print(f"❌ Async team formation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/task-status/<task_id>')
def get_task_status(task_id):
    """Get task status - since we process directly, always return completed"""
    return jsonify({
        'task_status': {
            'status': 'completed',
            'message': 'Direct processing completed',
            'progress': 100
        }
    })

if __name__ == '__main__':
    print("🚀 Starting Fixed Flask App")
    print("✅ Databases: Small (Gazi) Network + Full (Industrial Engineering) Network")
    print("✅ Algorithms: All 7 team formation algorithms")
    print("🌐 Server: http://127.0.0.1:5000")
    print("=" * 60)
    
    app.run(host='127.0.0.1', port=5000, debug=True)